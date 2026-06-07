from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    EXPERT = "expert"


class GPSPoint(BaseModel):
    lat: float
    lng: float
    elevation: Optional[float] = None
    timestamp: Optional[datetime] = None


class RouteCreate(BaseModel):
    name: str
    city: str
    difficulty: DifficultyLevel
    distance_km: float
    elevation_gain_m: Optional[float] = 0
    elevation_loss_m: Optional[float] = 0
    duration_hours: Optional[float] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    gpx_points: list[GPSPoint] = Field(default_factory=list)
    pois: list[str] = Field(default_factory=list)
    cover_image: Optional[str] = None
    images: list[str] = Field(default_factory=list)


class RouteResponse(RouteCreate):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True


class RouteSearchQuery(BaseModel):
    city: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    min_distance: Optional[float] = None
    max_distance: Optional[float] = None
    tags: Optional[list[str]] = None
    keyword: Optional[str] = None
    limit: int = 10
    offset: int = 0


class GPXUploadRequest(BaseModel):
    name: str
    parsed_name: Optional[str] = None
    city: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    gpx_points: list[GPSPoint]


class TrackUploadRequest(BaseModel):
    name: str
    city: Optional[str] = None
    difficulty: Optional[DifficultyLevel] = None
    description: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
    gpx_points: list[GPSPoint]
    images: list[str] = Field(default_factory=list)
