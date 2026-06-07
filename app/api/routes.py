import os
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File
from app.models.route import RouteCreate, RouteSearchQuery, GPXUploadRequest, TrackUploadRequest
from app.services.route_service import RouteService

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")

router = APIRouter(prefix="/routes", tags=["routes"])
route_service = RouteService()


@router.post("/upload-image", summary="上传路线图片")
async def upload_image(file: UploadFile = File(...)):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="仅支持上传图片文件")
    ext = os.path.splitext(file.filename or "image.jpg")[1] or ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过10MB")
    with open(filepath, "wb") as f:
        f.write(content)
    return {"url": f"/uploads/{filename}"}


@router.post("/upload-gpx", summary="上传GPX文件创建路线")
async def upload_gpx(data: GPXUploadRequest):
    if not data.gpx_points or len(data.gpx_points) < 2:
        raise HTTPException(status_code=400, detail="GPX 轨迹点不足，至少需要 2 个点")
    result = await route_service.create_from_gpx(data)
    return result


@router.post("/upload-track", summary="上传实时记录路线")
async def upload_track(data: TrackUploadRequest):
    if not data.gpx_points or len(data.gpx_points) < 2:
        raise HTTPException(status_code=400, detail="轨迹点不足，至少需要 2 个点")
    result = await route_service.create_from_track(data)
    return result


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
