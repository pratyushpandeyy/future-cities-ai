from fastapi import APIRouter

from app.models.schemas import RecommendationRequest, RecommendationResponse
from app.services.recommendation_engine import generate_recommendations


router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
def recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    return generate_recommendations(payload)
