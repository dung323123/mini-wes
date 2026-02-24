from fastapi import FastAPI

from app.api.routers.robots import router as robots_router
from app.api.routers.missions import router as missions_router
from app.api.routers.orders import router as orders_router
from app.api.routers.tasks import router as tasks_router
from app.api.routers.allocator import router as allocator_router
from app.api.routers.telemetry import router as telemetry_router

app = FastAPI(title="Mini WES API", version="0.1.0")

app.include_router(robots_router)
app.include_router(missions_router)
app.include_router(orders_router)
app.include_router(tasks_router)
app.include_router(allocator_router)
app.include_router(telemetry_router)

@app.get("/health")
def health():
    return {"status": "ok"}
