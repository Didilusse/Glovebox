from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException
from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog

router = APIRouter(prefix="/cars/{car_id}/stats", tags=["Stats"])


@router.get("/")
async def get_vehicle_stats(car_id: str):
    car = await CarModel.get(PydanticObjectId(car_id))
    if not car:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    pipeline = [
        {"$match": {"car_id": PydanticObjectId(car_id)}},
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
            "distance_travelled": None,
            "cost_by_done_by": {}
        }

    stats = result[0]
    stats.pop("_id", None)

    if car.mileage is not None and car.initial_mileage is not None:
        stats["distance_travelled"] = car.mileage - car.initial_mileage
    else:
        stats["distance_travelled"] = None

    done_by_pipeline = [
        {"$match": {"car_id": PydanticObjectId(car_id)}},
        {"$group": {
            "_id": "$done_by",
            "total_spent": {"$sum": "$cost"},
            "count": {"$sum": 1}
        }},
        {"$sort": {"total_spent": -1}}
    ]

    done_by_cursor = collection.aggregate(done_by_pipeline)
    done_by_result = await done_by_cursor.to_list(length=None)  # type: ignore[attr-defined]

    stats["cost_by_done_by"] = {
        entry["_id"]: {"total_spent": entry["total_spent"], "count": entry["count"]}
        for entry in done_by_result
    }

    return stats
