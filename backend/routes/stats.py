from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog

router = APIRouter(prefix="/vehicles/{vehicle_id}/stats", tags=["Stats"])


@router.get("/")
async def get_vehicle_stats(vehicle_id: str):
    car = await CarModel.get(PydanticObjectId(vehicle_id))
    if not car:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    pipeline = [
        {"$match": {"vehicle_id": PydanticObjectId(vehicle_id)}},
        {"$group": {
            "_id": None,
            "log_count": {"$sum": 1},
            "avg_cost_per_service": {"$avg": "$cost"},
            "total_spent": {"$sum": "$cost"},
            "max_cost": {"$max": "$cost"}
        }}
    ]

    collection = MaintenanceLog.get_pymongo_collection()
    cursor = collection.aggregate(pipeline)
    result = await cursor.to_list(length=None)  # type: ignore[attr-defined]

    if not result:
        return {
            "log_count": 0,
            "avg_cost_per_service": 0.0,
            "total_spent": 0.0,
            "max_cost": 0.0,
            "cost_by_category": {}
        }

    stats = result[0]
    stats.pop("_id", None)

    category_pipeline = [
        {"$match": {"vehicle_id": PydanticObjectId(vehicle_id)}},
        {"$group": {
            "_id": "$category",
            "total_spent": {"$sum": "$cost"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total_spent": -1}}
    ]

    category_cursor = collection.aggregate(category_pipeline)
    category_result = await category_cursor.to_list(length=None)  # type: ignore[attr-defined]

    stats["cost_by_category"] = {
        entry["_id"]: {"total_spent": entry["total_spent"], "count": entry["count"]}
        for entry in category_result
    }

    return stats
