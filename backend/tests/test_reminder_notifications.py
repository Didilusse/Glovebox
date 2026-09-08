import asyncio
from datetime import date, datetime, timedelta, timezone

import pytest
from beanie import PydanticObjectId
from mongomock_motor import AsyncMongoMockCollection

from backend.config import settings
from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog
from backend.models.notification import Notification, UserPreferences
from backend.models.user import FIRST_ADMIN_ID, User
from backend.services import notifications
from backend.services.reminders import car_reminders
from backend.tests.conftest import auth_headers_for, create_user


DESTINATIONS = {
    "webhook_url": "https://example.com/reminders",
    "discord_webhook_url": "https://discord.com/api/webhooks/123/test-token",
    "email": "driver@example.com",
}


@pytest.fixture(autouse=True)
def preserve_mock_partial_index(api_client):
    async def repair():
        collection = MaintenanceLog.get_pymongo_collection()
        if not isinstance(collection, AsyncMongoMockCollection):
            return
        # mongomock's create_indexes drops partialFilterExpression; create_index
        # supports it. Preserve the production constraint rather than dropping it.
        for index in MaintenanceLog.Settings.indexes:
            if not hasattr(index, "document") or "partialFilterExpression" not in index.document:
                continue
            definition = dict(index.document)
            keys = list(definition.pop("key").items())
            existing = await collection.index_information()
            if existing[definition["name"]].get("partialFilterExpression") != definition["partialFilterExpression"]:
                await collection.drop_index(definition["name"])
                await collection.create_index(keys, **definition)

    api_client.portal.call(repair)


@pytest.fixture(autouse=True)
def deliveries(monkeypatch):
    calls = []

    async def fake_deliver(channel, destination, title, message):
        calls.append((channel, destination, title, message))
        await asyncio.sleep(0)

    monkeypatch.setattr(notifications, "deliver", fake_deliver)
    # Fail closed if code starts bypassing the dispatch boundary in the future.
    def forbidden(*args, **kwargs):
        pytest.fail("Notification regression tests must not perform network delivery")

    monkeypatch.setattr("backend.services.notification_delivery._webhook", forbidden)
    monkeypatch.setattr("backend.services.notification_delivery.smtplib.SMTP", forbidden)
    monkeypatch.setattr("backend.services.notification_delivery.smtplib.SMTP_SSL", forbidden)
    return calls


def make_car(client, headers=None, **overrides):
    response = client.post("/cars/", headers=headers, json={
        "make": "Honda", "model": "Accord", "year": 2011,
        "mileage": 10000, **overrides,
    })
    assert response.status_code == 201, response.text
    return "/cars/" + response.json()["_id"]


def make_log(client, base, headers=None, **overrides):
    response = client.post(base + "/logs/", headers=headers, json={
        "date_of_service": "2020-01-01", "done_by": "shop",
        "mileage": 1000, "cost": 25, "work_done": "Oil change", **overrides,
    })
    assert response.status_code == 201, response.text
    return response.json()


def stored_notifications(client):
    async def read():
        return await Notification.find_all().to_list()

    return client.portal.call(read)


@pytest.mark.parametrize("method,path,payload", [
    ("get", "/settings", None),
    ("put", "/settings", {}),
    ("get", "/reminders/due", None),
    ("get", "/notifications/", None),
    ("patch", "/notifications/000000000000000000000001/read", None),
])
def test_endpoints_require_authentication(api_client, method, path, payload):
    response = api_client.request(method, path, headers={"Authorization": ""},
                                  **({"json": payload} if payload is not None else {}))
    assert response.status_code == 401


def test_preferences_defaults_isolation_and_email_availability(api_client, monkeypatch):
    create_user(api_client, "driver")
    headers = auth_headers_for(api_client, "driver", "password123")
    monkeypatch.setattr(settings, "smtp_host", None)
    monkeypatch.setattr(settings, "smtp_from", None)
    defaults = api_client.get("/settings").json()
    assert defaults == {"oil_interval_miles": 5000, "oil_interval_months": 6,
                        **dict.fromkeys(DESTINATIONS), "email_available": False}
    custom = {"oil_interval_miles": 7500, "oil_interval_months": None, **DESTINATIONS}
    response = api_client.put("/settings", json=custom, headers=headers)
    assert response.status_code == 200, response.text
    assert response.json() == {**custom, "email_available": False}
    assert api_client.get("/settings").json() == defaults
    assert api_client.get("/settings", headers=headers).json() == response.json()
    monkeypatch.setattr(settings, "smtp_host", "smtp.example.com")
    monkeypatch.setattr(settings, "smtp_from", "glovebox@example.com")
    assert api_client.get("/settings").json()["email_available"] is True
    assert api_client.put("/settings", json=custom, headers=headers).status_code == 200

    async def count():
        return await UserPreferences.find_all().count()

    assert api_client.portal.call(count) == 1


@pytest.mark.parametrize("payload", [
    {"oil_interval_miles": 0}, {"oil_interval_miles": -1},
    {"oil_interval_miles": 1000001}, {"oil_interval_months": 0},
    {"oil_interval_months": 1201}, {"user_id": "someone-else"},
    {"webhook_url": "http://example.com/hook"},
    {"webhook_url": "https://localhost/hook"},
    {"webhook_url": "https://127.0.0.1/hook"},
    {"webhook_url": "https://[::1]/hook"},
    {"webhook_url": "https://169.254.169.254/latest/meta-data"},
    {"webhook_url": "https://user:secret@example.com/hook"},
    {"webhook_url": "https://example.com:8443/hook"},
    {"webhook_url": "https://example.com/hook#fragment"},
    {"discord_webhook_url": "https://example.com/api/webhooks/123/token"},
    {"discord_webhook_url": "https://discord.com/not-a-webhook"},
    {"email": "not-an-email"}, {"email": "a@example.com\r\nBcc: victim@example.com"},
])
def test_invalid_preferences_do_not_change_saved_settings(api_client, payload):
    before = api_client.get("/settings").json()
    response = api_client.put("/settings", json=payload)
    assert response.status_code == 422, response.text
    assert api_client.get("/settings").json() == before


def test_oil_defaults_custom_per_user_and_explicit_null(api_client):
    base = make_car(api_client)
    default = make_log(api_client, base)
    assert (default["interval_miles"], default["interval_months"]) == (5000, 6)
    assert (default["reminder_mileage"], default["reminder_date"]) == (6000, "2020-07-01")
    create_user(api_client, "driver")
    headers = auth_headers_for(api_client, "driver", "password123")
    assert api_client.put("/settings", headers=headers, json={
        "oil_interval_miles": 7500, "oil_interval_months": 9,
    }).status_code == 200
    other = make_car(api_client, headers)
    custom = make_log(api_client, other, headers, work_done="Engine OIL changed")
    assert (custom["reminder_mileage"], custom["reminder_date"]) == (8500, "2020-10-01")
    partial = make_log(api_client, other, headers, interval_miles=None)
    assert partial["interval_miles"] is None and partial["reminder_mileage"] is None
    assert partial["interval_months"] == 9
    explicit = make_log(api_client, other, headers, interval_miles=2000, interval_months=None)
    assert explicit["reminder_mileage"] == 3000 and explicit["reminder_date"] is None
    disabled = make_log(api_client, other, headers, interval_miles=None, interval_months=None)
    assert disabled["reminder_mileage"] is None and disabled["reminder_date"] is None
    assert make_log(api_client, base)["interval_miles"] == 5000
    unrelated = make_log(api_client, base, work_done="Oil leak inspection")
    assert unrelated["interval_miles"] is None and unrelated["interval_months"] is None
    assert unrelated["_id"] not in {r["log_id"] for r in api_client.get(base + "/reminders/").json()}
    assert api_client.put("/settings", headers=headers, json={
        "oil_interval_miles": None, "oil_interval_months": None,
    }).status_code == 200
    assert make_log(api_client, other, headers)["reminder_date"] is None
    assert api_client.get(base + "/logs/" + default["_id"]).json() == default


def test_latest_oil_service_supersedes_history_even_without_reminder(api_client):
    base = make_car(api_client)
    latest = make_log(api_client, base, date_of_service="2022-01-01")
    make_log(api_client, base, date_of_service="2020-01-01")
    unrelated = make_log(api_client, base, work_done="Brake inspection", interval_months=12)
    assert {r["log_id"] for r in api_client.get(base + "/reminders/").json()} == {
        latest["_id"], unrelated["_id"],
    }
    make_log(api_client, base, date_of_service="2023-01-01", interval_miles=None, interval_months=None)
    assert [r["log_id"] for r in api_client.get(base + "/reminders/").json()] == [unrelated["_id"]]


@pytest.mark.parametrize("current,today,reason,overdue", [
    (5999, date(2020, 6, 30), None, False),
    (6000, date(2020, 6, 30), "mileage", False),
    (5999, date(2020, 7, 1), "date", False),
    (6000, date(2020, 7, 1), "both", False),
    (6001, date(2020, 7, 1), "both", True),
    (6000, date(2020, 7, 2), "both", True),
])
def test_due_inclusive_but_overdue_strict(api_client, current, today, reason, overdue):
    base = make_car(api_client, mileage=current)
    make_log(api_client, base)

    async def read():
        return await car_reminders(await CarModel.get(base.split("/")[-1]), today)

    reminder, = api_client.portal.call(read)
    assert reminder.is_due is (reason is not None)
    assert reminder.due_reason == reason
    assert reminder.is_overdue is overdue
    assert reminder.progress_miles == pytest.approx(min(100, (current - 1000) / 5000 * 100))
    assert 0 <= reminder.progress_time <= 100


@pytest.mark.parametrize("miles,months,current,service_mileage,expected_miles,expected_time", [
    (5000, None, 3500, 1000, 50, None),
    (None, 6, 3500, 1000, None, 50),
    (5000, 6, None, 1000, None, 50),
    (5000, 6, 3500, None, None, 50),
    (5000, None, 0, 1000, 0, None),
    (5000, None, 99999, 1000, 100, None),
])
def test_progress_missing_axes_unknown_mileage_and_clamping(
    api_client, miles, months, current, service_mileage, expected_miles, expected_time,
):
    base = make_car(api_client)
    log = make_log(api_client, base, interval_miles=miles, interval_months=months)

    async def read():
        car = await CarModel.get(base.split("/")[-1])
        car.mileage = current
        car.initial_mileage = None
        record = await MaintenanceLog.get(log["_id"])
        record.mileage = service_mileage
        await record.save()
        return await car_reminders(car, date(2020, 4, 1))

    reminder, = api_client.portal.call(read)
    assert reminder.current_mileage == current
    assert reminder.progress_miles == expected_miles
    assert reminder.progress_time == expected_time
    if current is None:
        assert not reminder.is_due


def test_due_endpoint_sharing_permissions_and_inactive_owner(api_client):
    recipient = create_user(api_client, "driver")
    headers = auth_headers_for(api_client, "driver", "password123")
    base = make_car(api_client)
    due = make_log(api_client, base)
    make_log(api_client, base, work_done="Future brakes", date_of_service=date.today().isoformat(), interval_months=12)
    assert api_client.get("/reminders/due", headers=headers).json() == []
    assert api_client.post(base + "/shares/", json={"username": "driver"}).status_code == 201
    assert [r["log_id"] for r in api_client.get("/reminders/due", headers=headers).json()] == [due["_id"]]
    assert api_client.put(base + "/shares/" + recipient["_id"], json={
        "permissions": {"maintenance": "none"},
    }).status_code == 200
    assert api_client.get("/reminders/due", headers=headers).json() == []
    assert api_client.put(base + "/shares/" + recipient["_id"], json={
        "permissions": {"maintenance": "view"},
    }).status_code == 200

    async def deactivate():
        user = await User.get(FIRST_ADMIN_ID)
        await user.update({"$set": {"is_deleting": True}})

    api_client.portal.call(deactivate)
    assert api_client.get("/reminders/due", headers=headers).json() == []
    api_client.portal.call(notifications.check_due_reminders)
    assert stored_notifications(api_client) == []


def test_concurrent_scans_persist_one_event_and_read_is_user_scoped(api_client, monkeypatch, deliveries):
    assert api_client.put("/settings", json=DESTINATIONS).status_code == 200
    base = make_car(api_client)
    log = make_log(api_client, base)
    create_user(api_client, "driver")
    headers = auth_headers_for(api_client, "driver", "password123")
    original_insert = Notification.insert

    async def scan_race():
        ready = asyncio.Event()
        arrivals = 0

        async def insert(record, *args, **kwargs):
            nonlocal arrivals
            arrivals += 1
            if arrivals == 2:
                ready.set()
            await asyncio.wait_for(ready.wait(), 2)
            return await original_insert(record, *args, **kwargs)

        with monkeypatch.context() as patch:
            patch.setattr(Notification, "insert", insert)
            await asyncio.gather(notifications.check_due_reminders(), notifications.check_due_reminders())

    api_client.portal.call(scan_race)
    record, = stored_notifications(api_client)
    assert str(record.log_id) == log["_id"]
    assert record.user_id == FIRST_ADMIN_ID
    assert set(record.deliveries) == {"webhook", "discord", "email"}
    response = api_client.get("/notifications/")
    assert response.status_code == 200
    event, = response.json()
    assert not {"deliveries", "event_key", "user_id"} & event.keys()
    assert event["read"] is False
    assert api_client.get("/notifications/", headers=headers).json() == []
    read_url = "/notifications/" + event["_id"] + "/read"
    assert api_client.patch(read_url, headers=headers).status_code == 404
    assert api_client.patch(read_url).status_code == 204
    assert api_client.patch(read_url).status_code == 204
    api_client.portal.call(notifications.dispatch_notifications)
    api_client.portal.call(notifications.check_due_reminders)
    api_client.portal.call(notifications.dispatch_notifications)
    assert len(deliveries) == 3
    assert {(c, d) for c, d, _, _ in deliveries} == {
        ("webhook", DESTINATIONS["webhook_url"]),
        ("discord", DESTINATIONS["discord_webhook_url"]), ("email", DESTINATIONS["email"]),
    }
    assert all(title and message for _, _, title, message in deliveries)
    record, = stored_notifications(api_client)
    assert record.read is True
    assert all(d["status"] == "sent" and d["attempts"] == 1 for d in record.deliveries.values())
    assert api_client.get("/notifications/").json()[0]["read"] is True


def test_dispatch_concurrent_workers_claim_each_channel_once(api_client, monkeypatch, deliveries):
    assert api_client.put("/settings", json=DESTINATIONS).status_code == 200
    make_log(api_client, make_car(api_client))
    api_client.portal.call(notifications.check_due_reminders)

    async def race():
        entered = asyncio.Event()
        release = asyncio.Event()

        async def deliver(channel, destination, title, message):
            deliveries.append((channel, destination, title, message))
            entered.set()
            await asyncio.wait_for(release.wait(), 2)

        monkeypatch.setattr(notifications, "deliver", deliver)
        first = asyncio.create_task(notifications.dispatch_notifications())
        try:
            await asyncio.wait_for(entered.wait(), 2)
            second = asyncio.create_task(notifications.dispatch_notifications())
            await asyncio.sleep(0)
            release.set()
            await asyncio.gather(first, second)
        finally:
            release.set()
            if not first.done():
                first.cancel()
                await asyncio.gather(first, return_exceptions=True)

    api_client.portal.call(race)
    assert sorted(c for c, *_ in deliveries) == ["discord", "email", "webhook"]
    record, = stored_notifications(api_client)
    assert all(d["attempts"] == 1 and d["status"] == "sent" and "claim" not in d
               for d in record.deliveries.values())


def test_scan_revalidates_reminder_deleted_during_insert(api_client, monkeypatch, deliveries):
    assert api_client.put("/settings", json=DESTINATIONS).status_code == 200
    make_log(api_client, make_car(api_client))
    original_insert = Notification.insert

    async def insert(record, *args, **kwargs):
        result = await original_insert(record, *args, **kwargs)
        log = await MaintenanceLog.get(record.log_id)
        await log.delete()
        return result

    monkeypatch.setattr(Notification, "insert", insert)
    api_client.portal.call(notifications.check_due_reminders)
    api_client.portal.call(notifications.dispatch_notifications)
    assert stored_notifications(api_client) == []
    assert api_client.get("/notifications/").json() == []
    assert deliveries == []


def test_notification_lists_and_read_updates_isolate_two_owners(api_client):
    create_user(api_client, "driver")
    headers = auth_headers_for(api_client, "driver", "password123")
    own = make_log(api_client, make_car(api_client))
    other = make_log(api_client, make_car(api_client, headers), headers)
    api_client.portal.call(notifications.check_due_reminders)
    admin_event, = api_client.get("/notifications/").json()
    user_event, = api_client.get("/notifications/", headers=headers).json()
    assert admin_event["log_id"] == own["_id"]
    assert user_event["log_id"] == other["_id"]
    assert api_client.patch("/notifications/" + user_event["_id"] + "/read").status_code == 404
    assert api_client.patch("/notifications/" + user_event["_id"] + "/read", headers=headers).status_code == 204
    assert api_client.get("/notifications/").json()[0]["read"] is False
    assert api_client.get("/notifications/", headers=headers).json()[0]["read"] is True
    for limit in (0, 101):
        assert api_client.get(f"/notifications/?limit={limit}").status_code == 422
    assert len(stored_notifications(api_client)) == 2


@pytest.mark.parametrize("recover", [False, True])
def test_delivery_backoff_retry_success_and_terminal_failure(api_client, monkeypatch, recover):
    assert api_client.put("/settings", json={"webhook_url": DESTINATIONS["webhook_url"]}).status_code == 200
    make_log(api_client, make_car(api_client))
    api_client.portal.call(notifications.check_due_reminders)
    calls = []

    async def deliver(*args):
        calls.append(args)
        if not recover or len(calls) == 1:
            raise RuntimeError("simulated delivery outage")

    monkeypatch.setattr(notifications, "deliver", deliver)
    for attempt in range(1, 3 if recover else 6):
        before = datetime.now(timezone.utc).replace(tzinfo=None)
        api_client.portal.call(notifications.dispatch_notifications)
        record, = stored_notifications(api_client)
        delivery = record.deliveries["webhook"]
        expected = "sent" if recover and attempt == 2 else "failed" if attempt == 5 else "pending"
        assert delivery["status"] == expected
        assert delivery["attempts"] == attempt
        # BSON datetimes truncate sub-millisecond precision.
        assert delivery["next_at"].replace(tzinfo=None) >= before + timedelta(minutes=2 ** attempt, milliseconds=-1)
        assert "claim" not in delivery
        api_client.portal.call(notifications.dispatch_notifications)
        assert len(calls) == attempt

        async def expire():
            await Notification.get_pymongo_collection().update_one(
                {"_id": record.id}, {"$set": {"deliveries.webhook.next_at": datetime(2000, 1, 1, tzinfo=timezone.utc)}},
            )

        api_client.portal.call(expire)
    api_client.portal.call(notifications.dispatch_notifications)
    assert len(calls) == (2 if recover else 5)


def test_expired_delivery_lease_is_recovered(api_client, deliveries):
    assert api_client.put("/settings", json={"email": DESTINATIONS["email"]}).status_code == 200
    make_log(api_client, make_car(api_client))
    api_client.portal.call(notifications.check_due_reminders)

    async def abandoned_claim():
        await Notification.get_pymongo_collection().update_many({}, {"$set": {
            "deliveries.email.status": "sending", "deliveries.email.claim": "dead-worker",
            "deliveries.email.attempts": 1, "deliveries.email.next_at": datetime(2000, 1, 1, tzinfo=timezone.utc),
        }})

    api_client.portal.call(abandoned_claim)
    api_client.portal.call(notifications.dispatch_notifications)
    api_client.portal.call(notifications.dispatch_notifications)
    assert len(deliveries) == 1
    record, = stored_notifications(api_client)
    assert record.deliveries["email"]["status"] == "sent"
    assert record.deliveries["email"]["attempts"] == 2


@pytest.mark.parametrize("invalidate", ["delete", "disable", "reschedule", "supersede", "inactive_car", "inactive_owner"])
def test_invalid_reminders_suppress_events_and_sends(api_client, deliveries, invalidate):
    assert api_client.put("/settings", json=DESTINATIONS).status_code == 200
    base = make_car(api_client)
    log = make_log(api_client, base)
    api_client.portal.call(notifications.check_due_reminders)
    event, = api_client.get("/notifications/").json()
    if invalidate == "delete":
        assert api_client.delete(base + "/logs/" + log["_id"]).status_code == 204
    elif invalidate in {"disable", "reschedule"}:
        payload = ({"interval_miles": None, "interval_months": None} if invalidate == "disable"
                   else {"interval_miles": 999999, "interval_months": 1200})
        assert api_client.patch(base + "/logs/" + log["_id"], json=payload).status_code == 200
    elif invalidate == "supersede":
        make_log(api_client, base, date_of_service=date.today().isoformat(), mileage=10000)
    else:
        async def deactivate():
            record = (await CarModel.get(base.split("/")[-1]) if invalidate == "inactive_car"
                      else await User.get(FIRST_ADMIN_ID))
            await record.update({"$set": {"is_deleting": True}})

        api_client.portal.call(deactivate)
    if invalidate != "inactive_owner":
        assert api_client.get("/notifications/").json() == []
        assert api_client.patch("/notifications/" + event["_id"] + "/read").status_code == 404
    api_client.portal.call(notifications.check_due_reminders)
    api_client.portal.call(notifications.dispatch_notifications)
    assert deliveries == []
    record, = stored_notifications(api_client)
    assert all(d["status"] == "cancelled" for d in record.deliveries.values())


def test_removed_destinations_cancel_pending_deliveries(api_client, deliveries):
    assert api_client.put("/settings", json=DESTINATIONS).status_code == 200
    make_log(api_client, make_car(api_client))
    api_client.portal.call(notifications.check_due_reminders)
    assert api_client.put("/settings", json=dict.fromkeys(DESTINATIONS)).status_code == 200
    api_client.portal.call(notifications.dispatch_notifications)
    assert deliveries == []
    record, = stored_notifications(api_client)
    assert all(d["status"] == "cancelled" for d in record.deliveries.values())
    assert len(api_client.get("/notifications/").json()) == 1


def test_mileage_correction_defers_delivery_until_due_again(api_client, deliveries):
    api_client.put("/settings", json={"webhook_url": DESTINATIONS["webhook_url"]})
    base = make_car(api_client, mileage=7000)
    make_log(api_client, base, mileage=1000, interval_months=None, interval_miles=5000)
    api_client.portal.call(notifications.check_due_reminders)
    assert api_client.patch(base, json={"mileage": 2000}).status_code == 200
    api_client.portal.call(notifications.dispatch_notifications)
    assert deliveries == []
    assert stored_notifications(api_client)[0].deliveries["webhook"]["status"] == "waiting"
    assert api_client.get("/notifications/").json() == []
    assert api_client.patch(base, json={"mileage": 6000}).status_code == 200
    api_client.portal.call(notifications.check_due_reminders)
    api_client.portal.call(notifications.dispatch_notifications)
    api_client.portal.call(notifications.check_due_reminders)
    api_client.portal.call(notifications.dispatch_notifications)
    assert len(deliveries) == 1
    assert len(api_client.get("/notifications/").json()) == 1


def test_configured_mileage_reminder_survives_unknown_service_mileage(api_client):
    base = make_car(api_client)
    log = make_log(api_client, base, interval_months=None)
    assert api_client.patch(base + "/logs/" + log["_id"], json={"mileage": None}).status_code == 200
    reminder, = api_client.get(base + "/reminders/").json()
    assert reminder["interval_miles"] == 5000
    assert reminder["reminder_mileage"] is None
    assert reminder["progress_miles"] is None
    assert reminder["is_due"] is False


@pytest.mark.parametrize("target", ["car", "user"])
def test_deletion_cleans_notifications_and_user_preferences(api_client, deliveries, target):
    user = create_user(api_client, "driver")
    headers = auth_headers_for(api_client, "driver", "password123")
    assert api_client.put("/settings", headers=headers, json=DESTINATIONS).status_code == 200
    base = make_car(api_client, headers)
    make_log(api_client, base, headers)
    own = make_car(api_client)
    make_log(api_client, own)
    api_client.portal.call(notifications.check_due_reminders)
    assert len(stored_notifications(api_client)) == 2
    if target == "car":
        assert api_client.delete(base, headers=headers).status_code == 204
    else:
        assert api_client.delete("/users/" + user["_id"]).status_code == 204
    api_client.portal.call(notifications.check_due_reminders)
    api_client.portal.call(notifications.dispatch_notifications)
    assert deliveries == []
    remaining, = stored_notifications(api_client)
    assert str(remaining.car_id) == own.split("/")[-1]

    async def preferences():
        return await UserPreferences.find_one(UserPreferences.user_id == PydanticObjectId(user["_id"]))

    assert (api_client.portal.call(preferences) is None) is (target == "user")


@pytest.mark.parametrize("enabled", [False, True])
def test_lifespan_starts_and_cancels_worker(api_client, monkeypatch, enabled):
    import backend.main as main

    async def smoke():
        calls = []
        started = asyncio.Event()

        async def init():
            calls.append("init")

        async def close():
            calls.append("close")

        async def worker():
            calls.append("worker")
            started.set()
            try:
                await asyncio.Event().wait()
            finally:
                calls.append("cancelled")

        with monkeypatch.context() as patch:
            patch.setattr(settings, "reminder_worker_enabled", enabled)
            patch.setattr(main, "init_db", init)
            patch.setattr(main, "close_db", close)
            patch.setattr(main, "reminder_worker", worker)
            async with main.lifespan(main.app):
                if enabled:
                    await asyncio.wait_for(started.wait(), 2)
                else:
                    await asyncio.sleep(0)
            assert calls == (["init", "worker", "cancelled", "close"] if enabled else ["init", "close"])

    api_client.portal.call(smoke)
