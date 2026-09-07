from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.auth import get_owned_car
from backend.models.car_model import CarModel
from backend.models.maintenance_log import (
    MaintenanceLog,
    MaintenanceLogCreate,
    MaintenanceLogUpdate,
)
from typing import List

from backend.services.maintenance import create_log
from backend.services.reminders import calculate_next_reminder

router = APIRouter(prefix="/cars/{car_id}/logs", tags=["Maintenance Logs"])

@router.post("/", response_model=MaintenanceLog, status_code=201)
async def create_maintenance_log(
    car_id: PydanticObjectId,
    log_data: MaintenanceLogCreate,
    _: CarModel = Depends(get_owned_car),
):
    return await create_log(car_id, log_data)

@router.get("/", response_model=List[MaintenanceLog])
async def get_maintenance_logs(car_id: PydanticObjectId, done_by: str | None = None,
                               min_cost: float | None = None, max_cost: float | None = None,
                               sort_by: str | None = None, sort_order: str = "asc",
                               skip: int = Query(0, ge=0),
                               limit: int = Query(100, ge=1, le=100),
                               _: CarModel = Depends(get_owned_car)):

    VALID_SORT_FIELDS = {"date_of_service", "cost", "mileage", "done_by", "work_done"}
    if sort_by is not None and sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by. Allowed: {sorted(VALID_SORT_FIELDS)}")

    if sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid sort_order. Allowed: 'asc', 'desc'")

    if min_cost is not None and max_cost is not None and min_cost > max_cost:
        raise HTTPException(status_code=400, detail="min_cost must be <= max_cost")

    query = MaintenanceLog.find(MaintenanceLog.car_id == car_id)
    if done_by is not None:
        query = query.find(MaintenanceLog.done_by == done_by)
    if min_cost is not None:
        query = query.find(MaintenanceLog.cost >= min_cost)
    if max_cost is not None:
        query = query.find(MaintenanceLog.cost <= max_cost)
    if sort_by is not None:
        sort_field = getattr(MaintenanceLog, sort_by)
        if sort_order == "desc":
            query = query.sort(-sort_field, MaintenanceLog.id)
        else:
            query = query.sort(sort_field, MaintenanceLog.id)
    else:
        query = query.sort(MaintenanceLog.id)

    query = query.skip(skip).limit(limit)

    maintenance_logs = await query.to_list()
    return maintenance_logs

@router.get("/{log_id}", response_model=MaintenanceLog)
async def get_maintenance_log(
    car_id: PydanticObjectId,
    log_id: PydanticObjectId,
    _: CarModel = Depends(get_owned_car),
):
    maintenance_log = await MaintenanceLog.find_one(
        MaintenanceLog.id == log_id,
        MaintenanceLog.car_id == car_id
    )

    if not maintenance_log:
        raise HTTPException(status_code=404, detail="Maintenance log not found for this car")

    return maintenance_log

@router.patch("/{log_id}", response_model=MaintenanceLog)
async def update_maintenance_log(
    car_id: PydanticObjectId,
    log_id: PydanticObjectId,
    log_data: MaintenanceLogUpdate,
    _: CarModel = Depends(get_owned_car),
):
    update_data = log_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    maintenance_log = await MaintenanceLog.get(log_id)

    if not maintenance_log or maintenance_log.car_id != car_id:
        raise HTTPException(status_code=404, detail="Maintenance log not found for this car")

    original_payload = maintenance_log.model_dump()
    updated_payload = original_payload.copy()
    updated_payload.update(update_data)

    reminder_date, reminder_mileage = calculate_next_reminder(
        date_of_service=updated_payload["date_of_service"],
        mileage=updated_payload["mileage"],
        interval_months=updated_payload.get("interval_months"),
        interval_miles=updated_payload.get("interval_miles"),
    )

    updated_payload["reminder_date"] = reminder_date
    updated_payload["reminder_mileage"] = reminder_mileage

    for key, value in updated_payload.items():
        setattr(maintenance_log, key, value)

    await maintenance_log.save()
    try:
        update = (
            {"$max": {"mileage": maintenance_log.mileage}}
            if maintenance_log.mileage is not None
            else {"$set": {"is_deleting": False}}
        )
        result = await CarModel.get_pymongo_collection().update_one(
            {"_id": car_id, "is_deleting": {"$ne": True}},
            update,
        )
    except Exception:
        for key, value in original_payload.items():
            setattr(maintenance_log, key, value)
        await maintenance_log.save()
        raise
    if result.matched_count == 0:
        await maintenance_log.delete()
        raise HTTPException(status_code=404, detail="Car not found")
    return maintenance_log

@router.delete("/{log_id}", status_code=204)
async def delete_maintenance_log(
    car_id: PydanticObjectId,
    log_id: PydanticObjectId,
    _: CarModel = Depends(get_owned_car),
):
    maintenance_log = await MaintenanceLog.get(log_id)

    if not maintenance_log or maintenance_log.car_id != car_id:
        raise HTTPException(status_code=404, detail="Maintenance log not found for this car")

    await maintenance_log.delete()
