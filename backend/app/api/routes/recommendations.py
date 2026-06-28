from fastapi import APIRouter

from app.models.schemas import (
    CandidateScreenRequest,
    CandidateScreenResponse,
    RecommendationRequest,
    RecommendationResponse,
)
from app.services.recommendation_engine import generate_recommendations
from app.services.recommendation_engine import screen_candidate_locations


router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.post("", response_model=RecommendationResponse)
def recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    return generate_recommendations(payload)


@router.post("/screen", response_model=CandidateScreenResponse)
def screen_candidates(payload: CandidateScreenRequest) -> CandidateScreenResponse:
    return screen_candidate_locations(payload)
