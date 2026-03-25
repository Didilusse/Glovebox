from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from beanie import init_beanie
from backend.config import settings
from backend.models.maintenance_log import MaintenanceLog


client = AsyncIOMotorClient(settings.mongodb_uri)
db = client.get_database(settings.database_name)

def get_car_collection():
    return db.get_collection("cars")

async def init_db():
    await init_beanie(
        database=client[settings.database_name], # type: ignore
        document_models=[
            MaintenanceLog
        ]
    )