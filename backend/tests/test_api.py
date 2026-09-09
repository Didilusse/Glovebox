from datetime import date

from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog
from backend.models.mod import ModItem


def create_car(client, **overrides):
    payload = {
        "make": "Toyota",
        "model": "Camry",
        "year": 2020,
        "mileage": 50_000,
        "fuel_type": "gas",
    }
    payload.update(overrides)
    response = client.post("/cars/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def create_log(client, car_id, **overrides):
    payload = {
        "date_of_service": date.today().isoformat(),
        "done_by": "shop",
        "mileage": 51_000,
        "cost": 125.50,
        "work_done": "Oil change",
        "category": "engine",
        "interval_miles": 5_000,
    }
    payload.update(overrides)
    response = client.post(f"/cars/{car_id}/logs/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_car_crud_contract_and_pagination(api_client):
    car = create_car(
        api_client,
        license_plate="ABC-123",
        purchased_price=25_000,
    )
    assert car["_id"]
    assert car["license_plate"] == "ABC-123"
    assert car["initial_mileage"] == 50_000

    response = api_client.post(
        "/cars/",
        json={"make": "A", "model": "B", "year": 2020, "licensePlate": "ignored"},
    )
    assert response.status_code == 422

    response = api_client.patch(f"/cars/{car['_id']}", json={"mileage": 50_500})
    assert response.status_code == 200
    assert response.json()["mileage"] == 50_500

    assert api_client.patch(f"/cars/{car['_id']}", json={"mileage": None}).status_code == 422
    assert api_client.get("/cars/?limit=0").status_code == 422
    assert api_client.get("/cars/not-an-object-id").status_code == 422


def test_car_create_and_update_reject_invalid_vins(api_client):
    invalid_vin = "1HGCM82643A004352"
    response = api_client.post("/cars/", json={"make": "Honda", "model": "Accord", "year": 2003, "vin": invalid_vin})
    assert response.status_code == 422
    assert "check digit" in response.text

    car = create_car(api_client)
    response = api_client.patch(f"/cars/{car['_id']}", json={"vin": invalid_vin})
    assert response.status_code == 422
    assert "check digit" in response.text

    response = api_client.patch(f"/cars/{car['_id']}", json={"vin": "1hgcm82633a004352"})
    assert response.status_code == 200
    assert response.json()["vin"] == "1HGCM82633A004352"


def test_maintenance_updates_mileage_and_rejects_invalid_updates(api_client):
    car = create_car(api_client)
    log = create_log(api_client, car["_id"], mileage=52_000)

    response = api_client.get(f"/cars/{car['_id']}")
    assert response.json()["mileage"] == 52_000

    response = api_client.patch(
        f"/cars/{car['_id']}/logs/{log['_id']}",
        json={"mileage": 53_000, "interval_miles": 6_000},
    )
    assert response.status_code == 200
    assert response.json()["reminder_mileage"] == 59_000
    assert api_client.get(f"/cars/{car['_id']}").json()["mileage"] == 53_000

    response = api_client.patch(
        f"/cars/{car['_id']}/logs/{log['_id']}",
        json={"work_done": None},
    )
    assert response.status_code == 422
    assert api_client.get(f"/cars/{car['_id']}/logs/?limit=101").status_code == 422


def test_car_delete_cascades_to_logs_and_mods(api_client):
    car = create_car(api_client)
    create_log(api_client, car["_id"])
    mod_response = api_client.post(
        f"/cars/{car['_id']}/planned-mods/",
        json={
            "name": "Coilovers",
            "type": "modification",
            "category": "suspension",
            "cost": 900,
            "url": "https://example.com/coilovers",
        },
    )
    assert mod_response.status_code == 201
    assert mod_response.json()["url"] == "https://example.com/coilovers"

    assert api_client.delete(f"/cars/{car['_id']}").status_code == 204
    assert api_client.get(f"/cars/{car['_id']}").status_code == 404

    async def dependent_counts():
        return await MaintenanceLog.find_all().count(), await ModItem.find_all().count()

    assert api_client.portal.call(dependent_counts) == (0, 0)


def test_deleting_car_rejects_racing_child_creation(api_client):
    car = create_car(api_client)

    async def mark_deleting():
        stored_car = await CarModel.get(car["_id"])
        await stored_car.update({"$set": {"is_deleting": True}})

    api_client.portal.call(mark_deleting)
    log_response = api_client.post(
        f"/cars/{car['_id']}/logs/",
        json={
            "date_of_service": date.today().isoformat(),
            "done_by": "shop",
            "mileage": 51_000,
            "cost": 100,
            "work_done": "Oil change",
        },
    )
    mod_response = api_client.post(
        f"/cars/{car['_id']}/planned-mods/",
        json={"name": "Part", "type": "modification", "category": "engine"},
    )
    assert log_response.status_code == 404
    assert mod_response.status_code == 404


def test_reminders_and_stats(api_client):
    car = create_car(api_client, mileage=60_000)
    create_log(api_client, car["_id"], mileage=50_000, interval_miles=5_000, cost=100)

    reminders = api_client.get(f"/cars/{car['_id']}/reminders/?only_due=true").json()
    assert len(reminders) == 1
    assert reminders[0]["is_due"] is True
    assert reminders[0]["due_reason"] == "mileage"

    stats = api_client.get(f"/cars/{car['_id']}/stats/")
    assert stats.status_code == 200
    assert stats.json()["log_count"] == 1
    assert stats.json()["total_spent"] == 100
