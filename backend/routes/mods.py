from fastapi import APIRouter, HTTPException, Query, status
from beanie import PydanticObjectId
from typing import List
from backend.models.car_model import CarModel
from backend.models.mod import ModItem, ModItemCreate, ModItemUpdate

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

@router.post("/", response_model=ModItem, status_code=status.HTTP_201_CREATED)
async def create_planned_mod(car_id: PydanticObjectId, mod_data: ModItemCreate):
    await get_car_or_404(car_id)
    
    # Unpack the create schema and inject the car_id from the URL
    new_mod = ModItem(car_id=car_id, **mod_data.model_dump(mode="json"))
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
    mods = await ModItem.find(ModItem.car_id == car_id).sort(ModItem.id).skip(skip).limit(limit).to_list()
    return mods


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
    
    # Update only the fields that were provided in the request
    update_data = mod_update.model_dump(exclude_unset=True, mode="json")
    for key, value in update_data.items():
        setattr(mod, key, value)
        
    await mod.save()
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
        
    await mod.delete()
