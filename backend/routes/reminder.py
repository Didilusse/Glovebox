from datetime import date
from typing import List

from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException, Query

from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog, MaintenanceReminder
from backend.services.reminders import determine_due_reason, reminder_sort_key


router = APIRouter(prefix="/cars/{car_id}/reminders", tags=["Reminders"])


@router.get("/", response_model=List[MaintenanceReminder])
async def list_reminders(
	car_id: str,
	only_due: bool = Query(False, description="Return only reminders that are currently due"),
):
	try:
		car_object_id = PydanticObjectId(car_id)
	except Exception:
		raise HTTPException(status_code=400, detail="Invalid car ID format")

	car = await CarModel.get(car_object_id)
	if not car:
		raise HTTPException(status_code=404, detail="Car not found")

	maintenance_logs = await MaintenanceLog.find(MaintenanceLog.car_id == car_object_id).to_list()
	current_date = date.today()
	current_mileage = car.mileage or car.initial_mileage

	reminders = []
	for maintenance_log in maintenance_logs:
		if maintenance_log.id is None:
			continue

		is_due, due_reason = determine_due_reason(
			maintenance_log.reminder_date,
			maintenance_log.reminder_mileage,
			current_date,
			current_mileage,
		)

		if only_due and not is_due:
			continue

		reminders.append(
			MaintenanceReminder(
				log_id=maintenance_log.id,
				car_id=maintenance_log.car_id,
				date_of_service=maintenance_log.date_of_service,
				mileage=maintenance_log.mileage,
				work_done=maintenance_log.work_done,
				reminder_date=maintenance_log.reminder_date,
				reminder_mileage=maintenance_log.reminder_mileage,
				current_mileage=current_mileage,
				is_due=is_due,
				due_reason=due_reason,
			)
		)

	reminders.sort(key=lambda reminder: reminder_sort_key(reminder.reminder_date, reminder.reminder_mileage))
	return reminders
