from fastapi import APIRouter

from app.models.schemas import RAGQueryRequest, RAGQueryResponse
from app.services.rag_retrieval import retrieve_climate_knowledge


router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/query", response_model=RAGQueryResponse)
def query_rag(payload: RAGQueryRequest) -> RAGQueryResponse:
    return retrieve_climate_knowledge(payload)
