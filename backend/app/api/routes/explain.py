from fastapi import APIRouter

from app.models.schemas import ExplanationRequest, ExplanationResponse
from app.services.ai_explanation import explain_climate_impact


router = APIRouter(prefix="/api", tags=["explain"])


@router.post("/explain", response_model=ExplanationResponse)
def explain(payload: ExplanationRequest) -> ExplanationResponse:
    return explain_climate_impact(payload)
