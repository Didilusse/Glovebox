from fastapi import FastAPI
from backend.routes import car_route

app = FastAPI(title="Vehicle API")

app.include_router(car_route.router)