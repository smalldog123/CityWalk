from __future__ import annotations
from typing import Optional, Any
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
from app.core.database import get_database
from app.models.route import RouteCreate, RouteSearchQuery, DifficultyLevel, GPSPoint, GPXUploadRequest, TrackUploadRequest
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

    def _haversine_distance(self, lat1: float, lng1: float, lat2: float, lng2: float) -> float:
        R = 6371
        dlat = radians(lat2 - lat1)
        dlng = radians(lng2 - lng1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def _calc_gpx_stats(self, points: list[GPSPoint]) -> dict:
        total_distance = 0.0
        total_gain = 0.0
        total_loss = 0.0
        prev_elevation = None

        for i in range(1, len(points)):
            p1 = points[i - 1]
            p2 = points[i]
            total_distance += self._haversine_distance(p1.lat, p1.lng, p2.lat, p2.lng)

            if p1.elevation is not None and p2.elevation is not None:
                diff = p2.elevation - p1.elevation
                if diff > 0:
                    total_gain += diff
                else:
                    total_loss += abs(diff)

        duration = None
        if len(points) >= 2:
            first_time = points[0].timestamp
            last_time = points[-1].timestamp
            if first_time and last_time:
                try:
                    dt = last_time - first_time
                    duration = round(dt.total_seconds() / 3600, 1)
                except Exception:
                    pass

        if duration is None:
            duration = round(total_distance / 4.0, 1)

        return {
            "distance_km": round(total_distance, 2),
            "elevation_gain_m": round(total_gain, 1),
            "elevation_loss_m": round(total_loss, 1),
            "duration_hours": duration,
        }

    async def create_from_gpx(self, data: GPXUploadRequest) -> dict:
        stats = self._calc_gpx_stats(data.gpx_points)

        difficulty = data.difficulty or DifficultyLevel.MODERATE
        if stats["distance_km"] > 30 or stats["elevation_gain_m"] > 2000:
            difficulty = DifficultyLevel.EXPERT
        elif stats["distance_km"] > 20 or stats["elevation_gain_m"] > 1000:
            difficulty = DifficultyLevel.HARD

        route = RouteCreate(
            name=data.parsed_name or data.name,
            city=data.city or "未知",
            difficulty=difficulty,
            distance_km=stats["distance_km"],
            elevation_gain_m=stats["elevation_gain_m"],
            elevation_loss_m=stats["elevation_loss_m"],
            duration_hours=stats["duration_hours"],
            description=data.description,
            tags=data.tags,
            gpx_points=data.gpx_points,
        )
        return await self.create_route(route)

    async def create_from_track(self, data: TrackUploadRequest) -> dict:
        stats = self._calc_gpx_stats(data.gpx_points)

        difficulty = data.difficulty or DifficultyLevel.MODERATE
        if stats["distance_km"] > 30 or stats["elevation_gain_m"] > 2000:
            difficulty = DifficultyLevel.EXPERT
        elif stats["distance_km"] > 20 or stats["elevation_gain_m"] > 1000:
            difficulty = DifficultyLevel.HARD

        route = RouteCreate(
            name=data.name,
            city=data.city or "未知",
            difficulty=difficulty,
            distance_km=stats["distance_km"],
            elevation_gain_m=stats["elevation_gain_m"],
            elevation_loss_m=stats["elevation_loss_m"],
            duration_hours=stats["duration_hours"],
            description=data.description,
            tags=data.tags,
            gpx_points=data.gpx_points,
            images=data.images,
        )
        return await self.create_route(route)

    async def count_routes(self, query: RouteSearchQuery) -> int:
        collection = await self._get_collection()
        filter_doc: dict = {}
        if query.city:
            filter_doc["city"] = query.city
        if query.difficulty:
            filter_doc["difficulty"] = query.difficulty.value
        return await collection.count_documents(filter_doc)
