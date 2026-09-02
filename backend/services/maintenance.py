from typing import Any

from beanie import PydanticObjectId
from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog, MaintenanceLogCreate
from backend.services.reminders import calculate_next_reminder


async def create_log(car_id: PydanticObjectId, log_data: MaintenanceLogCreate) -> MaintenanceLog:
    car = await CarModel.get(car_id)
    if not car or car.is_deleting:
        raise HTTPException(status_code=404, detail="Car not found")

    reminder_date, reminder_mileage = calculate_next_reminder(
        date_of_service=log_data.date_of_service,
        mileage=log_data.mileage,
        interval_months=log_data.interval_months,
        interval_miles=log_data.interval_miles,
    )
    log = MaintenanceLog(
        car_id=car_id,
        reminder_date=reminder_date,
        reminder_mileage=reminder_mileage,
        **log_data.model_dump(),
    )
    await log.insert()

    try:
        result = await CarModel.get_pymongo_collection().update_one(
            {"_id": car_id, "is_deleting": {"$ne": True}},
            {"$max": {"mileage": log_data.mileage}},
        )
    except Exception:
        await log.delete()
        raise
    if result.matched_count == 0:
        await log.delete()
        raise HTTPException(status_code=404, detail="Car not found")
    return log


async def create_imported_logs(
    car_id: PydanticObjectId,
    records: list[dict[str, Any]],
) -> tuple[list[MaintenanceLog], int]:
    car = await CarModel.get(car_id)
    if not car or car.is_deleting:
        raise HTTPException(status_code=404, detail="Car not found")

    created: list[MaintenanceLog] = []
    skipped = 0
    try:
        for record in records:
            log = MaintenanceLog(car_id=car_id, source="carfax", **record)
            try:
                await log.insert()
            except DuplicateKeyError:
                skipped += 1
                continue
            created.append(log)

        known_mileages = [log.mileage for log in created if log.mileage is not None]
        update = (
            {"$max": {"mileage": max(known_mileages)}}
            if known_mileages
            else {"$set": {"is_deleting": False}}
        )
        result = await CarModel.get_pymongo_collection().update_one(
            {"_id": car_id, "is_deleting": {"$ne": True}},
            update,
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Car not found")
    except Exception:
        for log in created:
            await log.delete()
        raise

    return created, skipped
