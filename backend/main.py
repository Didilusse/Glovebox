from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import init_db
from backend.routes import maintenance_logs, car_route, stats, reminder, mods


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

origins = [
    "http://localhost:5173", 
    "http://localhost:8080", 
]

app = FastAPI(title="Glovebox API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],
)

app.include_router(car_route.router)
app.include_router(maintenance_logs.router)
app.include_router(reminder.router)
app.include_router(stats.router)
app.include_router(mods.router)