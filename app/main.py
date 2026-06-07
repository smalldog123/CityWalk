import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.config import get_settings
from app.core.database import close_mongo_client
from app.core.graph_db import close_falkordb
from app.api import routes, agent, health

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    print(f"[CityWalk] Server starting on {settings.APP_HOST}:{settings.APP_PORT}")
    print(f"[CityWalk] MongoDB: {settings.MONGODB_URI}")
    print(f"[CityWalk] FalkorDB: {settings.FALKORDB_HOST}:{settings.FALKORDB_PORT}")
    yield
    await close_mongo_client()
    close_falkordb()
    print("[CityWalk] Server shutting down")


app = FastAPI(
    title="CityWalk API",
    description="智能徒步路线搜索平台 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api/v1")
app.include_router(agent.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/routes")
async def serve_routes_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/chat")
async def serve_chat_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/map/{route_id}")
async def serve_map_page(route_id: str):
    return FileResponse(os.path.join(STATIC_DIR, "map.html"))


@app.get("/track")
async def serve_track_page():
    return FileResponse(os.path.join(STATIC_DIR, "track.html"))


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.DEBUG,
    )
