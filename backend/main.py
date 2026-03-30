from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.database import init_db
from backend.routes import maintenance_logs, car_route, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Glovebox API", lifespan=lifespan)

app.include_router(car_route.router)
app.include_router(maintenance_logs.router)
app.include_router(stats.router)