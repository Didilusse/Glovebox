from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.config import settings
from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog
from backend.models.mod import ModItem

client = None
client_factory = AsyncIOMotorClient


async def init_db():
    global client
    client = client_factory(settings.mongodb_uri)
    await init_beanie(
        database=client[settings.database_name], # type: ignore
        document_models=[
            MaintenanceLog,
            CarModel,
            ModItem
        ]
    )


async def close_db():
    global client
    if client is not None:
        client.close()
        client = None
