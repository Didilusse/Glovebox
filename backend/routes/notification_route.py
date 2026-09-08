from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query

from backend.auth import get_current_user
from backend.config import settings
from backend.models.car_model import CarModel
from backend.models.car_share import CarShare
from backend.models.notification import Notification, NotificationResponse, PreferencesResponse, ReminderPreferences, UserPreferences
from backend.models.maintenance_log import MaintenanceReminder
from backend.models.user import User
from backend.services.reminders import car_reminders
from backend.services.notifications import current_notification

router = APIRouter(tags=["Settings and notifications"])


def preferences_response(preferences):
    return PreferencesResponse(
        **ReminderPreferences.model_validate(preferences.model_dump(include=set(ReminderPreferences.model_fields))).model_dump(),
        email_available=bool(settings.smtp_host and settings.smtp_from),
    )


@router.get("/settings", response_model=PreferencesResponse)
async def get_settings(user: User = Depends(get_current_user)):
    preferences = await UserPreferences.find_one(UserPreferences.user_id == user.id)
    return preferences_response(preferences or ReminderPreferences())


@router.put("/settings", response_model=PreferencesResponse)
async def save_settings(payload: ReminderPreferences, user: User = Depends(get_current_user)):
    await UserPreferences.get_pymongo_collection().update_one(
        {"user_id": user.id}, {"$set": payload.model_dump()}, upsert=True,
    )
    current = await User.get(user.id)
    if not current or current.is_deleting:
        await UserPreferences.find(UserPreferences.user_id == user.id).delete()
        raise HTTPException(401, "Account unavailable")
    return preferences_response(payload)


@router.get("/reminders/due", response_model=list[MaintenanceReminder])
async def due_reminders(user: User = Depends(get_current_user)):
    shares = await CarShare.find({"user_id": user.id, "permissions.maintenance": {"$in": ["view", "edit"]}}).to_list()
    cars = CarModel.find({"is_deleting": {"$ne": True}, "$or": [
        {"owner_id": user.id}, {"_id": {"$in": [share.car_id for share in shares]}}
    ]})
    result = []
    async for car in cars:
        owner = await User.get(car.owner_id) if car.owner_id else None
        if not owner or owner.is_deleting:
            continue
        result.extend(reminder for reminder in await car_reminders(car) if reminder.is_due)
    return result


@router.get("/notifications/", response_model=list[NotificationResponse])
async def notifications(user: User = Depends(get_current_user), limit: int = Query(100, ge=1, le=100)):
    result = []
    query = Notification.find(Notification.user_id == user.id).sort(
        -Notification.created_at
    ).limit(settings.max_notifications_per_user)
    async for notification in query:
        if await current_notification(notification):
            result.append(notification)
        if len(result) >= limit:
            break
    return result


@router.patch("/notifications/{notification_id}/read", status_code=204)
async def mark_read(notification_id: PydanticObjectId, user: User = Depends(get_current_user)):
    notification = await Notification.find_one({"_id": notification_id, "user_id": user.id})
    if not notification or not await current_notification(notification):
        raise HTTPException(404, "Notification not found")
    await notification.update({"$set": {"read": True}})
