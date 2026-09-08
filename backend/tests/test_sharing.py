import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest
from beanie import PydanticObjectId

from backend.models.car_model import CarModel
from backend.models.car_share import CarShare
from backend.models.user import FIRST_ADMIN_ID, User
from backend.routes import car_route, users_route
from backend.tests.conftest import auth_headers_for, create_user
from backend.tests.test_carfax_api import _confirm_payload, _preview


VIEW = {"vehicle": "view", "maintenance": "view", "mods": "view"}
EDIT = dict.fromkeys(VIEW, "edit")
CAR = {"make": "Honda", "model": "Accord", "year": 2011, "vin": "1HGCP3F89BA028384", "mileage": 0}
LOG = {"date_of_service": "2024-01-15", "done_by": "shop", "mileage": 100, "cost": 25, "work_done": "Oil change"}
MOD = {"name": "Brakes", "type": "modification", "category": "brakes", "cost": 100}


@pytest.fixture
def shared(api_client):
    recipient = create_user(api_client, "mechanic")
    headers = auth_headers_for(api_client, "mechanic", "password123")
    car = api_client.post("/cars/", json=CAR).json()
    base = f"/cars/{car['_id']}"
    response = api_client.post(base + "/shares/", json={"username": "mechanic"})
    assert response.status_code == 201, response.text
    return base, recipient, headers, response.json()


def test_sharing_contract_normalization_discovery_and_revoke(api_client, shared):
    base, recipient, headers, grant = shared
    assert set(grant) == {"_id", "user_id", "username", "permissions"}
    assert grant["user_id"] == recipient["_id"]
    assert grant["permissions"] == VIEW
    assert api_client.get(base + "/shares/").json() == [grant]
    owner_car = api_client.get(base).json()
    assert owner_car["access"] == {"is_owner": True, "owner_username": "admin", "permissions": EDIT}
    car = api_client.get(base, headers=headers).json()
    assert car["access"] == {"is_owner": False, "owner_username": "admin", "permissions": VIEW}
    assert not {"shares", "owner_id", "user_id", "is_deleting"} & car.keys()
    own = api_client.post("/cars/", json=CAR, headers=headers).json()
    assert own["access"]["is_owner"] is True
    ids = sorted([car["_id"], own["_id"]])
    assert [c["_id"] for c in api_client.get("/cars/", headers=headers).json()] == ids
    for skip in range(2):
        assert [c["_id"] for c in api_client.get(f"/cars/?skip={skip}&limit=1", headers=headers).json()] == ids[skip:skip + 1]
    assert api_client.post(base + "/shares/", json={"username": " MECHANIC "}).status_code == 409
    assert api_client.post(base + "/shares/", json={"username": " ADMIN "}).status_code == 400
    for username in ("missing", "mech", "mechanic2"):
        assert api_client.post(base + "/shares/", json={"username": username}).status_code == 404
    assert api_client.get("/users/", headers=headers).status_code == 403
    url = base + "/shares/" + recipient["_id"]
    assert api_client.delete(url).status_code == 204
    for suffix in ("", "/logs/", "/stats/", "/reminders/", "/planned-mods/", "/nhtsa/", "/shares/"):
        assert api_client.get(base + suffix, headers=headers).status_code == 404
    assert [c["_id"] for c in api_client.get("/cars/", headers=headers).json()] == [own["_id"]]
    recreated = api_client.post(base + "/shares/", json={"username": " MeChAnIc "})
    assert recreated.status_code == 201
    assert recreated.json()["username"] == "mechanic"


@pytest.mark.parametrize("level", ["none", "view", "edit"])
def test_section_permissions_all_operations(api_client, shared, monkeypatch, level):
    base, recipient, headers, _ = shared
    permissions = {"vehicle": "view", "maintenance": level, "mods": level}
    url = base + "/shares/" + recipient["_id"]
    assert api_client.put(url, json={"permissions": permissions}).json()["permissions"] == permissions
    log = api_client.post(base + "/logs/", json=LOG).json()
    mod = api_client.post(base + "/planned-mods/", json=MOD).json()
    async def safety(car):
        return {"recalls": []}
    monkeypatch.setattr("backend.routes.nhtsa.get_nhtsa_data", safety)
    assert api_client.get(base, headers=headers).status_code == 200
    assert api_client.get(base + "/nhtsa/", headers=headers).status_code == 200
    assert api_client.patch(base, headers=headers, json={"mileage": 200}).status_code == 403
    for suffix in ("/logs/", "/logs/" + log["_id"], "/stats/", "/reminders/", "/planned-mods/"):
        assert api_client.get(base + suffix, headers=headers).status_code == (403 if level == "none" else 200)
    for method, suffix, payload, success in (
        ("patch", "/logs/" + log["_id"], {"cost": 50}, 200),
        ("post", "/planned-mods/", MOD, 201),
        ("patch", "/planned-mods/" + mod["_id"], {"name": "New brakes"}, 200),
        ("patch", "/planned-mods/" + mod["_id"] + "/move", {"status": "purchased", "position": 0}, 200),
    ):
        response = getattr(api_client, method)(base + suffix, headers=headers, json=payload)
        assert response.status_code == (success if level == "edit" else 403), response.text
    for suffix in ("/logs/" + log["_id"], "/planned-mods/" + mod["_id"]):
        assert api_client.delete(base + suffix, headers=headers).status_code == (204 if level == "edit" else 403)
    assert api_client.post(base + "/logs/", headers=headers, json=LOG).status_code == (201 if level == "edit" else 403)
    # Section edit never confers ownership operations.
    assert api_client.delete(base, headers=headers).status_code == 403
    assert api_client.get(base + "/shares/", headers=headers).status_code == 403
    assert api_client.post(base + "/shares/", headers=headers, json={"username": "admin"}).status_code == 403
    assert api_client.put(url, headers=headers, json={"permissions": EDIT}).status_code == 403
    assert api_client.delete(url, headers=headers).status_code == 403


def test_vehicle_edit_is_independent_and_downgrades_apply_next_request(api_client, shared):
    base, recipient, headers, _ = shared
    url = base + "/shares/" + recipient["_id"]
    permissions = {"vehicle": "edit", "maintenance": "none", "mods": "none"}
    assert api_client.put(url, json={"permissions": permissions}).status_code == 200
    response = api_client.patch(base, json={"mileage": 999}, headers=headers)
    assert response.status_code == 200
    assert response.json()["access"]["permissions"] == permissions
    assert api_client.get(base + "/logs/", headers=headers).status_code == 403
    assert api_client.get(base + "/planned-mods/", headers=headers).status_code == 403
    assert api_client.delete(base, headers=headers).status_code == 403
    assert api_client.put(url, json={"permissions": {}}).json()["permissions"] == VIEW
    assert api_client.patch(base, json={"mileage": 1000}, headers=headers).status_code == 403


@pytest.mark.parametrize("level", ["none", "view", "edit"])
def test_import_preview_confirm_and_stats_permissions(api_client, shared, monkeypatch, level):
    base, recipient, headers, _ = shared
    preview = _preview(api_client, base.split("/")[-1], monkeypatch).json()
    payload = _confirm_payload(preview)
    assert api_client.put(base + "/shares/" + recipient["_id"], json={"permissions": {"maintenance": level, "mods": "none"}}).status_code == 200
    response = api_client.post(base + "/logs/import/preview", headers=headers,
                               files={"file": ("carfax.pdf", b"%PDF-test", "application/pdf")})
    assert response.status_code == (200 if level == "edit" else 403)
    response = api_client.post(base + "/logs/import/confirm", headers=headers, json=payload)
    assert response.status_code == (201 if level == "edit" else 403)
    assert api_client.get(base + "/stats/").json()["log_count"] == (29 if level == "edit" else 0)
    if level == "edit":
        assert api_client.get(base + "/stats/", headers=headers).json()["log_count"] == 29
        assert api_client.get(base, headers=headers).json()["mileage"] == 108707
    assert api_client.delete(base + "/shares/" + recipient["_id"]).status_code == 204
    assert api_client.post(base + "/logs/import/confirm", headers=headers, json=payload).status_code == 404


def test_nested_ids_cannot_cross_cars_even_with_edit(api_client, shared):
    base, recipient, headers, _ = shared
    api_client.put(base + "/shares/" + recipient["_id"], json={"permissions": EDIT})
    other = api_client.post("/cars/", json=CAR).json()
    foreign = f"/cars/{other['_id']}"
    log = api_client.post(foreign + "/logs/", json=LOG).json()
    mod = api_client.post(foreign + "/planned-mods/", json=MOD).json()
    for target in (base, foreign):
        for method, suffix, payload in (
            ("get", "/logs/" + log["_id"], None),
            ("patch", "/logs/" + log["_id"], {"cost": 0}),
            ("delete", "/logs/" + log["_id"], None),
            ("patch", "/planned-mods/" + mod["_id"], {"name": "Stolen"}),
            ("patch", "/planned-mods/" + mod["_id"] + "/move", {"status": "purchased", "position": 0}),
            ("delete", "/planned-mods/" + mod["_id"], None),
        ):
            response = api_client.request(method, target + suffix, headers=headers, **({"json": payload} if payload else {}))
            assert response.status_code == 404, response.text
    assert api_client.get(foreign + "/logs/" + log["_id"]).json()["cost"] == 25


@pytest.mark.parametrize("permissions", [{"vehicle": "none"}, {"maintenance": "owner"}, {"mods": None}, {"sharing": "edit"}])
def test_invalid_permissions_rejected(api_client, shared, permissions):
    base, recipient, _, _ = shared
    assert api_client.put(base + "/shares/" + recipient["_id"], json={"permissions": permissions}).status_code == 422
    assert api_client.post(base + "/shares/", json={"username": "mechanic", "permissions": permissions}).status_code == 422


@pytest.mark.parametrize("deleted", ["owner", "recipient", "vehicle"])
def test_deletion_cleans_grants_without_deleting_received_cars(api_client, deleted):
    owner = create_user(api_client, "owner")
    recipient = create_user(api_client, "recipient")
    headers = auth_headers_for(api_client, "owner", "password123")
    car = api_client.post("/cars/", json=CAR, headers=headers).json()
    base = f"/cars/{car['_id']}"
    assert api_client.post(base + "/shares/", headers=headers, json={"username": "recipient"}).status_code == 201
    admin_car = api_client.post("/cars/", json=CAR).json()
    assert api_client.post(f"/cars/{admin_car['_id']}/shares/", json={"username": "owner"}).status_code == 201
    if deleted == "vehicle":
        assert api_client.delete(base, headers=headers).status_code == 204
    else:
        assert api_client.delete("/users/" + (owner if deleted == "owner" else recipient)["_id"]).status_code == 204
    async def check():
        assert await CarShare.find(CarShare.car_id == PydanticObjectId(car["_id"])).count() == 0
        if deleted == "owner":
            assert await CarShare.find_all().count() == 0
        assert await CarModel.get(PydanticObjectId(admin_car["_id"])) is not None
    api_client.portal.call(check)
    if deleted == "recipient":
        assert api_client.get(base, headers=headers).status_code == 200


@pytest.mark.parametrize("deleted", ["owner", "recipient", "vehicle"])
def test_grant_insert_racing_deletion_is_compensated(api_client, monkeypatch, deleted):
    owner = create_user(api_client, "owner")
    recipient = create_user(api_client, "recipient")
    headers = auth_headers_for(api_client, "owner", "password123")
    car = api_client.post("/cars/", headers=headers, json=CAR).json()
    original = CarShare.insert
    async def insert_after_cascade(grant, *args, **kwargs):
        if deleted == "vehicle":
            await car_route.delete_car(await CarModel.get(grant.car_id))
        else:
            target = owner if deleted == "owner" else recipient
            await users_route.delete_user(PydanticObjectId(target["_id"]), await User.get(FIRST_ADMIN_ID))
        return await original(grant, *args, **kwargs)
    monkeypatch.setattr(CarShare, "insert", insert_after_cascade)
    assert api_client.post(f"/cars/{car['_id']}/shares/", headers=headers, json={"username": "recipient"}).status_code == 404
    async def check():
        assert await CarShare.find_all().count() == 0
    api_client.portal.call(check)


def test_inactive_recipient_and_owner_are_inaccessible(api_client, shared):
    base, recipient, headers, _ = shared
    async def mark(user_id):
        await User.get_pymongo_collection().update_one({"_id": user_id}, {"$set": {"is_deleting": True}})
    api_client.portal.call(mark, PydanticObjectId(recipient["_id"]))
    assert api_client.post(base + "/shares/", json={"username": "mechanic"}).status_code == 404
    assert api_client.put(base + "/shares/" + recipient["_id"], json={"permissions": EDIT}).status_code == 404
    assert api_client.get(base + "/shares/").json() == []
    assert api_client.get(base, headers=headers).status_code == 401


def test_deleting_owner_hidden_before_vehicle_cascade(api_client, shared):
    base, _, headers, _ = shared
    async def mark():
        await User.get_pymongo_collection().update_one({"_id": FIRST_ADMIN_ID}, {"$set": {"is_deleting": True}})
    api_client.portal.call(mark)
    assert api_client.get("/cars/", headers=headers).json() == []
    for suffix in ("", "/logs/", "/stats/", "/reminders/", "/planned-mods/", "/nhtsa/"):
        assert api_client.get(base + suffix, headers=headers).status_code == 404


def test_concurrent_grants_have_one_winner_and_registered_indexes(api_client, monkeypatch):
    create_user(api_client, "mechanic")
    car = api_client.post("/cars/", json=CAR).json()
    original = CarShare.insert
    arrived = 0
    ready = asyncio.Event()
    async def synchronized_insert(grant, *args, **kwargs):
        nonlocal arrived
        arrived += 1
        if arrived == 2:
            ready.set()
        await asyncio.wait_for(ready.wait(), timeout=5)
        return await original(grant, *args, **kwargs)
    monkeypatch.setattr(CarShare, "insert", synchronized_insert)
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda username: api_client.post(
            f"/cars/{car['_id']}/shares/", json={"username": username}
        ), ["mechanic", " MECHANIC "]))
    assert sorted(response.status_code for response in responses) == [201, 409]
    async def check():
        indexes = await CarShare.get_pymongo_collection().index_information()
        assert indexes["unique_car_recipient"]["unique"] is True
        assert list(indexes["unique_car_recipient"]["key"]) == [("car_id", 1), ("user_id", 1)]
        assert list(indexes["share_recipient"]["key"]) == [("user_id", 1)]
        assert await CarShare.find_all().count() == 1
    api_client.portal.call(check)


def test_mods_edit_does_not_enable_maintenance_and_revoke_blocks_writes(api_client, shared):
    base, recipient, headers, _ = shared
    url = base + "/shares/" + recipient["_id"]
    assert api_client.put(url, json={"permissions": {"mods": "edit", "maintenance": "none"}}).status_code == 200
    mod = api_client.post(base + "/planned-mods/", headers=headers, json=MOD)
    assert mod.status_code == 201
    assert api_client.post(base + "/logs/", headers=headers, json=LOG).status_code == 403
    assert api_client.get(base + "/stats/", headers=headers).status_code == 403
    assert api_client.delete(url).status_code == 204
    for method, suffix, payload in (
        ("patch", "", {"mileage": 100}),
        ("post", "/logs/", LOG),
        ("post", "/planned-mods/", MOD),
        ("patch", "/planned-mods/" + mod.json()["_id"], {"name": "Revoked"}),
        ("patch", "/planned-mods/" + mod.json()["_id"] + "/move", {"status": "purchased", "position": 0}),
        ("delete", "/planned-mods/" + mod.json()["_id"], None),
    ):
        assert api_client.request(method, base + suffix, headers=headers,
                                  **({"json": payload} if payload else {})).status_code == 404


def test_share_update_racing_revocation_does_not_upsert(api_client, shared, monkeypatch):
    base, recipient, _, _ = shared
    collection = CarShare.get_pymongo_collection()
    original = collection.update_one
    async def revoke_then_update(query, update, *args, **kwargs):
        await collection.delete_one(query)
        return await original(query, update, *args, **kwargs)
    monkeypatch.setattr(collection, "update_one", revoke_then_update)
    assert api_client.put(base + "/shares/" + recipient["_id"], json={"permissions": EDIT}).status_code == 404
    assert api_client.get(base + "/shares/").json() == []


def test_sharing_missing_relationships_and_untrusted_fields(api_client, shared):
    base, recipient, headers, _ = shared
    outsider = create_user(api_client, "outsider")
    outsider_headers = auth_headers_for(api_client, "outsider", "password123")
    url = base + "/shares/" + outsider["_id"]
    for method, path, payload in (
        ("get", base + "/shares/", None),
        ("post", base + "/shares/", {"username": "outsider"}),
        ("put", url, {"permissions": EDIT}),
        ("delete", url, None),
    ):
        assert api_client.request(method, path, headers=outsider_headers,
                                  **({"json": payload} if payload else {})).status_code == 404
    assert api_client.put(url, json={"permissions": EDIT}).status_code == 404
    assert api_client.delete(url).status_code == 404
    assert api_client.put(base + "/shares/" + recipient["_id"], json={}).status_code == 422
    assert api_client.post(base + "/shares/", json={"username": "outsider", "user_id": recipient["_id"]}).status_code == 422
    api_client.put(base + "/shares/" + recipient["_id"], json={"permissions": EDIT})
    for payload in ({"owner_id": recipient["_id"]}, {"access": {"is_owner": True}}, {"shares": []}):
        assert api_client.patch(base, headers=headers, json=payload).status_code == 422
    assert api_client.get(base, headers=headers).json()["access"]["is_owner"] is False
