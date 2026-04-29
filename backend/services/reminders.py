from datetime import date
from typing import Optional, Tuple

from dateutil.relativedelta import relativedelta


def calculate_next_reminder(
    date_of_service: date,
    mileage: int,
    interval_months: int | None,
    interval_miles: int | None,
) -> tuple[Optional[date], Optional[int]]:
    reminder_date = (
        date_of_service + relativedelta(months=interval_months)
        if interval_months is not None
        else None
    )
    reminder_mileage = mileage + interval_miles if interval_miles is not None else None
    return reminder_date, reminder_mileage


def determine_due_reason(
    reminder_date: Optional[date],
    reminder_mileage: Optional[int],
    current_date: date,
    current_mileage: Optional[int],
) -> tuple[bool, Optional[str]]:
    due_date = reminder_date is not None and current_date >= reminder_date
    due_mileage = (
        reminder_mileage is not None
        and current_mileage is not None
        and current_mileage >= reminder_mileage
    )

    if due_date and due_mileage:
        return True, "both"
    if due_date:
        return True, "date"
    if due_mileage:
        return True, "mileage"
    return False, None


def reminder_sort_key(
    reminder_date: Optional[date],
    reminder_mileage: Optional[int],
) -> tuple[int, str]:
    if reminder_date is not None:
        return (0, reminder_date.isoformat())
    if reminder_mileage is not None:
        return (1, f"{reminder_mileage:020d}")
    return (2, "")