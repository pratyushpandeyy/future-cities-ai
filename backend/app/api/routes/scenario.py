from fastapi import APIRouter

from app.models.schemas import (
    ScenarioCompareRequest,
    ScenarioCompareResponse,
    ScenarioScoreRequest,
    ScenarioScoreResponse,
)
from app.services.simulation import compare_scenarios, score_scenario

router = APIRouter(prefix="/api/scenario", tags=["scenario"])


@router.post("/score", response_model=ScenarioScoreResponse)
def scenario_score(payload: ScenarioScoreRequest) -> ScenarioScoreResponse:
    return score_scenario(payload)


@router.post("/compare", response_model=ScenarioCompareResponse)
def scenario_compare(payload: ScenarioCompareRequest) -> ScenarioCompareResponse:
    return compare_scenarios(payload)
