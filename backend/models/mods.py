from beanie import Document, PydanticObjectId
from pydantic import Field
from enum import Enum
from typing import Optional

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
    fluids = "fluids" # Added this as it's useful for maintenance!

class Status(str, Enum):
    planned = "planned"
    purchased = "purchased"
    installed = "installed"

class ModItem(Document):
    car_id: PydanticObjectId
    name: str = Field(..., description="The name of the item")
    type: ModType = Field(..., description="The type of item: maintenance or modification")
    category: Category = Field(..., description="The category of the item")
    cost: float = Field(0.0, description="The cost of the item") # Defaulted to 0.0 to prevent errors on free items
    status: Status = Field(default=Status.planned, description="The current status of the item")
    url: Optional[str] = Field(None, description="A URL for more information about the item")
    brand: Optional[str] = Field(None, description="The brand of the part used in the item")
    notes: Optional[str] = Field(None, description="Additional notes about the item")

    class Settings:
        name = "mods" 