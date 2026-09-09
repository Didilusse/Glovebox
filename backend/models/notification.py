from datetime import datetime, timezone

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pymongo import IndexModel


class ReminderPreferences(BaseModel):
    oil_interval_miles: int | None = Field(5000, gt=0, le=1000000, strict=True)
    oil_interval_months: int | None = Field(6, gt=0, le=1200)
    webhook_url: str | None = Field(None, max_length=2048)
    discord_webhook_url: str | None = Field(None, max_length=2048)
    email: str | None = Field(None, max_length=254)

    model_config = ConfigDict(extra="forbid")

    @field_validator("webhook_url", "discord_webhook_url")
    @classmethod
    def validate_webhook(cls, value, info):
        if value is None:
            return None
        from backend.services.notification_delivery import validate_destination
        return validate_destination(value, discord=info.field_name == "discord_webhook_url")

    @field_validator("email")
    @classmethod
    def validate_email(cls, value):
        if value is None:
            return None
        import re
        if not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}", value):
            raise ValueError("Enter a valid email address")
        return value


class UserPreferences(Document, ReminderPreferences):
    user_id: PydanticObjectId

    class Settings:
        name = "user_preferences"
        indexes = [IndexModel([("user_id", 1)], unique=True)]


class PreferencesResponse(ReminderPreferences):
    email_available: bool


class Notification(Document):
    user_id: PydanticObjectId
    car_id: PydanticObjectId
    log_id: PydanticObjectId
    event_key: str
    title: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read: bool = False
    # Destinations stay in preferences, not in notification records or responses.
    deliveries: dict = Field(default_factory=dict)

    class Settings:
        name = "notifications"
        indexes = [
            IndexModel([("event_key", 1)], unique=True),
            IndexModel([("user_id", 1), ("created_at", -1)]),
            IndexModel([("car_id", 1)]),
        ]


class NotificationResponse(BaseModel):
    id: PydanticObjectId = Field(serialization_alias="_id")
    car_id: PydanticObjectId
    log_id: PydanticObjectId
    title: str
    message: str
    created_at: datetime
    read: bool

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
