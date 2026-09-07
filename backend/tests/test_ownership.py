from backend.tests.conftest import auth_headers_for, create_user

OWNERLESS_ID = "000000000000000000000000"


def create_admin_car(api_client):
    response = api_client.post(
        "/cars/",
        json={"make": "Toyota", "model": "Camry", "year": 2020, "mileage": 50_000},
    )
    assert response.status_code == 201, response.text
    return response.json()["_id"]


def test_car_list_only_shows_own_cars(api_client):
    admin_car = create_admin_car(api_client)

    create_user(api_client, "mechanic")
    mechanic = auth_headers_for(api_client, "mechanic", "password123")

    assert [car["_id"] for car in api_client.get("/cars/", headers=mechanic).json()] == []

    mechanic_car = api_client.post(
        "/cars/",
        json={"make": "Honda", "model": "Civic", "year": 2019, "mileage": 30_000},
        headers=mechanic,
    ).json()
    assert [car["_id"] for car in api_client.get("/cars/", headers=mechanic).json()] == [
        mechanic_car["_id"]
    ]
    assert [car["_id"] for car in api_client.get("/cars/").json()] == [admin_car]


def test_other_users_get_404_for_foreign_car(api_client):
    car_id = create_admin_car(api_client)

    create_user(api_client, "mechanic")
    mechanic = auth_headers_for(api_client, "mechanic", "password123")

    assert api_client.get(f"/cars/{car_id}", headers=mechanic).status_code == 404
    assert api_client.patch(
        f"/cars/{car_id}", json={"mileage": 51_000}, headers=mechanic
    ).status_code == 404
    assert api_client.delete(f"/cars/{car_id}", headers=mechanic).status_code == 404

    # The car survives the forbidden attempts.
    assert api_client.get(f"/cars/{car_id}").status_code == 200


def test_child_resources_reject_foreign_car(api_client):
    car_id = create_admin_car(api_client)

    create_user(api_client, "mechanic")
    mechanic = auth_headers_for(api_client, "mechanic", "password123")

    log_payload = {
        "date_of_service": "2024-01-15",
        "done_by": "shop",
        "mileage": 51_000,
        "cost": 100,
        "work_done": "Oil change",
    }
    assert api_client.post(f"/cars/{car_id}/logs/", json=log_payload, headers=mechanic).status_code == 404
    assert api_client.get(f"/cars/{car_id}/logs/", headers=mechanic).status_code == 404
    assert api_client.get(f"/cars/{car_id}/reminders/", headers=mechanic).status_code == 404
    assert api_client.get(f"/cars/{car_id}/stats/", headers=mechanic).status_code == 404
    assert api_client.get(f"/cars/{car_id}/nhtsa/", headers=mechanic).status_code == 404

    mod_payload = {"name": "Coilovers", "type": "modification", "category": "suspension", "cost": 900}
    assert api_client.post(f"/cars/{car_id}/planned-mods/", json=mod_payload, headers=mechanic).status_code == 404
    assert api_client.get(f"/cars/{car_id}/planned-mods/", headers=mechanic).status_code == 404
    assert api_client.post(
        f"/cars/{car_id}/logs/import/preview", headers=mechanic
    ).status_code in (404, 422)


def test_owner_full_access_to_child_resources(api_client):
    car_id = create_admin_car(api_client)

    log_payload = {
        "date_of_service": "2024-01-15",
        "done_by": "shop",
        "mileage": 51_000,
        "cost": 100,
        "work_done": "Oil change",
    }
    log = api_client.post(f"/cars/{car_id}/logs/", json=log_payload)
    assert log.status_code == 201

    assert api_client.get(f"/cars/{car_id}/logs/").status_code == 200
    assert api_client.get(f"/cars/{car_id}/logs/{log.json()['_id']}").status_code == 200
    assert api_client.get(f"/cars/{car_id}/reminders/").status_code == 200
    assert api_client.get(f"/cars/{car_id}/stats/").status_code == 200
