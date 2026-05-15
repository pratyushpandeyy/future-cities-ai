from fastapi import APIRouter

from app.models.schemas import RegionBoundaryResponse
from app.services.simulation import region_boundary

router = APIRouter(prefix="/api", tags=["region"])


@router.get("/region-boundary", response_model=RegionBoundaryResponse)
def get_region_boundary(location: str) -> RegionBoundaryResponse:
    return region_boundary(location)
