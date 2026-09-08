from typing import Literal

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, field_validator
from pymongo import ASCENDING, IndexModel

from backend.models.user import UserCreate


class SharePermissions(BaseModel):
    vehicle: Literal["view", "edit"] = "view"
    maintenance: Literal["none", "view", "edit"] = "view"
    mods: Literal["none", "view", "edit"] = "view"

    model_config = ConfigDict(extra="forbid")


class ShareUpdate(BaseModel):
    permissions: SharePermissions

    model_config = ConfigDict(extra="forbid")


class ShareCreate(ShareUpdate):
    username: str
    permissions: SharePermissions = Field(default_factory=SharePermissions)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return UserCreate.validate_username(value)


class CarShare(Document):
    car_id: PydanticObjectId
    user_id: PydanticObjectId
    permissions: SharePermissions = Field(default_factory=SharePermissions)

    class Settings:
        name = "car_shares"
        indexes = [
            IndexModel([("car_id", ASCENDING), ("user_id", ASCENDING)], unique=True, name="unique_car_recipient"),
            IndexModel([("user_id", ASCENDING)], name="share_recipient"),
        ]


class ShareResponse(BaseModel):
    id: PydanticObjectId = Field(serialization_alias="_id")
    user_id: PydanticObjectId
    username: str
    permissions: SharePermissions


class CarAccess(BaseModel):
    is_owner: bool
    owner_username: str
    permissions: SharePermissions
