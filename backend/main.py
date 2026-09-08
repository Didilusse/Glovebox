import asyncio
from contextlib import asynccontextmanager, suppress
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import close_db, init_db
from backend.config import settings
from backend.routes import notification_route
from backend.services.notifications import reminder_worker
from backend.routes import auth_route, carfax_car_import, maintenance_import, maintenance_logs, car_route, stats, reminder, mods, nhtsa, users_route


@asynccontextmanager
async def lifespan(app: FastAPI):
    worker = None
    try:
        await init_db()
        if settings.reminder_worker_enabled:
            worker = asyncio.create_task(reminder_worker())
        yield
    finally:
        if worker:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker
        await close_db()

app = FastAPI(title="Glovebox API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"], 
    allow_headers=["*"],
)

app.include_router(auth_route.router)
app.include_router(users_route.router)
app.include_router(car_route.router)
app.include_router(carfax_car_import.router)
app.include_router(maintenance_logs.router)
app.include_router(maintenance_import.router)
app.include_router(reminder.router)
app.include_router(stats.router)
app.include_router(mods.router)
app.include_router(nhtsa.router)
app.include_router(notification_route.router)
