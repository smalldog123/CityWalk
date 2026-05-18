from __future__ import annotations
from typing import Optional, Any
from datetime import datetime
from app.core.database import get_database
from app.models.route import RouteCreate, RouteSearchQuery, DifficultyLevel
from bson import ObjectId


def _route_helper(route: dict) -> dict:
    route["_id"] = str(route["_id"])
    return route


class RouteService:
    def __init__(self):
        self._db: Any = None

    async def _get_collection(self):
        if self._db is None:
            self._db = await get_database()
        return self._db.routes

    async def create_route(self, route: RouteCreate) -> dict:
        collection = await self._get_collection()
        now = datetime.utcnow()
        doc = route.model_dump()
        doc["created_at"] = now
        doc["updated_at"] = now
        result = await collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def get_route(self, route_id: str) -> Optional[dict]:
        collection = await self._get_collection()
        route = await collection.find_one({"_id": ObjectId(route_id)})
        if route:
            return _route_helper(route)
        return None

    async def search_routes(self, query: RouteSearchQuery) -> list[dict]:
        collection = await self._get_collection()
        filter_doc: dict = {}

        if query.city:
            filter_doc["city"] = query.city
        if query.difficulty:
            filter_doc["difficulty"] = query.difficulty.value
        if query.min_distance is not None or query.max_distance is not None:
            distance_filter = {}
            if query.min_distance is not None:
                distance_filter["$gte"] = query.min_distance
            if query.max_distance is not None:
                distance_filter["$lte"] = query.max_distance
            filter_doc["distance_km"] = distance_filter
        if query.tags:
            filter_doc["tags"] = {"$in": query.tags}
        if query.keyword:
            filter_doc["$or"] = [
                {"name": {"$regex": query.keyword, "$options": "i"}},
                {"description": {"$regex": query.keyword, "$options": "i"}},
            ]

        cursor = collection.find(filter_doc).skip(query.offset).limit(query.limit)
        routes = await cursor.to_list(length=query.limit)
        return [_route_helper(r) for r in routes]

    async def list_routes(self, limit: int = 20, offset: int = 0) -> list[dict]:
        collection = await self._get_collection()
        cursor = collection.find().skip(offset).limit(limit).sort("created_at", -1)
        routes = await cursor.to_list(length=limit)
        return [_route_helper(r) for r in routes]

    async def fuzzy_match_routes(self, names: list[str]) -> list[dict]:
        collection = await self._get_collection()
        results = []
        for name in names:
            exact = await collection.find_one({"name": name})
            if exact:
                results.append(_route_helper(exact))
                continue
            substring = await collection.find_one({"name": {"$regex": name, "$options": "i"}})
            if substring:
                results.append(_route_helper(substring))
                continue
            keywords = name.split()
            for kw in keywords:
                kw_match = await collection.find_one({"name": {"$regex": kw, "$options": "i"}})
                if kw_match:
                    results.append(_route_helper(kw_match))
                    break
        return results

    async def count_routes(self, query: RouteSearchQuery) -> int:
        collection = await self._get_collection()
        filter_doc: dict = {}
        if query.city:
            filter_doc["city"] = query.city
        if query.difficulty:
            filter_doc["difficulty"] = query.difficulty.value
        return await collection.count_documents(filter_doc)
