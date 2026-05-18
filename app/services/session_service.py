from __future__ import annotations
from typing import Any
from datetime import datetime
from app.core.database import get_database
from app.models.session import ChatMessage


class SessionService:
    def __init__(self):
        self._db: Any = None

    async def _get_collection(self):
        if self._db is None:
            self._db = await get_database()
        return self._db.sessions

    async def get_or_create_session(self, session_id: str, user_id: str) -> dict:
        collection = await self._get_collection()
        session = await collection.find_one({"session_id": session_id})
        if session:
            session["_id"] = str(session["_id"])
            return session
        now = datetime.utcnow()
        doc = {
            "session_id": session_id,
            "user_id": user_id,
            "messages": [],
            "created_at": now,
            "updated_at": now,
        }
        result = await collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def get_messages(self, session_id: str) -> list[dict]:
        collection = await self._get_collection()
        session = await collection.find_one({"session_id": session_id})
        if not session:
            return []
        return session.get("messages", [])

    async def add_message(self, session_id: str, message: ChatMessage):
        collection = await self._get_collection()
        now = datetime.utcnow()
        msg_doc = message.model_dump(exclude_none=True)
        await collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": msg_doc},
                "$set": {"updated_at": now},
            },
        )

    async def add_messages(self, session_id: str, messages: list[ChatMessage]):
        collection = await self._get_collection()
        now = datetime.utcnow()
        msg_docs = [m.model_dump(exclude_none=True) for m in messages]
        await collection.update_one(
            {"session_id": session_id},
            {
                "$push": {"messages": {"$each": msg_docs}},
                "$set": {"updated_at": now},
            },
        )

    async def clear_session(self, session_id: str):
        collection = await self._get_collection()
        now = datetime.utcnow()
        await collection.update_one(
            {"session_id": session_id},
            {"$set": {"messages": [], "updated_at": now}},
        )
