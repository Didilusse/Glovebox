from beanie import Document, PydanticObjectId
from pydantic import ConfigDict, Field, BaseModel
from typing import Optional
from datetime import date
from backend.models.parts import Parts

class MaintenanceLog(Document):
    car_id: PydanticObjectId
    date_of_service: date
    description: str
    category: str
    cost: float
    mileage: int
    parts: list[Parts] = Field(default_factory=list)
    class Settings:
        name = "maintenance_logs"

class MaintenanceLogCreate(BaseModel):
    date_of_service: date = Field(..., description="The date the maintenance was performed")
    description: str = Field(..., description="A description of the maintenance performed")
    category: str = Field(..., description="The category of the maintenance performed")
    cost: float = Field(0, description="The cost of the maintenance performed")
    mileage: int = Field(..., description="The mileage of the vehicle at the time of maintenance")
    parts: list[Parts] = Field(default_factory=list)

class MaintenanceLogUpdate(BaseModel):
    date_of_service: date | None = Field(None, description="The date the maintenance was performed")
    description: str | None = Field(None, description="A description of the maintenance performed")
    category: str | None = Field(None, description="The category of the maintenance performed")
    cost: float | None = Field(None, description="The cost of the maintenance performed")
    mileage: int | None = Field(None, description="The mileage of the vehicle at the time of maintenance")
    parts: list[Parts] = Field(default_factory=list)
