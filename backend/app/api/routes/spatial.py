from fastapi import APIRouter

from app.models.schemas import SpatialResolveRequest, SpatialResolutionResponse
from app.services.spatial_resolution import resolve_spatial_context


router = APIRouter(prefix="/api/spatial", tags=["spatial"])


@router.post("/resolve", response_model=SpatialResolutionResponse)
def resolve_spatial_location(
    payload: SpatialResolveRequest,
) -> SpatialResolutionResponse:
    return resolve_spatial_context(payload.query)
