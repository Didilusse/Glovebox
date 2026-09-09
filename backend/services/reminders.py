from datetime import date
from typing import Optional, Tuple
import re

from dateutil.relativedelta import relativedelta
from backend.config import settings


def is_oil_change(work_done: str) -> bool:
    return bool(re.search(r"\boil\b", work_done, re.I) and re.search(r"\bchang(?:e|ed|ing)\b", work_done, re.I))


async def car_reminders(car, today: date | None = None):
    from backend.models.maintenance_log import MaintenanceLog, MaintenanceReminder
    today = today or date.today()
    logs = await MaintenanceLog.find(MaintenanceLog.car_id == car.id).sort(
        -MaintenanceLog.date_of_service, -MaintenanceLog.id
    ).limit(settings.max_maintenance_logs_per_car).to_list()
    current_mileage = car.mileage if car.mileage is not None else car.initial_mileage
    reminders = []
    seen_oil_change = False
    for log in logs:
        if is_oil_change(log.work_done):
            if seen_oil_change:
                continue
            seen_oil_change = True
        if all(value is None for value in (log.reminder_date, log.reminder_mileage, log.interval_months, log.interval_miles)):
            continue
        is_due, reason = determine_due_reason(log.reminder_date, log.reminder_mileage, today, current_mileage)
        mileage_progress = None
        if log.reminder_mileage is not None and log.mileage is not None and current_mileage is not None:
            distance = log.reminder_mileage - log.mileage
            if distance > 0:
                mileage_progress = min(100, max(0, (current_mileage - log.mileage) / distance * 100))
        time_progress = None
        if log.reminder_date is not None:
            days = (log.reminder_date - log.date_of_service).days
            if days > 0:
                time_progress = min(100, max(0, (today - log.date_of_service).days / days * 100))
        reminders.append(MaintenanceReminder(
            log_id=log.id, car_id=car.id, date_of_service=log.date_of_service,
            mileage=log.mileage, work_done=log.work_done, reminder_date=log.reminder_date,
            reminder_mileage=log.reminder_mileage, current_mileage=current_mileage, current_date=today,
            interval_miles=log.interval_miles, interval_months=log.interval_months,
            is_due=is_due, due_reason=reason,
            is_overdue=(log.reminder_date is not None and today > log.reminder_date) or (
                log.reminder_mileage is not None and current_mileage is not None and current_mileage > log.reminder_mileage
            ),
            progress_miles=mileage_progress, progress_time=time_progress,
            car_name=f"{car.year} {car.make} {car.model}",
        ))
    reminders.sort(key=lambda r: (not r.is_due, reminder_sort_key(r.reminder_date, r.reminder_mileage), str(r.log_id)))
    return reminders


def calculate_next_reminder(
    date_of_service: date,
    mileage: Optional[int],
    interval_months: int | None,
    interval_miles: int | None,
) -> tuple[Optional[date], Optional[int]]:
    reminder_date = (
        date_of_service + relativedelta(months=interval_months)
        if interval_months is not None
        else None
    )
    reminder_mileage = (
        mileage + interval_miles
        if mileage is not None and interval_miles is not None
        else None
    )
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
