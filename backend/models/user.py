import re
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field, field_validator
from beanie import Document, Indexed, PydanticObjectId
from pymongo import ASCENDING, IndexModel

USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_.-]{2,29}$")
FIRST_ADMIN_ID = PydanticObjectId("000000000000000000000001")


class User(Document):
    username: Indexed(str, unique=True)
    password_hash: str
    is_admin: bool = False
    is_deleting: bool = False
    credential_version: int = 0
    legacy_claim_complete: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "users"
        indexes = [
            IndexModel([("username", ASCENDING)], name="unique_username", unique=True)
        ]

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not USERNAME_PATTERN.match(normalized):
            raise ValueError(
                "Username must be 3-30 characters using letters, numbers, dots, dashes, or underscores"
            )
        return normalized


class UserResponse(BaseModel):
    id: PydanticObjectId = Field(serialization_alias="_id")
    username: str
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=4, max_length=128)

    model_config = ConfigDict(extra="forbid")

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not USERNAME_PATTERN.match(normalized):
            raise ValueError(
                "Username must be 3-30 characters using letters, numbers, dots, dashes, or underscores"
            )
        return normalized


class PasswordReset(BaseModel):
    new_password: str = Field(min_length=4, max_length=128)

    model_config = ConfigDict(extra="forbid")


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=4, max_length=128)

    model_config = ConfigDict(extra="forbid")


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=128)

    model_config = ConfigDict(extra="forbid")


class SetupRequest(UserCreate):
    pass


class AuthResponse(BaseModel):
    token: str
    user: UserResponse
