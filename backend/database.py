from motor.motor_asyncio import AsyncIOMotorClient
from backend.config import settings

client = AsyncIOMotorClient(settings.mongodb_uri)
db = client.get_database(settings.database_name)

def get_car_collection():
    return db.get_collection("cars")