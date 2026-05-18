from __future__ import annotations
import json
from app.services.route_service import RouteService
from app.services.knowledge_service import KnowledgeService
from app.services.user_service import UserService
from app.models.route import RouteSearchQuery, DifficultyLevel
from app.models.user import UserPreference


class ToolExecutor:
    def __init__(self):
        self.route_service = RouteService()
        self.knowledge_service = KnowledgeService()
        self.user_service = UserService()

    async def execute(self, tool_name: str, arguments: dict, user_id: str = None) -> str:
        handler = {
            "search_routes": self._search_routes,
            "search_knowledge": self._search_knowledge,
            "get_user_preference": self._get_user_preference,
            "update_user_preference": self._update_user_preference,
        }.get(tool_name)

        if not handler:
            return json.dumps({"error": f"Unknown tool: {tool_name}"}, ensure_ascii=False)

        try:
            result = await handler(arguments, user_id)
            return json.dumps(result, ensure_ascii=False, default=str)
        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    async def _search_routes(self, args: dict, user_id: str = None) -> dict:
        query = RouteSearchQuery(
            city=args.get("city"),
            difficulty=DifficultyLevel(args["difficulty"]) if args.get("difficulty") else None,
            min_distance=args.get("min_distance"),
            max_distance=args.get("max_distance"),
            tags=args.get("tags"),
            keyword=args.get("keyword"),
            limit=args.get("limit", 10),
            offset=0,
        )
        routes = await self.route_service.search_routes(query)

        if user_id and routes:
            first_route = routes[0]
            await self.user_service.auto_learn_preference(
                user_id=user_id,
                city=first_route.get("city"),
                difficulty=first_route.get("difficulty"),
                tags=first_route.get("tags"),
                distance=first_route.get("distance_km"),
            )

        return {
            "routes": routes,
            "total": len(routes),
        }

    async def _search_knowledge(self, args: dict, user_id: str = None) -> dict:
        query = args.get("query", "")
        search_type = args.get("search_type", "semantic")

        if search_type == "city":
            results = await self.knowledge_service.search_routes_by_city(query)
        elif search_type == "tag":
            results = await self.knowledge_service.search_routes_by_tag(query)
        elif search_type == "poi":
            results = await self.knowledge_service.search_poi_near_route(query)
        elif search_type == "entity":
            entity_type = args.get("entity_type", "Route")
            results = await self.knowledge_service.search_by_entity(entity_type, query)
        else:
            results = await self.knowledge_service.semantic_search(query)

        return {
            "results": results,
            "total": len(results),
        }

    async def _get_user_preference(self, args: dict, user_id: str = None) -> dict:
        uid = args.get("user_id", user_id)
        if not uid:
            return {"error": "user_id is required"}
        preference = await self.user_service.get_user_preference(uid)
        return preference

    async def _update_user_preference(self, args: dict, user_id: str = None) -> dict:
        uid = args.get("user_id", user_id)
        if not uid:
            return {"error": "user_id is required"}

        current = await self.user_service.get_user_preference(uid)
        pref = UserPreference(**current)

        if "cities" in args and args["cities"]:
            pref.cities = args["cities"]
        if "difficulties" in args and args["difficulties"]:
            pref.difficulties = [DifficultyLevel(d) for d in args["difficulties"]]
        if "tags" in args and args["tags"]:
            pref.tags = args["tags"]

        updated = await self.user_service.update_user_preference(uid, pref)
        return updated
