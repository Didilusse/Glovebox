from fastapi import APIRouter, HTTPException
from bson import ObjectId
from backend.models.maintenance_log import MaintenanceLog, MaintenanceLogCreate
from backend.database import get_car_collection

router = APIRouter(prefix="/vehicles/{vehicle_id}/logs", tags=["Maintenance Logs"])

@router.post("/", response_model=MaintenanceLog, status_code=201)
async def create_maintenance_log(vehicle_id: str, log_data: MaintenanceLogCreate):
    car_collection = get_car_collection()
    car = await car_collection.find_one({"_id": ObjectId(vehicle_id)})
    
    if not car:
        raise HTTPException(status_code=404, detail="Vehicle not found")
        
    # TODO: Create and save the maintenance log