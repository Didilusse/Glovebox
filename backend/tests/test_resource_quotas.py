from datetime import date

from backend.config import settings
from backend.models.notification import Notification
from backend.services import notifications
from backend.tests.conftest import auth_headers_for, create_user
from backend.tests.test_api import create_car, create_log
from backend.tests.test_mods_api import create_mod


def test_car_quota_is_per_user_and_delete_releases_capacity(api_client, monkeypatch):
    monkeypatch.setattr(settings, "max_cars_per_user", 1)
    car = create_car(api_client)
    assert api_client.post("/cars/", json={
        "make": "Honda", "model": "Civic", "year": 2020,
    }).status_code == 409

    create_user(api_client, "driver")
    headers = auth_headers_for(api_client, "driver", "password1234")
    assert api_client.post("/cars/", headers=headers, json={
        "make": "Honda", "model": "Civic", "year": 2020,
    }).status_code == 201

    assert api_client.delete(f"/cars/{car['_id']}").status_code == 204
    assert api_client.post("/cars/", json={
        "make": "Mazda", "model": "3", "year": 2020,
    }).status_code == 201


def test_child_quotas_are_per_car_and_deletes_release_capacity(api_client, monkeypatch):
    monkeypatch.setattr(settings, "max_maintenance_logs_per_car", 1)
    monkeypatch.setattr(settings, "max_mods_per_car", 1)
    first = create_car(api_client)
    second = create_car(api_client, license_plate="OTHER")

    log = create_log(api_client, first["_id"])
    assert api_client.post(f"/cars/{first['_id']}/logs/", json={
        "date_of_service": date.today().isoformat(), "done_by": "shop",
        "mileage": 1, "cost": 1, "work_done": "Inspection",
    }).status_code == 409
    create_log(api_client, second["_id"])
    assert api_client.delete(f"/cars/{first['_id']}/logs/{log['_id']}").status_code == 204
    create_log(api_client, first["_id"])

    mod = create_mod(api_client, first["_id"], "First")
    assert api_client.post(f"/cars/{first['_id']}/planned-mods/", json={
        "name": "Blocked", "type": "modification", "category": "engine",
    }).status_code == 409
    create_mod(api_client, second["_id"], "Other car")
    assert api_client.delete(f"/cars/{first['_id']}/planned-mods/{mod['_id']}").status_code == 204
    create_mod(api_client, first["_id"], "Replacement")


def test_notification_events_and_retention_are_bounded_per_user(api_client, monkeypatch):
    monkeypatch.setattr(settings, "max_notifications_per_user", 1)
    first = create_car(api_client, mileage=20_000)
    second = create_car(api_client, mileage=20_000, license_plate="OTHER")
    create_log(api_client, first["_id"], mileage=1_000, interval_miles=1_000)
    create_log(api_client, second["_id"], mileage=1_000, interval_miles=1_000)

    api_client.portal.call(notifications.check_due_reminders)

    async def count():
        return await Notification.find_all().count()

    assert api_client.portal.call(count) == 1
    assert len(api_client.get("/notifications/").json()) == 1
