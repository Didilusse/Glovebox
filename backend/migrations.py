import hashlib
import json
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from pydantic_core import PydanticUndefined

from backend.models.car_model import CarModel
from backend.models.maintenance_log import MaintenanceLog
from backend.models.mod import ModItem
from backend.models.car_share import CarShare


DEFAULT_MIGRATION_ID = "model-defaults"
MODELS = (
    (CarModel, "cars"),
    (MaintenanceLog, "maintenance_logs"),
    (ModItem, "mods"),
    (CarShare, "car_shares"),
)


def _model_defaults(model: type) -> dict[str, Any]:
    defaults = {}
    for name, field in model.model_fields.items():
        if field.default is not PydanticUndefined:
            defaults[name] = deepcopy(field.default)
    return defaults


def _defaults_signature(defaults_by_collection: dict[str, dict[str, Any]]) -> str:
    payload = json.dumps(defaults_by_collection, default=str, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


async def apply_default_migrations(database) -> None:
    """Backfill newly added model fields with defaults without overwriting stored values."""
    defaults_by_collection = {
        collection: _model_defaults(model)
        for model, collection in MODELS
    }
    signature = _defaults_signature(defaults_by_collection)
    migrations = database.schema_migrations
    applied = await migrations.find_one({"_id": DEFAULT_MIGRATION_ID})
    if not applied or applied.get("signature") != signature:
        for collection, defaults in defaults_by_collection.items():
            for field, default in defaults.items():
                await database[collection].update_many(
                    {field: {"$exists": False}},
                    {"$set": {field: default}},
                )

        await migrations.update_one(
            {"_id": DEFAULT_MIGRATION_ID},
            {"$set": {"signature": signature, "applied_at": datetime.now(timezone.utc)}},
            upsert=True,
        )

    await database.quota_slots.create_index(
        [("kind", 1), ("scope", 1), ("resource_id", 1)],
        unique=True,
        name="quota_resource",
    )
