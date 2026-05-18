from fastapi import APIRouter
from app.core.database import get_database
from app.core.graph_db import get_falkordb_graph

router = APIRouter(tags=["health"])


@router.get("/health", summary="健康检查")
async def health_check():
    status = {"status": "ok", "services": {}}

    try:
        db = await get_database()
        await db.command("ping")
        status["services"]["mongodb"] = "ok"
    except Exception as e:
        status["services"]["mongodb"] = f"error: {str(e)}"

    try:
        graph = get_falkordb_graph()
        graph.query("RETURN 1")
        status["services"]["falkordb"] = "ok"
    except Exception as e:
        status["services"]["falkordb"] = f"error: {str(e)}"

    return status
