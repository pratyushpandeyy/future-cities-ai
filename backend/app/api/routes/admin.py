from fastapi import APIRouter, HTTPException

from app.models.schemas import AdminBoundaryDetail, AdminBoundarySummary
from app.services.boundaries import (
    get_database_boundary_detail,
    list_database_boundaries,
)


router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/boundaries", response_model=list[AdminBoundarySummary])
def get_boundaries() -> list[AdminBoundarySummary]:
    return list_database_boundaries()


@router.get("/boundaries/{boundary_id}", response_model=AdminBoundaryDetail)
def get_boundary(boundary_id: int) -> AdminBoundaryDetail:
    boundary = get_database_boundary_detail(boundary_id)

    if not boundary:
        raise HTTPException(status_code=404, detail="Boundary not found")

    return boundary
