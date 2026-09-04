from fastapi import APIRouter, HTTPException, Query, status
from beanie import PydanticObjectId
from typing import List
from backend.models.car_model import CarModel
from backend.models.mod import ModItem, ModItemCreate, ModItemMove, ModItemUpdate, Status

router = APIRouter(
    prefix="/cars/{car_id}/planned-mods",
    tags=["Planned Mods"]
)

# Helper function to validate the car exists
async def get_car_or_404(car_id: PydanticObjectId) -> CarModel:
    car = await CarModel.get(car_id)
    if not car or car.is_deleting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Car not found"
        )
    return car


async def get_status_mods(car_id: PydanticObjectId, mod_status: Status) -> List[ModItem]:
    return await ModItem.find(
        ModItem.car_id == car_id,
        ModItem.status == mod_status,
    ).sort("position", "_id").to_list()


async def save_positions(mods: List[ModItem]) -> None:
    for position, mod in enumerate(mods):
        if mod.position != position:
            mod.position = position
            await mod.save()

@router.post("/", response_model=ModItem, status_code=status.HTTP_201_CREATED)
async def create_planned_mod(car_id: PydanticObjectId, mod_data: ModItemCreate):
    await get_car_or_404(car_id)

    column = await get_status_mods(car_id, mod_data.status)
    position = column[-1].position + 1 if column else 0
    # Unpack the create schema and inject the car_id from the URL
    new_mod = ModItem(
        car_id=car_id,
        position=position,
        **mod_data.model_dump(mode="json"),
    )
    await new_mod.insert()

    car_still_exists = await CarModel.find_one(
        CarModel.id == car_id,
        CarModel.is_deleting == False,
    )
    if not car_still_exists:
        await new_mod.delete()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found")
    
    return new_mod


@router.get("/", response_model=List[ModItem])
async def get_planned_mods(
    car_id: PydanticObjectId,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
):
    await get_car_or_404(car_id)
    
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
):
    await get_car_or_404(car_id)
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
    await mod.save()
    if move.status == source_status:
        await save_positions(destination)
    else:
        await save_positions(source)
        await save_positions(destination)
    return mod


@router.patch("/{mod_id}", response_model=ModItem)
async def update_planned_mod(
    car_id: PydanticObjectId, 
    mod_id: PydanticObjectId, 
    mod_update: ModItemUpdate
):
    await get_car_or_404(car_id)
    
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

    await mod.save()
    if status_changed:
        await save_positions(source)
    return mod

# DELETE
@router.delete("/{mod_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_planned_mod(car_id: PydanticObjectId, mod_id: PydanticObjectId):
    await get_car_or_404(car_id)
    
    mod = await ModItem.find_one(ModItem.id == mod_id, ModItem.car_id == car_id)
    if not mod:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Mod item not found for this car"
        )
    old_status = mod.status
    await mod.delete()
    await save_positions(await get_status_mods(car_id, old_status))
