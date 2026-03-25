from beanie import  PydanticObjectId
from fastapi import APIRouter, HTTPException
from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog, MaintenanceLogCreate, MaintenanceLogUpdate
from backend.database import get_car_collection
from typing import List
router = APIRouter(prefix="/vehicles/{vehicle_id}/logs", tags=["Maintenance Logs"])

@router.post("/", response_model=MaintenanceLog, status_code=201)
async def create_maintenance_log(vehicle_id: str, log_data: MaintenanceLogCreate):
    car_collection = get_car_collection()
    car = await CarModel.get(PydanticObjectId(vehicle_id))
    
    if not car:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    if log_data.mileage > (car.mileage or 0):
        car.mileage = log_data.mileage                    
        await car.save()
    

    maintenanceLog = MaintenanceLog(
        vehicle_id=PydanticObjectId(vehicle_id),
        **log_data.model_dump()
    )
    await maintenanceLog.insert()
    return maintenanceLog

@router.get("/", response_model=List[MaintenanceLog])
async def get_maintenance_logs(vehicle_id: str):
    car = await CarModel.get(PydanticObjectId(vehicle_id))
    
    if not car:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    maintenance_logs = await MaintenanceLog.find(MaintenanceLog.vehicle_id == PydanticObjectId(vehicle_id)).to_list()
    return maintenance_logs

@router.get("/{log_id}", response_model=MaintenanceLog)
async def get_maintenance_log(vehicle_id: str, log_id: str):
    car = await CarModel.get(PydanticObjectId(vehicle_id))
    
    if not car:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    maintenance_log = await MaintenanceLog.get(PydanticObjectId(log_id))
    
    if not maintenance_log or maintenance_log.vehicle_id != PydanticObjectId(vehicle_id):
        raise HTTPException(status_code=404, detail="Maintenance log not found for this vehicle")
    
    return maintenance_log

@router.patch("/{log_id}", response_model=MaintenanceLog)
async def update_maintenance_log(vehicle_id: str, log_id: str, log_data: MaintenanceLogUpdate):
    car = await CarModel.get(PydanticObjectId(vehicle_id))
    
    if not car:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    update_data = log_data.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    
    maintenance_log = await MaintenanceLog.get(PydanticObjectId(log_id))
    
    if not maintenance_log or maintenance_log.vehicle_id != PydanticObjectId(vehicle_id):
        raise HTTPException(status_code=404, detail="Maintenance log not found for this vehicle")
    
    await maintenance_log.update({"$set": update_data})
    updated_log = await MaintenanceLog.get(PydanticObjectId(log_id))
    return updated_log

@router.delete("/{log_id}", status_code=204)
async def delete_maintenance_log(vehicle_id: str, log_id: str):
    car = await CarModel.get(PydanticObjectId(vehicle_id))
    
    if not car:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    
    maintenance_log = await MaintenanceLog.get(PydanticObjectId(log_id))
    
    if not maintenance_log or maintenance_log.vehicle_id != PydanticObjectId(vehicle_id):
        raise HTTPException(status_code=404, detail="Maintenance log not found for this vehicle")
    
    await maintenance_log.delete()