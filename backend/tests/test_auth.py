from backend.models.car_model import CarModel
from backend.tests.conftest import auth_headers_for, create_user


def test_status_and_setup_creates_first_admin(raw_client):
    assert raw_client.get("/auth/status").json() == {"setup_required": True, "setup_token_required": False}

    response = raw_client.post(
        "/auth/setup",
        json={"username": "Admin", "password": "longenough1"},
    )
    assert response.status_code == 201, response.text
    payload = response.json()
    assert payload["user"]["username"] == "admin"
    assert payload["user"]["is_admin"] is True
    assert payload["token"]

    assert raw_client.get("/auth/status").json() == {"setup_required": False, "setup_token_required": False}

    headers = {"Authorization": f"Bearer {payload['token']}"}
    me = raw_client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["username"] == "admin"


def test_setup_rejects_second_admin_and_weak_payloads(raw_client):
    assert raw_client.post(
        "/auth/setup", json={"username": "has space", "password": "longenough1"}
    ).status_code == 422

    assert raw_client.post(
        "/auth/setup", json={"username": "admin", "password": "longenough1"}
    ).status_code == 201

    assert raw_client.post(
        "/auth/setup", json={"username": "other", "password": "longenough2"}
    ).status_code == 403

    assert raw_client.post(
        "/auth/setup", json={"username": "short", "password": "tiny"}
    ).status_code == 422


def test_setup_claims_preexisting_ownerless_cars(raw_client):
    async def insert_ownerless_car():
        car = CarModel(make="Toyota", model="Supra", year=1994, mileage=120_000)
        await car.insert()
        return car

    car = raw_client.portal.call(insert_ownerless_car)

    payload = raw_client.post(
        "/auth/setup", json={"username": "admin", "password": "longenough1"}
    ).json()
    headers = {"Authorization": f"Bearer {payload['token']}"}

    cars = raw_client.get("/cars/", headers=headers).json()
    assert [entry["_id"] for entry in cars] == [str(car.id)]


def test_login_and_logout(raw_client):
    raw_client.post("/auth/setup", json={"username": "admin", "password": "longenough1"})

    wrong_password = raw_client.post(
        "/auth/login", json={"username": "admin", "password": "wrongpassword"}
    )
    assert wrong_password.status_code == 401

    unknown_user = raw_client.post(
        "/auth/login", json={"username": "ghost", "password": "longenough1"}
    )
    assert unknown_user.status_code == 401

    login = raw_client.post(
        "/auth/login", json={"username": "admin", "password": "longenough1"}
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['token']}"}

    assert raw_client.get("/cars/", headers=headers).status_code == 200

    assert raw_client.post("/auth/logout", headers=headers).status_code == 204
    assert raw_client.get("/auth/me", headers=headers).status_code == 401


def test_protected_routes_reject_missing_tokens(raw_client):
    raw_client.post("/auth/setup", json={"username": "admin", "password": "longenough1"})

    assert raw_client.get("/cars/").status_code == 401
    assert raw_client.get("/auth/me").status_code == 401
    assert raw_client.post("/cars/", json={"make": "A", "model": "B", "year": 2020}).status_code == 401


def test_change_password_revokes_other_sessions(raw_client):
    setup_payload = raw_client.post(
        "/auth/setup", json={"username": "admin", "password": "longenough1"}
    ).json()
    first = {"Authorization": f"Bearer {setup_payload['token']}"}

    second_token = raw_client.post(
        "/auth/login", json={"username": "admin", "password": "longenough1"}
    ).json()["token"]
    second = {"Authorization": f"Bearer {second_token}"}

    wrong_current = raw_client.post(
        "/auth/password",
        json={"current_password": "wrong", "new_password": "longenough2"},
        headers=first,
    )
    assert wrong_current.status_code == 400

    change = raw_client.post(
        "/auth/password",
        json={"current_password": "longenough1", "new_password": "longenough2"},
        headers=first,
    )
    assert change.status_code == 204

    # The session that made the change stays valid; others are revoked.
    assert raw_client.get("/auth/me", headers=first).status_code == 200
    assert raw_client.get("/auth/me", headers=second).status_code == 401

    relogin = raw_client.post(
        "/auth/login", json={"username": "admin", "password": "longenough2"}
    )
    assert relogin.status_code == 200
    assert raw_client.post(
        "/auth/login", json={"username": "admin", "password": "longenough1"}
    ).status_code == 401


def test_created_user_can_log_in_and_sees_empty_garage(api_client):
    create_user(api_client, "mechanic", "password123")

    headers = auth_headers_for(api_client, "mechanic", "password123")
    me = api_client.get("/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["is_admin"] is False

    assert api_client.get("/cars/", headers=headers).json() == []
