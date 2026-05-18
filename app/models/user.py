from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.route import DifficultyLevel


class UserPreference(BaseModel):
    cities: list[str] = Field(default_factory=list)
    difficulties: list[DifficultyLevel] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    avg_distance: Optional[float] = None


class UserCreate(BaseModel):
    user_id: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    preference: UserPreference = Field(default_factory=UserPreference)
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
