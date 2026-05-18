from __future__ import annotations
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import get_settings

_client: Optional[AsyncIOMotorClient] = None


async def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = AsyncIOMotorClient(settings.MONGODB_URI)
    return _client


async def get_database():
    settings = get_settings()
    client = await get_mongo_client()
    return client[settings.MONGODB_DB_NAME]


async def close_mongo_client():
    global _client
    if _client is not None:
        _client.close()
        _client = None
