from fastapi import APIRouter

from app.models.schemas import RegionBoundaryResponse
from app.services.boundaries import get_region_boundary as load_region_boundary

router = APIRouter(prefix="/api", tags=["region"])


@router.get("/region-boundary", response_model=RegionBoundaryResponse)
def get_region_boundary(location: str) -> RegionBoundaryResponse:
    return load_region_boundary(location)
