from beanie import Document, PydanticObjectId
from pydantic import Field, BaseModel
from typing import Optional
from datetime import date
from enum import Enum


class DoneBy(str, Enum):
    self_ = "self"
    shop = "shop"


class MaintenanceLog(Document):
    car_id: PydanticObjectId
    date_of_service: date
    done_by: DoneBy
    mileage: int
    cost: float
    notes: str

    class Settings:
        name = "maintenance_logs"


class MaintenanceLogCreate(BaseModel):
    date_of_service: date = Field(default_factory=date.today, description="The date the maintenance was performed")
    done_by: DoneBy = Field(..., description="Who performed the work: self or shop")
    mileage: int = Field(..., description="Odometer reading at the time of service")
    cost: float = Field(..., description="The cost of the service")
    notes: str = Field(..., description="What work was done")


class MaintenanceLogUpdate(BaseModel):
    date_of_service: Optional[date] = Field(None, description="The date the maintenance was performed")
    done_by: Optional[DoneBy] = Field(None, description="Who performed the work: self or shop")
    mileage: Optional[int] = Field(None, description="Odometer reading at the time of service")
    cost: Optional[float] = Field(None, description="The cost of the service")
    notes: Optional[str] = Field(None, description="What work was done")
