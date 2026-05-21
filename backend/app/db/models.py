from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AdministrativeBoundary(Base):
    __tablename__ = "administrative_boundaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    aliases: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    region_type: Mapped[str] = mapped_column(String(80), nullable=False, default="region")
    climate_region_type: Mapped[str] = mapped_column(String(80), nullable=False, default="continental")
    source: Mapped[str] = mapped_column(String(120), nullable=False, default="local_seed_geojson")
    geometry_geojson: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class SavedScenario(Base):
    __tablename__ = "saved_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    location_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(255), nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    warming_level: Mapped[float] = mapped_column(Float, nullable=False)
    season: Mapped[str] = mapped_column(String(80), nullable=False)
    time_of_day: Mapped[str] = mapped_column(String(80), nullable=False)
    active_layer: Mapped[str] = mapped_column(String(120), nullable=False)
    livability_score: Mapped[int] = mapped_column(Integer, nullable=False)
    heat_risk: Mapped[str] = mapped_column(String(80), nullable=False)
    flood_risk: Mapped[str] = mapped_column(String(80), nullable=False)
    outdoor_comfort: Mapped[str] = mapped_column(String(80), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
