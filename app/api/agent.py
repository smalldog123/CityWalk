import json
import logging
from fastapi import APIRouter
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from app.agent.engine import AgentEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])
agent_engine = AgentEngine()


class ChatRequest(BaseModel):
    session_id: str
    user_id: str
    message: str


@router.post("/chat", summary="Agent对话（非流式）")
async def chat(request: ChatRequest):
    full_response = ""
    routes = []
    error = None

    async for event in agent_engine.chat(
        session_id=request.session_id,
        user_id=request.user_id,
        question=request.message,
    ):
        if event["type"] == "text":
            full_response += event["content"]
        elif event["type"] == "route_recommendations":
            routes = event["routes"]
        elif event["type"] == "error":
            error = event["content"]

    if error and not full_response:
        return {
            "response": error,
            "routes": [],
            "session_id": request.session_id,
            "is_error": True,
        }

    return {
        "response": full_response,
        "routes": routes,
        "session_id": request.session_id,
    }


@router.post("/chat/stream", summary="Agent对话（SSE流式）")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        try:
            async for event in agent_engine.chat(
                session_id=request.session_id,
                user_id=request.user_id,
                question=request.message,
            ):
                yield {
                    "event": event["type"],
                    "data": json.dumps(event, ensure_ascii=False, default=str),
                }
        except Exception as e:
            logger.error(f"SSE stream error: {e}", exc_info=True)
            yield {
                "event": "error",
                "data": json.dumps({
                    "type": "error",
                    "content": "智能助手暂时无法响应，请稍后重试。",
                }, ensure_ascii=False),
            }

    return EventSourceResponse(event_generator())


@router.get("/sessions/{session_id}/history", summary="获取会话历史")
async def get_session_history(session_id: str):
    session_service = agent_engine.session_service
    session = await session_service.get_or_create_session(session_id, "unknown")
    return {
        "session_id": session_id,
        "messages": session.get("messages", []),
    }


@router.delete("/sessions/{session_id}", summary="清除会话历史")
async def clear_session(session_id: str):
    session_service = agent_engine.session_service
    await session_service.clear_session(session_id)
    return {"message": "Session cleared"}
