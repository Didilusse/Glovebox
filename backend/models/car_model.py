from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional
from datetime import date
from enum import Enum
from beanie import Document, PydanticObjectId
from pymongo import ASCENDING, IndexModel
from backend.models.car_share import CarAccess


MAX_VEHICLE_YEAR = date.today().year + 1


class FuelType(str, Enum):
    gas = "gas"
    diesel = "diesel"
    electric = "electric"


class CarFields(BaseModel):
    make: str = Field(min_length=1, max_length=100, description="The company that made the car")
    model: str = Field(min_length=1, max_length=100, description="The model name")
    year: int = Field(ge=1886, le=MAX_VEHICLE_YEAR, description="What year the car was made")
    mileage: Optional[int] = Field(None, ge=0, description="Current mileage of the vehicle")
    initial_mileage: Optional[int] = Field(None, ge=0, description="Odometer reading when the car was added")
    vin: Optional[str] = Field(None, min_length=1, max_length=17, description="Vehicle Identification Number")
    license_plate: Optional[str] = Field(None, min_length=1, max_length=20, description="License plate number")
    fuel_type: Optional[FuelType] = Field(None, description="Fuel type: gas, diesel, or electric")
    purchased_date: Optional[date] = Field(None, description="Date the vehicle was purchased")
    purchased_price: Optional[float] = Field(None, ge=0, allow_inf_nan=False, description="Price paid for the vehicle")

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @field_validator("purchased_date")
    @classmethod
    def validate_purchased_date(cls, value: date | None) -> date | None:
        if value is not None and value > date.today():
            raise ValueError("purchased_date cannot be in the future")
        return value


class CarCreate(CarFields):
    pass


class CarUpdate(BaseModel):
    make: Optional[str] = Field(None, min_length=1, max_length=100)
    model: Optional[str] = Field(None, min_length=1, max_length=100)
    year: Optional[int] = Field(None, ge=1886, le=MAX_VEHICLE_YEAR)
    mileage: Optional[int] = Field(None, ge=0)
    initial_mileage: Optional[int] = Field(None, ge=0)
    vin: Optional[str] = Field(None, min_length=1, max_length=17)
    license_plate: Optional[str] = Field(None, min_length=1, max_length=20)
    fuel_type: Optional[FuelType] = None
    purchased_date: Optional[date] = None
    purchased_price: Optional[float] = Field(None, ge=0, allow_inf_nan=False)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    @model_validator(mode="after")
    def reject_null_values(self):
        null_fields = [name for name in self.model_fields_set if getattr(self, name) is None]
        if null_fields:
            raise ValueError(f"Fields cannot be null: {', '.join(sorted(null_fields))}")
        if self.purchased_date is not None and self.purchased_date > date.today():
            raise ValueError("purchased_date cannot be in the future")
        return self


class CarModel(Document, CarFields):
    is_deleting: bool = False
    owner_id: Optional[PydanticObjectId] = None

    class Settings:
        name = "cars"
        indexes = [IndexModel([("owner_id", ASCENDING), ("_id", ASCENDING)], name="car_owner")]


class CarResponse(CarFields):
    id: PydanticObjectId = Field(serialization_alias="_id")
    access: CarAccess

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
