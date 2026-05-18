from __future__ import annotations
from typing import Optional, Any
from datetime import datetime
from app.core.database import get_database
from app.models.user import UserPreference
from app.models.route import DifficultyLevel


class UserService:
    def __init__(self):
        self._db: Any = None

    async def _get_collection(self):
        if self._db is None:
            self._db = await get_database()
        return self._db.users

    async def get_or_create_user(self, user_id: str, nickname: str = None, avatar: str = None) -> dict:
        collection = await self._get_collection()
        user = await collection.find_one({"user_id": user_id})
        if user:
            user["_id"] = str(user["_id"])
            return user
        now = datetime.utcnow()
        doc = {
            "user_id": user_id,
            "nickname": nickname,
            "avatar": avatar,
            "preference": UserPreference().model_dump(),
            "created_at": now,
            "updated_at": now,
        }
        result = await collection.insert_one(doc)
        doc["_id"] = str(result.inserted_id)
        return doc

    async def get_user_preference(self, user_id: str) -> dict:
        collection = await self._get_collection()
        user = await collection.find_one({"user_id": user_id})
        if not user:
            return UserPreference().model_dump()
        return user.get("preference", UserPreference().model_dump())

    async def update_user_preference(self, user_id: str, preference: UserPreference) -> dict:
        collection = await self._get_collection()
        now = datetime.utcnow()
        await collection.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "preference": preference.model_dump(),
                    "updated_at": now,
                }
            },
            upsert=True,
        )
        return preference.model_dump()

    async def auto_learn_preference(self, user_id: str, city: str = None, difficulty: str = None, tags: list[str] = None, distance: float = None):
        current = await self.get_user_preference(user_id)
        pref = UserPreference(**current)

        if city and city not in pref.cities:
            pref.cities.append(city)
            if len(pref.cities) > 5:
                pref.cities = pref.cities[-5:]

        if difficulty:
            try:
                diff = DifficultyLevel(difficulty)
                if diff not in pref.difficulties:
                    pref.difficulties.append(diff)
            except ValueError:
                pass

        if tags:
            for tag in tags:
                if tag not in pref.tags:
                    pref.tags.append(tag)
            if len(pref.tags) > 10:
                pref.tags = pref.tags[-10:]

        if distance is not None:
            if pref.avg_distance is None:
                pref.avg_distance = distance
            else:
                pref.avg_distance = round((pref.avg_distance + distance) / 2, 1)

        return await self.update_user_preference(user_id, pref)
