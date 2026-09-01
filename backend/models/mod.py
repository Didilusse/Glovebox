from beanie import Document, PydanticObjectId
from pydantic import ConfigDict, Field, HttpUrl, model_validator
from enum import Enum
from typing import Optional
from pydantic import BaseModel

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

class ModItem(Document):
    car_id: PydanticObjectId
    name: str = Field(..., description="The name of the item")
    type: ModType = Field(..., description="The type of item: maintenance or modification")
    category: Category = Field(..., description="The category of the item")
    cost: float = Field(0.0, description="The cost of the item") 
    status: Status = Field(default=Status.planned, description="The current status of the item")
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
    url: Optional[HttpUrl] = None
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=5000)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

class ModItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    type: Optional[ModType] = None
    category: Optional[Category] = None
    cost: Optional[float] = Field(None, ge=0, allow_inf_nan=False)
    status: Optional[Status] = None
    url: Optional[HttpUrl] = None
    brand: Optional[str] = Field(None, min_length=1, max_length=100)
    notes: Optional[str] = Field(None, max_length=5000)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="after")
    def reject_null_for_required_fields(self):
        required_fields = {"name", "type", "category", "cost", "status"}
        null_fields = [
            name for name in self.model_fields_set
            if name in required_fields and getattr(self, name) is None
        ]
        if null_fields:
            raise ValueError(f"Fields cannot be null: {', '.join(sorted(null_fields))}")
        return self
