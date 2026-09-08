import asyncio
import hashlib
import logging
import secrets
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from backend.config import settings
from backend.models.car_model import CarModel
from backend.models.notification import Notification, UserPreferences
from backend.models.user import User
from backend.services.notification_delivery import deliver
from backend.services.reminders import car_reminders
from backend.services.quotas import QuotaExceeded, claim_quota, release_quota

logger = logging.getLogger(__name__)
CHANNEL_FIELDS = {"webhook": "webhook_url", "discord": "discord_webhook_url", "email": "email"}


def event_key(user_id, reminder):
    values = (user_id, reminder.car_id, reminder.log_id, reminder.date_of_service,
              reminder.mileage, reminder.reminder_date, reminder.reminder_mileage)
    return hashlib.sha256("|".join(map(str, values)).encode()).hexdigest()


async def notification_reminder(notification):
    car = await CarModel.get(notification.car_id)
    user = await User.get(notification.user_id)
    if not car or car.is_deleting or car.owner_id != notification.user_id or not user or user.is_deleting:
        return None
    return next((r for r in await car_reminders(car) if event_key(user.id, r) == notification.event_key), None)


async def current_notification(notification):
    reminder = await notification_reminder(notification)
    return reminder is not None and reminder.is_due


async def check_due_reminders():
    """Persist a single event per deadline; MongoDB claims coordinate all app workers."""
    async for car in CarModel.find({"is_deleting": {"$ne": True}, "owner_id": {"$ne": None}}):
        user = await User.get(car.owner_id)
        if not user or user.is_deleting:
            continue
        preferences = await UserPreferences.find_one(UserPreferences.user_id == user.id)
        for reminder in await car_reminders(car):
            if not reminder.is_due:
                continue
            key = event_key(user.id, reminder)
            existing = await Notification.find_one(Notification.event_key == key)
            if existing:
                for channel in CHANNEL_FIELDS:
                    prefix = f"deliveries.{channel}"
                    await Notification.get_pymongo_collection().update_one(
                        {"_id": existing.id, f"{prefix}.status": "waiting",
                         f"{prefix}.attempts": {"$lt": settings.notification_max_delivery_attempts}},
                        {"$set": {f"{prefix}.status": "pending", f"{prefix}.next_at": datetime.now(timezone.utc)}},
                    )
                continue
            now = datetime.now(timezone.utc)
            deadlines = []
            if reminder.reminder_date:
                deadlines.append(f"date {reminder.reminder_date}")
            if reminder.reminder_mileage is not None:
                deadlines.append(f"odometer {reminder.reminder_mileage:,} miles")
            notification = Notification(
                id=PydanticObjectId(),
                user_id=user.id, car_id=car.id, log_id=reminder.log_id, event_key=key,
                title=f"Maintenance due: {reminder.work_done}",
                message=f"{reminder.car_name}: {reminder.work_done} is due. Scheduled for {' or '.join(deadlines)}.",
                deliveries={channel: {"status": "pending", "attempts": 0, "next_at": now}
                            for channel, field in CHANNEL_FIELDS.items()
                            if preferences and getattr(preferences, field)},
            )
            try:
                await claim_quota(
                    "notifications", user.id, notification.id, settings.max_notifications_per_user,
                    Notification.get_pymongo_collection(), {"user_id": user.id}, car_id=str(car.id),
                )
            except QuotaExceeded:
                continue
            try:
                await notification.insert()
            except DuplicateKeyError:
                await release_quota("notifications", notification.id)
                continue
            except Exception:
                await release_quota("notifications", notification.id)
                raise
            if not await current_notification(notification):
                await notification.delete()
                await release_quota("notifications", notification.id)


async def dispatch_notifications():
    collection = Notification.get_pymongo_collection()
    # Bounded batches leave time for deadline scans and prevent an outage backlog
    # from monopolizing the worker. Claims expire after interrupted deliveries.
    for channel, field in CHANNEL_FIELDS.items():
        prefix = f"deliveries.{channel}"
        for _ in range(settings.notification_dispatch_batch):
            now = datetime.now(timezone.utc)
            claim = secrets.token_hex(16)
            document = await collection.find_one_and_update(
                {f"{prefix}.status": {"$in": ["pending", "sending"]},
                 f"{prefix}.next_at": {"$lte": now},
                 f"{prefix}.attempts": {"$lt": settings.notification_max_delivery_attempts}},
                {"$set": {f"{prefix}.status": "sending", f"{prefix}.claim": claim,
                          f"{prefix}.next_at": now + timedelta(minutes=2)},
                 "$inc": {f"{prefix}.attempts": 1}},
                return_document=True,
            )
            if not document:
                break
            notification = Notification.model_validate(document)
            attempts = notification.deliveries[channel]["attempts"]
            status = "cancelled"
            preferences = await UserPreferences.find_one(UserPreferences.user_id == notification.user_id)
            destination = getattr(preferences, field) if preferences else None
            reminder = await notification_reminder(notification) if destination else None
            if reminder and not reminder.is_due:
                status = "waiting"
            if reminder and reminder.is_due:
                lease = asyncio.create_task(renew_delivery_claim(notification.id, prefix, claim))
                try:
                    await deliver(channel, destination, notification.title, notification.message)
                    status = "sent"
                except Exception:
                    status = ("failed" if attempts >= settings.notification_max_delivery_attempts
                              else "pending")
                    logger.warning("Reminder delivery unsuccessful: channel=%s attempt=%s", channel, attempts)
                finally:
                    lease.cancel()
                    with suppress(asyncio.CancelledError):
                        await lease
            await collection.update_one(
                {"_id": notification.id, f"{prefix}.claim": claim},
                {"$set": {f"{prefix}.status": status,
                          f"{prefix}.next_at": datetime.now(timezone.utc) + timedelta(minutes=min(60, 2 ** attempts))},
                 "$unset": {f"{prefix}.claim": ""}},
            )


async def renew_delivery_claim(notification_id, prefix, claim):
    while True:
        await asyncio.sleep(30)
        try:
            await Notification.get_pymongo_collection().update_one(
                {"_id": notification_id, f"{prefix}.claim": claim},
                {"$set": {f"{prefix}.next_at": datetime.now(timezone.utc) + timedelta(minutes=2)}},
            )
        except Exception:
            logger.error("Could not renew reminder delivery claim")


async def run_periodically(operation):
    while True:
        try:
            await operation()
        except Exception:
            # Do not include request URLs, SMTP credentials, or destination addresses.
            logger.error("Reminder check failed; will retry on the next interval")
        await asyncio.sleep(settings.reminder_check_seconds)


async def reminder_worker():
    # Slow endpoints cannot delay the discovery of due reminders and in-app alerts.
    async with asyncio.TaskGroup() as tasks:
        tasks.create_task(run_periodically(check_due_reminders))
        tasks.create_task(run_periodically(dispatch_notifications))
