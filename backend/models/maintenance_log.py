from beanie import Document, PydanticObjectId
from pymongo import IndexModel
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional
from datetime import date
from enum import Enum

class DoneBy(str, Enum):
    self_ = "self"
    shop = "shop"

class Category(str, Enum):
    engine = "engine"
    suspension = "suspension"
    exterior = "exterior"
    interior = "interior"
    wheels = "wheels"
    brakes = "brakes"
    exhaust = "exhaust"
    fluids = "fluids" 
    other = "other"

class MaintenanceLog(Document):
    car_id: PydanticObjectId
    date_of_service: date
    done_by: DoneBy = DoneBy.shop
    mileage: Optional[int] = None
    cost: Optional[float] = None
    work_done: str = "Maintenance"
    category: Category = Category.other
    notes: Optional[str] = None
    interval_miles: int | None = None
    interval_months: int | None = None
    reminder_date: Optional[date] = Field(
        None,
        description="The calculated date when the next maintenance reminder should be sent."
    )
    reminder_mileage: Optional[int] = Field(
        None,
        description="The calculated mileage when the next maintenance reminder should be sent."
    )
    source: Optional[str] = None
    source_record_key: Optional[str] = None
    service_provider: Optional[str] = None

    @field_validator("category", mode="before")
    def _normalize_category_doc(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return v.lower()
        return v


    class Settings:
        name = "maintenance_logs"
        indexes = [
            [("car_id", 1), ("date_of_service", -1)],
            [("car_id", 1), ("cost", 1)],
            IndexModel(
                [("car_id", 1), ("source", 1), ("source_record_key", 1)],
                unique=True,
                partialFilterExpression={"source_record_key": {"$type": "string"}},
            ),
        ]


class MaintenanceLogCreate(BaseModel):
    date_of_service: date = Field(default_factory=date.today, description="The date the maintenance was performed")
    done_by: DoneBy = Field(..., description="Who performed the work: self or shop")
    mileage: int = Field(..., ge=0, description="Odometer reading at the time of service")
    cost: float = Field(..., ge=0, allow_inf_nan=False, description="The cost of the service")
    work_done: str = Field(..., min_length=1, max_length=500, description="What work was done")
    category: Category = Field(Category.other, description="Category of the maintenance")
    notes: Optional[str] = Field(None, max_length=5000, description="Additional details like parts or products used")
    interval_miles: int | None = Field(None, gt=0)
    interval_months: int | None = Field(None, gt=0, le=1200)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    
    @field_validator("category", mode="before")
    def _normalize_category(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return v.lower()
        return v


class MaintenanceLogUpdate(BaseModel):
    date_of_service: Optional[date] = Field(None, description="The date the maintenance was performed")
    done_by: Optional[DoneBy] = Field(None, description="Who performed the work: self or shop")
    mileage: Optional[int] = Field(None, ge=0, description="Odometer reading at the time of service")
    cost: Optional[float] = Field(None, ge=0, allow_inf_nan=False, description="The cost of the service")
    work_done: Optional[str] = Field(None, min_length=1, max_length=500, description="What work was done")
    category: Optional[Category] = Field(None, description="Category of the maintenance")
    interval_miles: Optional[int] = Field(None, gt=0, description="Interval in miles for next reminder")
    interval_months: Optional[int] = Field(None, gt=0, le=1200, description="Interval in months for next reminder")
    notes: Optional[str] = Field(None, max_length=5000, description="Additional details like parts or products used")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="after")
    def reject_null_for_required_fields(self):
        required_fields = {"date_of_service", "done_by", "work_done", "category"}
        null_fields = [
            name for name in self.model_fields_set
            if name in required_fields and getattr(self, name) is None
        ]
        if null_fields:
            raise ValueError(f"Fields cannot be null: {', '.join(sorted(null_fields))}")
        return self

    @field_validator("category", mode="before")
    def _normalize_category_update(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            return v.lower()
        return v


class MaintenanceReminder(BaseModel):
    log_id: PydanticObjectId
    car_id: PydanticObjectId
    date_of_service: date
    mileage: Optional[int] = None
    work_done: str
    reminder_date: Optional[date] = None
    reminder_mileage: Optional[int] = None
    current_mileage: Optional[int] = None
    is_due: bool = False
    due_reason: Optional[str] = None
    interval_miles: Optional[int] = None
    interval_months: Optional[int] = None
    is_overdue: bool = False
    progress_miles: Optional[float] = None
    progress_time: Optional[float] = None
    car_name: Optional[str] = None
