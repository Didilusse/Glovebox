from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import close_db, init_db
from backend.routes import carfax_car_import, maintenance_import, maintenance_logs, car_route, stats, reminder, mods, nhtsa


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        yield
    finally:
        await close_db()

app = FastAPI(title="Glovebox API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=r"https?://.*",
    allow_credentials=False,
    allow_methods=["*"], 
    allow_headers=["*"],
)

app.include_router(car_route.router)
app.include_router(carfax_car_import.router)
app.include_router(maintenance_logs.router)
app.include_router(maintenance_import.router)
app.include_router(reminder.router)
app.include_router(stats.router)
app.include_router(mods.router)
app.include_router(nhtsa.router)
