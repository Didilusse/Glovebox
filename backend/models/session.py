from datetime import datetime, timedelta, timezone

from pydantic import Field
from beanie import Document, Indexed, PydanticObjectId
from pymongo import ASCENDING, IndexModel


class AuthSession(Document):
    token_hash: Indexed(str, unique=True)
    user_id: PydanticObjectId
    credential_version: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime

    class Settings:
        name = "sessions"
        indexes = [
            IndexModel([("expires_at", ASCENDING)], name="session_expiry", expireAfterSeconds=0),
            IndexModel([("token_hash", ASCENDING)], name="unique_token_hash", unique=True),
            IndexModel([("user_id", ASCENDING)], name="session_user"),
        ]

    def is_expired(self) -> bool:
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at <= datetime.now(timezone.utc)

    @staticmethod
    def new_expiry(ttl_days: int) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=ttl_days)
