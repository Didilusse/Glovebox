import asyncio

from mongomock_motor import AsyncMongoMockClient

from backend.migrations import apply_default_migrations


def test_default_migration_backfills_missing_car_fields_without_overwriting_values():
    async def run_test():
        database = AsyncMongoMockClient().glovebox
        await database.cars.insert_one({
            "make": "Toyota",
            "model": "Corolla",
            "year": 2014,
            "mileage": 55_202,
        })

        await apply_default_migrations(database)
        migrated = await database.cars.find_one({"make": "Toyota"})

        assert migrated["mileage"] == 55_202
        assert migrated["initial_mileage"] is None
        assert migrated["is_deleting"] is False
        assert await database.schema_migrations.find_one({"_id": "model-defaults"})

    asyncio.run(run_test())
