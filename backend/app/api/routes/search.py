from fastapi import APIRouter

from app.models.schemas import LocationResult
from app.services.simulation import search_location

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=LocationResult)
def search(query: str) -> LocationResult:
    return search_location(query)
