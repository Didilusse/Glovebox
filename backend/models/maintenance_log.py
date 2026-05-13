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
    done_by: DoneBy = DoneBy.shop
    mileage: int
    cost: float
    work_done: str = "Maintenance"
    notes: Optional[str] = None
    interval_miles: int | None = 5000
    interval_months: int | None = 6
    reminder_date: Optional[date] = Field(
        None,
        description="The calculated date when the next maintenance reminder should be sent."
    )
    reminder_mileage: Optional[int] = Field(
        None,
        description="The calculated mileage when the next maintenance reminder should be sent."
    )


    class Settings:
        name = "maintenance_logs"


class MaintenanceLogCreate(BaseModel):
    date_of_service: date = Field(default_factory=date.today, description="The date the maintenance was performed")
    done_by: DoneBy = Field(..., description="Who performed the work: self or shop")
    mileage: int = Field(..., description="Odometer reading at the time of service")
    cost: float = Field(..., description="The cost of the service")
    work_done: str = Field(..., description="What work was done")
    notes: Optional[str] = Field(None, description="Additional details like parts or products used")
    interval_miles: int | None = 5000
    interval_months: int | None = 6


class MaintenanceLogUpdate(BaseModel):
    date_of_service: Optional[date] = Field(None, description="The date the maintenance was performed")
    done_by: Optional[DoneBy] = Field(None, description="Who performed the work: self or shop")
    mileage: Optional[int] = Field(None, description="Odometer reading at the time of service")
    cost: Optional[float] = Field(None, description="The cost of the service")
    work_done: Optional[str] = Field(None, description="What work was done")
    notes: Optional[str] = Field(None, description="Additional details like parts or products used")


class MaintenanceReminder(BaseModel):
    log_id: PydanticObjectId
    car_id: PydanticObjectId
    date_of_service: date
    mileage: int
    work_done: str
    reminder_date: Optional[date] = None
    reminder_mileage: Optional[int] = None
    current_mileage: Optional[int] = None
    is_due: bool = False
    due_reason: Optional[str] = None
