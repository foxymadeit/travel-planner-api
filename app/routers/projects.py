from typing import Annotated, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Place, Project
from ..schemas import (
    ProjectCreate,
    ProjectListItem,
    ProjectResponse,
    ProjectUpdate,
)
from ..services import artwork_api

router = APIRouter(prefix="/projects", tags=["projects"])

DB = Annotated[Session, Depends(get_db)]


# ── helpers ────────────────────────────────────────────────────────────────────

def _get_or_404(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def _resolve_place(external_id: int) -> dict:
    """Fetch artwork from external API; raise 422 if not found or API errors."""
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

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(payload: ProjectCreate, db: DB):
    """
    Create a travel project.  Optionally include an array of ``place_ids``
    (artwork IDs from the Art Institute of Chicago) to seed the project with
    places in a single request.
    """
    place_ids = payload.place_ids or []

    if len(place_ids) > 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A project can have at most 10 places",
        )

    # Validate & fetch all places upfront so we fail before writing anything.
    place_infos = []
    for eid in place_ids:
        info = await _resolve_place(eid)
        place_infos.append((eid, info))

    project = Project(
        name=payload.name,
        description=payload.description,
        start_date=payload.start_date,
    )
    db.add(project)
    db.flush()  

    for external_id, info in place_infos:
        db.add(Place(project_id=project.id, external_id=external_id, **info))

    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=List[ProjectListItem])
def list_projects(db: DB):
    """List all travel projects."""
    projects = db.query(Project).order_by(Project.created_at.desc()).all()
    return [
        ProjectListItem(
            **{c.name: getattr(p, c.name) for c in Project.__table__.columns},
            place_count=len(p.places),
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: DB):
    """Get a single travel project including its places."""
    return _get_or_404(db, project_id)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, payload: ProjectUpdate, db: DB):
    """Update a project's name, description, or start date."""
    project = _get_or_404(db, project_id)

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: DB):
    """
    Delete a travel project.
    Returns 409 Conflict if any of its places are already marked as visited.
    """
    project = _get_or_404(db, project_id)

    if any(p.is_visited for p in project.places):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a project that has visited places",
        )

    db.delete(project)
    db.commit()
