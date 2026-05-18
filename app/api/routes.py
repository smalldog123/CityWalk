from fastapi import APIRouter, HTTPException
from app.models.route import RouteCreate, RouteSearchQuery
from app.services.route_service import RouteService

router = APIRouter(prefix="/routes", tags=["routes"])
route_service = RouteService()


@router.post("/", summary="创建路线")
async def create_route(route: RouteCreate):
    result = await route_service.create_route(route)
    return result


@router.get("/{route_id}", summary="获取路线详情")
async def get_route(route_id: str):
    result = await route_service.get_route(route_id)
    if not result:
        raise HTTPException(status_code=404, detail="Route not found")
    return result


@router.post("/search", summary="搜索路线")
async def search_routes(query: RouteSearchQuery):
    routes = await route_service.search_routes(query)
    total = await route_service.count_routes(query)
    return {"routes": routes, "total": total}


@router.get("/", summary="获取路线列表")
async def list_routes(limit: int = 20, offset: int = 0):
    routes = await route_service.list_routes(limit, offset)
    return {"routes": routes}
