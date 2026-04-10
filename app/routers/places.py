from typing import Annotated, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Place, Project
from ..schemas import PlaceCreate, PlaceResponse, PlaceUpdate
from ..services import artwork_api

router = APIRouter(prefix="/projects/{project_id}/places", tags=["places"])

DB = Annotated[Session, Depends(get_db)]


# Helpers

def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _get_place_or_404(db: Session, project_id: int, place_id: int) -> Place:
    place = db.query(Place).filter(Place.id == place_id, Place.project_id == project_id).first()
    if not place:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Place not found")
    return place


def _sync_project_completed(project: Project) -> None:
    if not project.places:
        project.is_completed = False
    else:
        project.is_completed = all(p.is_visited for p in project.places)


async def _resolve_artwork(external_id: int) -> dict:
    try:
        data = await artwork_api.get_artwork(external_id)
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Could not reach the Art Institute API: {exc}",
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Art Institute API returned an error: {exc.response.status_code}",
        )

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Artwork with external_id={external_id} does not exist in the Art Institute API",
        )

    return artwork_api.extract_place_info(data)


# ENDPOINTS

@router.post("", response_model=PlaceResponse, status_code=status.HTTP_201_CREATED)
async def add_place(project_id: int, payload: PlaceCreate, db: DB):
    """
    Add a place (artwork) to an existing project.

    - Validates the artwork exists in the Art Institute of Chicago API.
    - Enforces the 10-place maximum.
    - Prevents duplicate external IDs within the same project.
    """
    project = _get_project_or_404(db, project_id)

    if len(project.places) >= 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A project cannot have more than 10 places",
        )

    info = await _resolve_artwork(payload.external_id)

    place = Place(project_id=project_id, external_id=payload.external_id, **info)
    db.add(place)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This place is already in the project",
        )

    db.refresh(place)
    return place


@router.get("", response_model=List[PlaceResponse])
def list_places(project_id: int, db: DB):
    """List all places for a project."""
    _get_project_or_404(db, project_id)
    return db.query(Place).filter(Place.project_id == project_id).order_by(Place.created_at.asc()).all()


@router.get("/{place_id}", response_model=PlaceResponse)
def get_place(project_id: int, place_id: int, db: DB):
    """Get a single place within a project."""
    _get_project_or_404(db, project_id)
    return _get_place_or_404(db, project_id, place_id)


@router.patch("/{place_id}", response_model=PlaceResponse)
def update_place(project_id: int, place_id: int, payload: PlaceUpdate, db: DB):
    """
    Update a place's notes and/or visited status.

    When all places in a project are marked as visited the project is
    automatically marked as completed.
    """
    project = _get_project_or_404(db, project_id)
    place = _get_place_or_404(db, project_id, place_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(place, field, value)

    _sync_project_completed(project)

    db.commit()
    db.refresh(place)
    return place
