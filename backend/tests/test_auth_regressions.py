from concurrent.futures import ThreadPoolExecutor
from threading import Barrier, get_ident

import bcrypt
import pytest
from beanie import PydanticObjectId
from fastapi import HTTPException
from pydantic import SecretStr, ValidationError

import backend.auth as auth
import backend.database as database
from backend.config import Settings, settings
from backend.models.car_model import CarModel
from backend.models.mod import ModItem
from backend.models.session import AuthSession
from backend.models.user import FIRST_ADMIN_ID, User
from backend.routes import auth_route, users_route
from backend.tests.conftest import auth_headers_for, create_user
from backend.tests.test_carfax_car_import import _preview, _records


def test_setup_token_and_configuration(raw_client, monkeypatch):
    token = "operator-secret-" * 3
    monkeypatch.setattr(settings, "setup_token", SecretStr(token))
    assert raw_client.get("/auth/status").json()["setup_token_required"] is True
    payload = {"username": "admin", "password": "password123"}
    for headers in ({}, {"X-Setup-Token": "wrong"}):
        assert raw_client.post("/auth/setup", json=payload, headers=headers).status_code == 403
    assert raw_client.post("/auth/setup", json=payload, headers={"X-Setup-Token": token}).status_code == 201
    assert Settings(_env_file=None, FRONTEND_URL="unused").session_ttl_days == 30
    for invalid in (
        {"session_ttl_days": 0}, {"session_ttl_days": 366},
        {"login_max_attempts": 0}, {"login_window_seconds": 0},
        {"login_max_buckets": 100001}, {"setup_token_required": True, "setup_token": None},
        {"setup_token": "short"},
    ):
        with pytest.raises(ValidationError):
            Settings(_env_file=None, **invalid)


def test_concurrent_setup_has_one_durable_winner(raw_client, monkeypatch):
    barrier = Barrier(2)
    original = auth.hash_password

    def paused_hash(password):
        barrier.wait(timeout=5)
        return original(password)

    monkeypatch.setattr(auth_route, "hash_password", paused_hash)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda name: raw_client.post(
            "/auth/setup", json={"username": name, "password": "password123"}
        ), ["first", "second"]))
    assert sorted(response.status_code for response in responses) == [201, 403]

    async def check():
        assert await User.find_all().count() == 1
        assert (await User.get(FIRST_ADMIN_ID)).is_admin

    raw_client.portal.call(check)


@pytest.mark.parametrize("legacy_id", [False, True])
def test_startup_recovers_partial_legacy_claim(raw_client, legacy_id):
    async def seed_and_restart():
        user = User(
            id=PydanticObjectId() if legacy_id else FIRST_ADMIN_ID,
            username="admin", password_hash=auth.DUMMY_PASSWORD_HASH, is_admin=True,
        )
        await user.insert()
        car = await CarModel(make="Honda", model="Civic", year=2020).insert()
        assigned = await CarModel(make="Ford", model="Focus", year=2020, owner_id=PydanticObjectId()).insert()
        await database.init_db()
        assert (await CarModel.get(car.id)).owner_id == user.id
        assert (await CarModel.get(assigned.id)).owner_id == assigned.owner_id
        assert (await User.get(user.id)).legacy_claim_complete
        await database.recover_legacy_claim()
        assert (await CarModel.get(car.id)).owner_id == user.id

    raw_client.portal.call(seed_and_restart)


def test_passwords_use_all_bytes_and_preserve_whitespace(raw_client):
    password = " " + "\u00e9" * 70 + " "
    response = raw_client.post("/auth/setup", json={"username": " Admin ", "password": password})
    assert response.status_code == 201
    for supplied, expected in ((password, 200), (password.strip(), 401), (password[:-2] + "x ", 401)):
        assert raw_client.post("/auth/login", json={"username": "ADMIN", "password": supplied}).status_code == expected
    headers = {"Authorization": "Bearer " + response.json()["token"]}
    new_password = " new-password "
    assert raw_client.post("/auth/password", headers=headers, json={
        "current_password": password, "new_password": new_password,
    }).status_code == 204
    assert raw_client.post("/auth/login", json={"username": "admin", "password": new_password}).status_code == 200


def test_legacy_bcrypt_never_accepts_truncated_input():
    hashed = bcrypt.hashpw(b"a" * 72, bcrypt.gensalt()).decode()
    assert auth.verify_password("a" * 72, hashed)
    assert not auth.verify_password("a" * 72 + "different", hashed)


def test_unknown_login_verifies_dummy_in_worker(raw_client, monkeypatch):
    from argon2.exceptions import VerifyMismatchError
    with pytest.raises(VerifyMismatchError):
        auth.password_hasher.verify(auth.DUMMY_PASSWORD_HASH, "password123")
    loop_thread = raw_client.portal.call(get_ident)
    calls = []
    original = auth.verify_password

    def verify(password, hashed):
        calls.append((get_ident(), hashed))
        return original(password, hashed)

    monkeypatch.setattr(auth_route, "verify_password", verify)
    assert raw_client.post("/auth/login", json={"username": "unknown", "password": "password123"}).status_code == 401
    assert calls == [(calls[0][0], auth.DUMMY_PASSWORD_HASH)]
    assert calls[0][0] != loop_thread


def test_login_throttle_is_bounded_and_expires(raw_client, monkeypatch):
    monkeypatch.setattr(settings, "login_max_attempts", 1)
    monkeypatch.setattr(settings, "login_max_buckets", 1)
    payload = {"username": "unknown", "password": "password123"}
    assert raw_client.post("/auth/login", json=payload).status_code == 401
    response = raw_client.post("/auth/login", json={**payload, "username": "another"})
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    from starlette.requests import Request
    with pytest.raises(HTTPException) as exc:
        auth.throttle_login(Request({"type": "http", "client": ("another-host", 1)}))
    assert exc.value.status_code == 429
    assert len(auth.login_buckets) == 1
    auth.login_buckets["testclient"] = (0, 1)
    assert raw_client.post("/auth/login", json=payload).status_code == 401


def test_duplicate_username_insert_race_maps_to_conflict(api_client, monkeypatch):
    barrier = Barrier(2)

    def paused_hash(password):
        barrier.wait(timeout=5)
        return auth.hash_password(password)

    monkeypatch.setattr(users_route, "hash_password", paused_hash)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: api_client.post(
            "/users/", json={"username": "mechanic", "password": "password123"}
        ), range(2)))
    assert sorted(response.status_code for response in responses) == [201, 409]


def test_reset_between_verification_and_session_insert(api_client, monkeypatch):
    created = create_user(api_client, "mechanic")
    original = auth_route.create_session

    async def reset_then_create(user):
        await users_route.reset_user_password(user.id, users_route.PasswordReset(new_password="replacement-password"))
        return await original(user)

    monkeypatch.setattr(auth_route, "create_session", reset_then_create)
    assert api_client.post("/auth/login", json={"username": "mechanic", "password": "password123"}).status_code == 401

    async def check_late_session():
        user = await User.get(PydanticObjectId(created["_id"]))
        token = "late-old-credential-token"
        await AuthSession(token_hash=auth.hash_token(token), user_id=user.id,
                          credential_version=0, expires_at=AuthSession.new_expiry(1)).insert()
        return token

    token = api_client.portal.call(check_late_session)
    assert api_client.get("/auth/me", headers={"Authorization": "Bearer " + token}).status_code == 401


def test_password_change_cannot_overwrite_concurrent_reset(api_client, monkeypatch):
    created = create_user(api_client, "mechanic")
    headers = auth_headers_for(api_client, "mechanic", "password123")
    original = auth_route.run_in_threadpool

    async def reset_before_password_write(function, *args):
        result = await original(function, *args)
        if function is auth_route.hash_password:
            await users_route.reset_user_password(
                PydanticObjectId(created["_id"]), users_route.PasswordReset(new_password="operator-password")
            )
        return result

    monkeypatch.setattr(auth_route, "run_in_threadpool", reset_before_password_write)
    assert api_client.post("/auth/password", headers=headers, json={
        "current_password": "password123", "new_password": "stale-password",
    }).status_code == 409
    assert api_client.get("/auth/me", headers=headers).status_code == 401
    assert api_client.post("/auth/login", json={"username": "mechanic", "password": "operator-password"}).status_code == 200


def test_carfax_vin_is_owner_scoped(api_client, monkeypatch):
    preview = _preview(api_client, monkeypatch).json()
    vin = preview["report"]["vin"]
    api_client.post("/cars/", json={"make": "Honda", "model": "Accord", "year": 2011, "vin": vin})
    create_user(api_client, "mechanic")
    api_client.default_headers = auth_headers_for(api_client, "mechanic", "password123")
    assert _preview(api_client, monkeypatch).status_code == 200
    payload = {"report_vin": vin, "vehicle": {"make": "Honda", "model": "Accord", "year": 2011, "vin": vin, "mileage": 108707},
               "records": _records(preview)}
    assert api_client.post("/cars/import/carfax/confirm", json=payload).status_code == 201
    assert api_client.post("/cars/import/carfax/confirm", json=payload).status_code == 409


def test_delete_disables_user_and_marks_cars_before_cascade(api_client, monkeypatch):
    created = create_user(api_client, "mechanic")
    headers = auth_headers_for(api_client, "mechanic", "password123")
    car = api_client.post("/cars/", headers=headers, json={"make": "Honda", "model": "Civic", "year": 2020}).json()
    original = CarModel.delete

    async def fail_delete(car, *args, **kwargs):
        assert (await User.get(car.owner_id)).is_deleting
        assert (await CarModel.get(car.id)).is_deleting
        raise RuntimeError("interrupted cascade")

    monkeypatch.setattr(CarModel, "delete", fail_delete)
    with pytest.raises(RuntimeError, match="interrupted cascade"):
        api_client.delete(f"/users/{created['_id']}")
    assert api_client.get("/auth/me", headers=headers).status_code == 401
    assert api_client.post("/auth/login", json={"username": "mechanic", "password": "password123"}).status_code == 401
    monkeypatch.setattr(CarModel, "delete", original)
    assert api_client.delete(f"/users/{created['_id']}").status_code == 204
    assert api_client.get(f"/cars/{car['_id']}", headers=headers).status_code == 401


def test_car_insert_racing_account_delete_is_compensated(api_client, monkeypatch):
    created = create_user(api_client, "mechanic")
    headers = auth_headers_for(api_client, "mechanic", "password123")
    original = CarModel.insert

    async def insert_after_delete(car, *args, **kwargs):
        admin = await User.get(FIRST_ADMIN_ID)
        await users_route.delete_user(PydanticObjectId(created["_id"]), admin)
        return await original(car, *args, **kwargs)

    monkeypatch.setattr(CarModel, "insert", insert_after_delete)
    assert api_client.post("/cars/", headers=headers, json={"make": "Honda", "model": "Civic", "year": 2020}).status_code == 401

    async def check():
        assert await CarModel.find_all().count() == 0

    api_client.portal.call(check)


def test_administrators_cannot_be_deleted(api_client):
    async def seed():
        user = await User(username="other-admin", password_hash=auth.DUMMY_PASSWORD_HASH, is_admin=True).insert()
        return str(user.id)

    user_id = api_client.portal.call(seed)
    assert api_client.delete(f"/users/{user_id}").status_code == 400


def test_deleting_car_rejected_by_all_owned_routes(api_client):
    car = api_client.post("/cars/", json={"make": "Honda", "model": "Civic", "year": 2020}).json()

    async def mark():
        await CarModel.get_pymongo_collection().update_one(
            {"_id": PydanticObjectId(car["_id"])}, {"$set": {"is_deleting": True}}
        )

    api_client.portal.call(mark)
    for suffix in ("", "/logs/", "/planned-mods/"):
        assert api_client.get(f"/cars/{car['_id']}{suffix}").status_code == 404


def test_mod_save_racing_cascade_does_not_leave_orphan(api_client, monkeypatch):
    created = create_user(api_client, "mechanic")
    headers = auth_headers_for(api_client, "mechanic", "password123")
    car = api_client.post("/cars/", headers=headers, json={"make": "Honda", "model": "Civic", "year": 2020}).json()
    base = f"/cars/{car['_id']}/planned-mods"
    mod = api_client.post(base + "/", headers=headers, json={
        "name": "Brakes", "type": "modification", "category": "brakes",
    }).json()
    original = ModItem.save

    async def save_after_delete(mod, *args, **kwargs):
        await users_route.delete_user(PydanticObjectId(created["_id"]), await User.get(FIRST_ADMIN_ID))
        return await original(mod, *args, **kwargs)

    monkeypatch.setattr(ModItem, "save", save_after_delete)
    assert api_client.patch(base + "/" + mod["_id"], headers=headers, json={"name": "New brakes"}).status_code == 404

    async def check():
        assert await ModItem.find_all().count() == 0

    api_client.portal.call(check)
