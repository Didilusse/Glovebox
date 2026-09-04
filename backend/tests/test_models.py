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

    imported_update = MaintenanceLogUpdate(mileage=None, cost=None)
    assert imported_update.model_dump(exclude_unset=True) == {"mileage": None, "cost": None}

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


def test_mod_schema_defaults_clearable_fields_and_forbids_unknown_fields():
    created = ModItemCreate(
        name="  Brake kit  ",
        type="modification",
        category="brakes",
        part_number="  BBK-100  ",
        target_date="2026-10-15",
    )
    assert created.priority.value == "medium"
    assert created.install_method.value == "undecided"
    assert created.part_number == "BBK-100"
    assert created.target_date == date(2026, 10, 15)

    omitted_update = ModItemUpdate()
    assert omitted_update.priority.value == "medium"
    assert omitted_update.install_method.value == "undecided"
    assert omitted_update.model_dump(exclude_unset=True) == {}

    update = ModItemUpdate(part_number=None, target_date=None)
    assert update.model_dump(exclude_unset=True) == {
        "part_number": None,
        "target_date": None,
    }

    for field in ("priority", "install_method"):
        with pytest.raises(ValidationError):
            ModItemUpdate(**{field: None})

    with pytest.raises(ValidationError):
        ModItemCreate(
            name="Part",
            type="modification",
            category="engine",
            unknown="value",
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("priority", "urgent"),
        ("install_method", "dealer"),
        ("part_number", "   "),
        ("part_number", "X" * 101),
        ("target_date", "not-a-date"),
    ],
)
def test_mod_schema_rejects_invalid_planning_fields(field, value):
    with pytest.raises(ValidationError):
        ModItemCreate(
            name="Part",
            type="modification",
            category="engine",
            **{field: value},
        )
