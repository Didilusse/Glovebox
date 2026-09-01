from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from backend.models.car_model import CarCreate, CarUpdate
from backend.models.maintenance_log import MaintenanceLogCreate, MaintenanceLogUpdate
from backend.models.mod import ModItemCreate, ModItemUpdate


def test_car_schema_rejects_unknown_and_invalid_values():
    with pytest.raises(ValidationError):
        CarCreate(make="A", model="B", year=2020, licensePlate="ABC")

    with pytest.raises(ValidationError):
        CarCreate(make="A", model="B", year=2020, mileage=-1)

    with pytest.raises(ValidationError):
        CarUpdate(mileage=None)

    with pytest.raises(ValidationError):
        CarCreate(
            make="A",
            model="B",
            year=2020,
            purchased_date=date.today() + timedelta(days=1),
        )


def test_maintenance_schema_distinguishes_clearing_from_required_nulls():
    update = MaintenanceLogUpdate(notes=None, interval_miles=None)
    assert update.model_dump(exclude_unset=True) == {"notes": None, "interval_miles": None}

    with pytest.raises(ValidationError):
        MaintenanceLogUpdate(mileage=None)

    with pytest.raises(ValidationError):
        MaintenanceLogCreate(
            done_by="shop",
            mileage=10,
            cost=-1,
            work_done="Oil change",
        )


def test_mod_schema_validates_cost_url_and_required_nulls():
    with pytest.raises(ValidationError):
        ModItemCreate(
            name="Part",
            type="modification",
            category="engine",
            cost=-1,
        )

    with pytest.raises(ValidationError):
        ModItemCreate(
            name="Part",
            type="modification",
            category="engine",
            url="not-a-url",
        )

    with pytest.raises(ValidationError):
        ModItemUpdate(status=None)
