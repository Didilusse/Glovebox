from beanie import PydanticObjectId
from pymongo.errors import DuplicateKeyError

from backend.models.car_model import CarModel


class QuotaExceeded(Exception):
    pass


def _collection():
    database = CarModel.get_pymongo_collection().database
    return database.get_collection("quota_slots")


async def claim_quota(
    kind: str,
    scope: PydanticObjectId,
    resource_id: PydanticObjectId,
    limit: int,
    resource_collection,
    resource_filter: dict,
    **metadata,
) -> None:
    """Reserve one fixed slot while accounting for records created before quotas."""
    scope_value = str(scope)
    slots = _collection()
    reservations = await slots.find(
        {"kind": kind, "scope": scope_value}, {"resource_id": 1}
    ).to_list(length=limit)
    represented_ids = [reservation["resource_id"] for reservation in reservations]
    legacy_filter = {**resource_filter, "_id": {"$nin": represented_ids}}
    legacy_count = await resource_collection.count_documents(legacy_filter, limit=limit)

    for slot in range(legacy_count, limit):
        try:
            await slots.insert_one({
                "_id": f"{kind}:{scope_value}:{slot}",
                "kind": kind,
                "scope": scope_value,
                "resource_id": resource_id,
                **metadata,
            })
            return
        except DuplicateKeyError:
            continue
    raise QuotaExceeded


async def release_quota(kind: str, resource_id: PydanticObjectId) -> None:
    await _collection().delete_one({"kind": kind, "resource_id": resource_id})


async def release_scope(kind: str, scope: PydanticObjectId) -> None:
    await _collection().delete_many({"kind": kind, "scope": str(scope)})


async def release_car_quotas(car_id: PydanticObjectId) -> None:
    slots = _collection()
    await slots.delete_many({"kind": {"$in": ["maintenance_logs", "mods"]}, "scope": str(car_id)})
    await slots.delete_many({"kind": "notifications", "car_id": str(car_id)})
