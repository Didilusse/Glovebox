from typing import List

from fastapi import APIRouter, Depends, Query

from backend.auth import get_maintenance_car
from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceReminder
from backend.services.reminders import car_reminders

router = APIRouter(prefix="/cars/{car_id}/reminders", tags=["Reminders"])


@router.get("/", response_model=List[MaintenanceReminder])
async def list_reminders(
    car: CarModel = Depends(get_maintenance_car),
    only_due: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    reminders = await car_reminders(car)
    if only_due:
        reminders = [reminder for reminder in reminders if reminder.is_due]
    return reminders[skip:skip + limit]
