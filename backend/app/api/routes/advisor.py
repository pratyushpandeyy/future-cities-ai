from fastapi import APIRouter

from app.models.schemas import AdvisorQueryRequest, AdvisorResponse
from app.services.advisor_engine import answer_advisor_query


router = APIRouter(prefix="/api/advisor", tags=["advisor"])


@router.post("/query", response_model=AdvisorResponse)
def advisor_query(payload: AdvisorQueryRequest) -> AdvisorResponse:
    return answer_advisor_query(payload)
