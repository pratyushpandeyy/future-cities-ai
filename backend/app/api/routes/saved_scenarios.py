from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, is_database_configured
from app.models.schemas import SavedScenarioCreate, SavedScenarioResponse
from app.services.saved_scenarios import (
    create_saved_scenario,
    delete_saved_scenario,
    get_saved_scenario,
    list_saved_scenarios,
)


router = APIRouter(prefix="/api/scenarios", tags=["saved scenarios"])


def get_saved_scenario_session() -> Generator[Session, None, None]:
    if not is_database_configured() or SessionLocal is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured for saved scenarios",
        )

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()


@router.post("/save", response_model=SavedScenarioResponse)
def save_scenario(
    payload: SavedScenarioCreate,
    session: Session = Depends(get_saved_scenario_session),
) -> SavedScenarioResponse:
    return create_saved_scenario(session, payload)


@router.get("", response_model=list[SavedScenarioResponse])
def scenarios(
    session: Session = Depends(get_saved_scenario_session),
) -> list[SavedScenarioResponse]:
    return list_saved_scenarios(session)


@router.get("/{scenario_id}", response_model=SavedScenarioResponse)
def scenario(
    scenario_id: int,
    session: Session = Depends(get_saved_scenario_session),
) -> SavedScenarioResponse:
    return get_saved_scenario(session, scenario_id)


@router.delete("/{scenario_id}")
def delete_scenario(
    scenario_id: int,
    session: Session = Depends(get_saved_scenario_session),
) -> dict[str, bool]:
    return delete_saved_scenario(session, scenario_id)
