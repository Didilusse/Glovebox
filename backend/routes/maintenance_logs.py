from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog, MaintenanceLogCreate, MaintenanceLogUpdate
from typing import List

router = APIRouter(prefix="/cars/{car_id}/logs", tags=["Maintenance Logs"])

@router.post("/", response_model=MaintenanceLog, status_code=201)
async def create_maintenance_log(car_id: str, log_data: MaintenanceLogCreate):
    car = await CarModel.get(PydanticObjectId(car_id))

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    if log_data.mileage > (car.mileage or 0):
        car.mileage = log_data.mileage
        await car.save()

    maintenanceLog = MaintenanceLog(
        car_id=PydanticObjectId(car_id),
        **log_data.model_dump()
    )
    await maintenanceLog.insert()
    return maintenanceLog

@router.get("/", response_model=List[MaintenanceLog])
async def get_maintenance_logs(car_id: str, done_by: str | None = None,
                               min_cost: float | None = None, max_cost: float | None = None,
                               sort_by: str | None = None, sort_order: str = "asc", skip: int = 0,
                               limit: int = 100):
    try:
        oid = PydanticObjectId(car_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid car ID format")

    VALID_SORT_FIELDS = {"date_of_service", "cost", "mileage", "done_by", "work_done"}
    if sort_by is not None and sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by. Allowed: {sorted(VALID_SORT_FIELDS)}")

    if sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid sort_order. Allowed: 'asc', 'desc'")

    if min_cost is not None and max_cost is not None and min_cost > max_cost:
        raise HTTPException(status_code=400, detail="min_cost must be <= max_cost")

    car = await CarModel.get(oid)
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    query = MaintenanceLog.find(MaintenanceLog.car_id == oid)
    if done_by is not None:
        query = query.find(MaintenanceLog.done_by == done_by)
    if min_cost is not None:
        query = query.find(MaintenanceLog.cost >= min_cost)
    if max_cost is not None:
        query = query.find(MaintenanceLog.cost <= max_cost)
    if skip > 0:
        query = query.skip(skip)
    if limit > 0:
        query = query.limit(limit)

    if sort_by is not None:
        if sort_order == "desc":
            query = query.sort(-getattr(MaintenanceLog, sort_by))
        else:
            query = query.sort(getattr(MaintenanceLog, sort_by))

    maintenance_logs = await query.to_list()
    return maintenance_logs

@router.get("/{log_id}", response_model=MaintenanceLog)
async def get_maintenance_log(car_id: str, log_id: str):
    car = await CarModel.get(PydanticObjectId(car_id))

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    maintenance_log = await MaintenanceLog.find_one(
        MaintenanceLog.id == PydanticObjectId(log_id),
        MaintenanceLog.car_id == PydanticObjectId(car_id)
    )

    if not maintenance_log:
        raise HTTPException(status_code=404, detail="Maintenance log not found for this car")

    return maintenance_log

@router.patch("/{log_id}", response_model=MaintenanceLog)
async def update_maintenance_log(car_id: str, log_id: str, log_data: MaintenanceLogUpdate):
    car = await CarModel.get(PydanticObjectId(car_id))

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    update_data = log_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    maintenance_log = await MaintenanceLog.get(PydanticObjectId(log_id))

    if not maintenance_log or maintenance_log.car_id != PydanticObjectId(car_id):
        raise HTTPException(status_code=404, detail="Maintenance log not found for this car")

    await maintenance_log.update({"$set": update_data})
    updated_log = await MaintenanceLog.get(PydanticObjectId(log_id))
    return updated_log

@router.delete("/{log_id}", status_code=204)
async def delete_maintenance_log(car_id: str, log_id: str):
    car = await CarModel.get(PydanticObjectId(car_id))

    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    maintenance_log = await MaintenanceLog.get(PydanticObjectId(log_id))

    if not maintenance_log or maintenance_log.car_id != PydanticObjectId(car_id):
        raise HTTPException(status_code=404, detail="Maintenance log not found for this car")

    await maintenance_log.delete()
