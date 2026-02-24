from fastapi import FastAPI

from app.api.routers.robots import router as robots_router
from app.api.routers.missions import router as missions_router

app = FastAPI(title="Mini WES API", version="0.1.0")

app.include_router(robots_router)
app.include_router(missions_router)

@app.get("/health")
def health():
    return {"status": "ok"}