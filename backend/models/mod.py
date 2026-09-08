from datetime import date
from enum import Enum
from typing import Annotated, Optional

from beanie import Document, PydanticObjectId
from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, field_validator, model_validator


PartNumber = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=100),
]

class ModType(str, Enum):
    maintenance = "maintenance"
    modification = "modification"

class Category(str, Enum):
    engine = "engine"
    suspension = "suspension"
    exterior = "exterior"
    interior = "interior"
    wheels = "wheels"
    brakes = "brakes"
    exhaust = "exhaust"
    fluids = "fluids" 

class Status(str, Enum):
    planned = "planned"
    purchased = "purchased"
    installed = "installed"

class Priority(str, Enum):
    high = "high"
    medium = "medium"
    low = "low"

class InstallMethod(str, Enum):
    diy = "diy"
    shop = "shop"
    undecided = "undecided"

class ModItem(Document):
    car_id: PydanticObjectId
    name: str = Field(..., description="The name of the item")
    type: ModType = Field(..., description="The type of item: maintenance or modification")
    category: Category = Field(..., description="The category of the item")
    cost: float = Field(0.0, description="The cost of the item") 
    status: Status = Field(default=Status.planned, description="The current status of the item")
    position: int = Field(default=0, ge=0, description="The zero-based position within the status")
    priority: Priority = Field(default=Priority.medium, description="The item's priority")
    install_method: InstallMethod = Field(default=InstallMethod.undecided, description="How the item will be installed")
    part_number: Optional[PartNumber] = Field(None, description="The part number")
    target_date: Optional[date] = Field(None, description="The target completion date")
    url: Optional[str] = Field(None, description="A URL for more information about the item")
    brand: Optional[str] = Field(None, description="The brand of the part used in the item")
    notes: Optional[str] = Field(None, description="Additional notes about the item")

    class Settings:
        name = "mods"
        indexes = ["car_id"]

class ModItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    type: ModType
    category: Category
    cost: float = Field(0.0, ge=0, allow_inf_nan=False)
    status: Status = Status.planned
    priority: Priority = Field(default=Priority.medium, description="The item's priority")
    install_method: InstallMethod = Field(default=InstallMethod.undecided, description="How the item will be installed")
    part_number: Optional[PartNumber] = Field(None, description="The part number")
    target_date: Optional[date] = Field(None, description="The target completion date")
    url: Optional[HttpUrl] = None
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=5000)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("url")
    @classmethod
    def require_https_url(cls, value):
        if value is not None and value.scheme != "https":
            raise ValueError("Product links must use HTTPS")
        return value

class ModItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[ModType] = None
    category: Optional[Category] = None
    cost: Optional[float] = Field(None, ge=0, allow_inf_nan=False)
    status: Optional[Status] = None
    priority: Optional[Priority] = Field(
        default=Priority.medium,
        description="The item's priority",
    )
    install_method: Optional[InstallMethod] = Field(
        default=InstallMethod.undecided,
        description="How the item will be installed",
    )
    part_number: Optional[PartNumber] = Field(None, description="The part number")
    target_date: Optional[date] = Field(None, description="The target completion date")
    url: Optional[HttpUrl] = None
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=5000)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("url")
    @classmethod
    def require_https_url(cls, value):
        if value is not None and value.scheme != "https":
            raise ValueError("Product links must use HTTPS")
        return value

    @model_validator(mode="after")
    def reject_null_for_required_fields(self):
        required_fields = {
            "name", "type", "category", "cost", "status", "priority", "install_method"
        }
        null_fields = [
            name for name in self.model_fields_set
            if name in required_fields and getattr(self, name) is None
        ]
        if null_fields:
            raise ValueError(f"Fields cannot be null: {', '.join(sorted(null_fields))}")
        return self


class ModItemMove(BaseModel):
    status: Status
    position: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")
