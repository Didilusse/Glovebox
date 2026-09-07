from backend.tests.conftest import auth_headers_for, create_user


def get_admin_id(api_client):
    return api_client.get("/auth/me", headers={}).json()["_id"]


def test_admin_lists_and_creates_users(api_client):
    users = api_client.get("/users/")
    assert users.status_code == 200
    assert [user["username"] for user in users.json()] == ["admin"]

    created = create_user(api_client, "mechanic")
    assert created["username"] == "mechanic"
    assert created["is_admin"] is False
    assert "password_hash" not in created

    duplicate = api_client.post(
        "/users/", json={"username": "MECHANIC", "password": "password123"}
    )
    assert duplicate.status_code == 409

    weak = api_client.post("/users/", json={"username": "helper", "password": "short"})
    assert weak.status_code == 422


def test_non_admin_cannot_manage_users(api_client):
    create_user(api_client, "mechanic")
    mechanic = auth_headers_for(api_client, "mechanic", "password123")

    assert api_client.get("/users/", headers=mechanic).status_code == 403
    assert api_client.post(
        "/users/", json={"username": "helper", "password": "password123"}, headers=mechanic
    ).status_code == 403

    admin_id = get_admin_id(api_client)
    assert api_client.get("/users/", headers=mechanic).status_code == 403
    assert api_client.delete(f"/users/{admin_id}", headers=mechanic).status_code == 403

    # Regular API access still works for the non-admin user.
    assert api_client.get("/cars/", headers=mechanic).status_code == 200


def test_admin_resets_password_and_revokes_sessions(api_client):
    created = create_user(api_client, "mechanic")
    mechanic = auth_headers_for(api_client, "mechanic", "password123")

    reset = api_client.patch(
        f"/users/{created['_id']}/password", json={"new_password": "brand-new-pass"}
    )
    assert reset.status_code == 204

    assert api_client.get("/auth/me", headers=mechanic).status_code == 401
    assert api_client.post(
        "/auth/login", json={"username": "mechanic", "password": "password123"}, headers={}
    ).status_code == 401
    assert api_client.post(
        "/auth/login", json={"username": "mechanic", "password": "brand-new-pass"}, headers={}
    ).status_code == 200

    assert api_client.patch(
        f"/users/{created['_id']}/password", json={"new_password": "tiny"}
    ).status_code == 422
    assert api_client.patch(
        "/users/000000000000000000000000/password",
        json={"new_password": "brand-new-pass"},
    ).status_code == 404


def test_admin_deletes_user_and_their_garage(api_client):
    created = create_user(api_client, "mechanic")
    mechanic = auth_headers_for(api_client, "mechanic", "password123")

    car_response = api_client.post(
        "/cars/",
        json={"make": "Honda", "model": "Civic", "year": 2019, "mileage": 30_000},
        headers=mechanic,
    )
    assert car_response.status_code == 201
    car_id = car_response.json()["_id"]

    deleted = api_client.delete(f"/users/{created['_id']}")
    assert deleted.status_code == 204

    assert api_client.get(f"/cars/{car_id}", headers={}).status_code == 404
    assert api_client.post(
        "/auth/login", json={"username": "mechanic", "password": "password123"}, headers={}
    ).status_code == 401

    remaining = api_client.get("/users/")
    assert [user["username"] for user in remaining.json()] == ["admin"]


def test_admin_cannot_delete_self(api_client):
    admin_id = get_admin_id(api_client)
    assert api_client.delete(f"/users/{admin_id}").status_code == 400
    assert api_client.get("/auth/me", headers={}).status_code == 200
