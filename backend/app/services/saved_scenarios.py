from fastapi import HTTPException
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import SavedScenario
from app.db.session import Base, engine, is_database_configured
from app.models.schemas import SavedScenarioCreate, SavedScenarioResponse


def ensure_saved_scenario_table() -> None:
    if not is_database_configured() or engine is None:
        raise HTTPException(
            status_code=503,
            detail="Database is not configured for saved scenarios",
        )

    Base.metadata.create_all(bind=engine, tables=[SavedScenario.__table__])


def create_saved_scenario(
    session: Session,
    payload: SavedScenarioCreate,
) -> SavedScenarioResponse:
    ensure_saved_scenario_table()
    scenario = SavedScenario(**payload.model_dump())

    try:
        session.add(scenario)
        session.commit()
        session.refresh(scenario)
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Could not save scenario") from exc

    return saved_scenario_to_response(scenario)


def list_saved_scenarios(session: Session) -> list[SavedScenarioResponse]:
    ensure_saved_scenario_table()
    scenarios = (
        session.query(SavedScenario)
        .order_by(desc(SavedScenario.created_at))
        .limit(50)
        .all()
    )

    return [saved_scenario_to_response(scenario) for scenario in scenarios]


def get_saved_scenario(session: Session, scenario_id: int) -> SavedScenarioResponse:
    ensure_saved_scenario_table()
    scenario = session.get(SavedScenario, scenario_id)

    if not scenario:
        raise HTTPException(status_code=404, detail="Saved scenario not found")

    return saved_scenario_to_response(scenario)


def delete_saved_scenario(session: Session, scenario_id: int) -> dict[str, bool]:
    ensure_saved_scenario_table()
    scenario = session.get(SavedScenario, scenario_id)

    if not scenario:
        raise HTTPException(status_code=404, detail="Saved scenario not found")

    try:
        session.delete(scenario)
        session.commit()
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Could not delete scenario") from exc

    return {"deleted": True}


def saved_scenario_to_response(scenario: SavedScenario) -> SavedScenarioResponse:
    return SavedScenarioResponse(
        id=scenario.id,
        name=scenario.name,
        location_name=scenario.location_name,
        region=scenario.region,
        latitude=scenario.latitude,
        longitude=scenario.longitude,
        year=scenario.year,
        warming_level=scenario.warming_level,
        season=scenario.season,
        time_of_day=scenario.time_of_day,
        active_layer=scenario.active_layer,
        livability_score=scenario.livability_score,
        heat_risk=scenario.heat_risk,
        flood_risk=scenario.flood_risk,
        outdoor_comfort=scenario.outdoor_comfort,
        created_at=scenario.created_at,
    )
