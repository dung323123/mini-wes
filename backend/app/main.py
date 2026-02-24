from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routers.robots import router as robots_router
from app.api.routers.missions import router as missions_router
from app.api.routers.orders import router as orders_router
from app.api.routers.tasks import router as tasks_router
from app.api.routers.allocator import router as allocator_router
from app.api.routers.telemetry import router as telemetry_router
from app.api.routers.events import router as events_router
from app.api.routers.dashboard import router as dashboard_router

app = FastAPI(title="Mini WES API", version="0.1.0")

cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(robots_router)
app.include_router(missions_router)
app.include_router(orders_router)
app.include_router(tasks_router)
app.include_router(allocator_router)
app.include_router(telemetry_router)
app.include_router(events_router)
app.include_router(dashboard_router)

@app.get("/health")
def health():
    return {"status": "ok"}
