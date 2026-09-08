from fastapi import APIRouter, Depends, HTTPException, Query, status
from beanie import PydanticObjectId
from typing import List
from backend.auth import get_mods_car
from backend.config import settings
from backend.models.car_model import CarModel
from backend.models.mod import ModItem, ModItemCreate, ModItemMove, ModItemUpdate, Status
from backend.services.quotas import QuotaExceeded, claim_quota, release_quota

router = APIRouter(
    prefix="/cars/{car_id}/planned-mods",
    tags=["Planned Mods"]
)

async def get_status_mods(car_id: PydanticObjectId, mod_status: Status) -> List[ModItem]:
    return await ModItem.find(
        ModItem.car_id == car_id,
        ModItem.status == mod_status,
    ).sort("position", "_id").limit(settings.max_mods_per_car).to_list()


async def save_positions(car_id: PydanticObjectId, mods: List[ModItem]) -> None:
    changes = []
    for position, mod in enumerate(mods):
        if mod.position != position:
            mod.position = position
            changes.append((mod.id, position))
    if changes:
        await ModItem.get_pymongo_collection().update_many(
            {"_id": {"$in": [mod_id for mod_id, _ in changes]}, "car_id": car_id},
            [{"$set": {"position": {"$switch": {
                "branches": [
                    {"case": {"$eq": ["$_id", mod_id]}, "then": position}
                    for mod_id, position in changes
                ],
                "default": "$position",
            }}}}],
        )


async def save_mod(mod: ModItem) -> None:
    await mod.save()
    # Beanie save can upsert after the deletion cascade has already passed.
    if not await CarModel.find_one({"_id": mod.car_id, "is_deleting": {"$ne": True}}):
        await mod.delete()
        await release_quota("mods", mod.id)
        raise HTTPException(status_code=404, detail="Car not found")

@router.post("/", response_model=ModItem, status_code=status.HTTP_201_CREATED)
async def create_planned_mod(
    car_id: PydanticObjectId,
    mod_data: ModItemCreate,
    car: CarModel = Depends(get_mods_car),
):
    column = await get_status_mods(car_id, mod_data.status)
    position = column[-1].position + 1 if column else 0
    # Unpack the create schema and inject the car_id from the URL
    new_mod = ModItem(
        id=PydanticObjectId(),
        car_id=car_id,
        position=position,
        **mod_data.model_dump(mode="json"),
    )
    try:
        await claim_quota("mods", car_id, new_mod.id, settings.max_mods_per_car,
                          ModItem.get_pymongo_collection(), {"car_id": car_id})
    except QuotaExceeded:
        raise HTTPException(status_code=409, detail="Planned mod quota reached") from None
    try:
        await new_mod.insert()
    except Exception:
        await release_quota("mods", new_mod.id)
        raise

    car_still_exists = await CarModel.find_one(
        CarModel.id == car_id,
        CarModel.is_deleting == False,
    )
    if not car_still_exists:
        await new_mod.delete()
        await release_quota("mods", new_mod.id)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    
    return new_mod


@router.get("/", response_model=List[ModItem])
async def get_planned_mods(
    car_id: PydanticObjectId,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    _: CarModel = Depends(get_mods_car),
):
    # Find all mods associated with this specific car
    mods = await ModItem.find(ModItem.car_id == car_id).sort(
        "status", "position", "_id"
    ).skip(skip).limit(limit).to_list()
    return mods


@router.patch("/{mod_id}/move", response_model=ModItem)
async def move_planned_mod(
    car_id: PydanticObjectId,
    mod_id: PydanticObjectId,
    move: ModItemMove,
    _: CarModel = Depends(get_mods_car),
):
    mod = await ModItem.find_one(ModItem.id == mod_id, ModItem.car_id == car_id)
    if not mod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mod item not found for this car",
        )

    source_status = mod.status
    source = await get_status_mods(car_id, source_status)
    source = [item for item in source if item.id != mod.id]

    if move.status == source_status:
        destination = source
    else:
        destination = await get_status_mods(car_id, move.status)

    if move.position > len(destination):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Position is outside the destination status",
        )

    mod.status = move.status
    mod.position = move.position
    destination.insert(move.position, mod)
    await save_mod(mod)
    if move.status == source_status:
        await save_positions(car_id, destination)
    else:
        await save_positions(car_id, source)
        await save_positions(car_id, destination)
    return mod


@router.patch("/{mod_id}", response_model=ModItem)
async def update_planned_mod(
    car_id: PydanticObjectId,
    mod_id: PydanticObjectId,
    mod_update: ModItemUpdate,
    _: CarModel = Depends(get_mods_car),
):
    # Find the specific mod, ensuring it belongs to the specified car
    mod = await ModItem.find_one(ModItem.id == mod_id, ModItem.car_id == car_id)
    if not mod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Mod item not found for this car"
        )
    
    update_data = mod_update.model_dump(exclude_unset=True, mode="json")
    old_status = mod.status
    status_changed = "status" in update_data and update_data["status"] != old_status
    if status_changed:
        source = await get_status_mods(car_id, old_status)
        source = [item for item in source if item.id != mod.id]
        destination = await get_status_mods(car_id, update_data["status"])
        mod.position = destination[-1].position + 1 if destination else 0

    # Update only the fields that were provided in the request
    for key, value in update_data.items():
        setattr(mod, key, value)

    await save_mod(mod)
    if status_changed:
        await save_positions(car_id, source)
    return mod

# DELETE
@router.delete("/{mod_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planned_mod(
    car_id: PydanticObjectId,
    mod_id: PydanticObjectId,
    _: CarModel = Depends(get_mods_car),
):
    mod = await ModItem.find_one(ModItem.id == mod_id, ModItem.car_id == car_id)
    if not mod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Mod item not found for this car"
        )
    old_status = mod.status
    await mod.delete()
    await release_quota("mods", mod.id)
    await save_positions(car_id, await get_status_mods(car_id, old_status))
