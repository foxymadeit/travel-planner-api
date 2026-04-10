from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import date, datetime


# Place schemas 

class PlaceCreate(BaseModel):
    external_id: int = Field(..., description="Artwork ID from the Art Institute of Chicago API")


class PlaceUpdate(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=5000)
    is_visited: Optional[bool] = None


class PlaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    external_id: int
    title: str
    artist: Optional[str] = None
    thumbnail_url: Optional[str] = None
    notes: Optional[str] = None
    is_visited: bool
    created_at: datetime
    updated_at: datetime


# Project schemas 

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    start_date: Optional[date] = None
    place_ids: Optional[List[int]] = Field(
        default=None,
        description="Optional list of artwork IDs to add at creation (max 10)",
    )

    @field_validator("place_ids")
    @classmethod
    def validate_place_ids(cls, v: Optional[List[int]]) -> Optional[List[int]]:
        if v is not None:
            if len(v) > 10:
                raise ValueError("A project can have at most 10 places")
            if len(v) != len(set(v)):
                raise ValueError("Duplicate place IDs are not allowed")
        return v


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    start_date: Optional[date] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    is_completed: bool
    places: List[PlaceResponse] = []
    created_at: datetime
    updated_at: datetime


class ProjectListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    is_completed: bool
    place_count: int
    created_at: datetime
    updated_at: datetime
