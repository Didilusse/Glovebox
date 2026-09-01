from datetime import date

from backend.services.reminders import calculate_next_reminder, determine_due_reason


def test_calculate_next_reminder_handles_end_of_month_and_leap_year():
    reminder_date, reminder_mileage = calculate_next_reminder(
        date(2024, 1, 31),
        10_000,
        interval_months=1,
        interval_miles=5_000,
    )
    assert reminder_date == date(2024, 2, 29)
    assert reminder_mileage == 15_000


def test_determine_due_reason_covers_each_due_condition():
    today = date(2026, 1, 1)
    assert determine_due_reason(today, 10_000, today, 10_000) == (True, "both")
    assert determine_due_reason(today, None, today, None) == (True, "date")
    assert determine_due_reason(None, 10_000, today, 10_000) == (True, "mileage")
    assert determine_due_reason(None, None, today, None) == (False, None)
