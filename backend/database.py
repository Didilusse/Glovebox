from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.config import settings
from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog
from backend.models.mod import ModItem
from backend.models.session import AuthSession
from backend.models.user import LoginRateLimit, User
from backend.models.car_share import CarShare
from backend.models.notification import Notification, UserPreferences
from backend.migrations import apply_default_migrations

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
            ModItem,
            CarShare,
            Notification,
            UserPreferences,
            User,
            AuthSession,
            LoginRateLimit,
        ]
    )
    await apply_default_migrations(client[settings.database_name])
    await recover_legacy_claim()


async def recover_legacy_claim():
    # The first insert is the bootstrap marker. Repeating the ownerless-only claim
    # is safe after a crash between account creation, claiming, and completion.
    admin = await User.find(User.is_admin == True).sort(User.created_at, User.id).first_or_none()
    if admin and not admin.legacy_claim_complete:
        await CarModel.get_pymongo_collection().update_many(
            {"owner_id": None}, {"$set": {"owner_id": admin.id}}
        )
        await User.get_pymongo_collection().update_one(
            {"_id": admin.id}, {"$set": {"legacy_claim_complete": True}}
        )


async def close_db():
    global client
    if client is not None:
        client.close()
        client = None
