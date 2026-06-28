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


class Place(Base):
    __tablename__ = "places"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    provider_key: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    place_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="location",
        index=True,
    )
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    locality: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    region: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    hierarchy_label: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    bbox: Mapped[list[float] | None] = mapped_column(JSON, nullable=True)
    geocoder_provider: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="unknown",
        index=True,
    )
    provider_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    point_geojson: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class ClimateDataset(Base):
    __tablename__ = "climate_datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    storage_uri: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    data_format: Mapped[str] = mapped_column(String(80), nullable=False)
    spatial_resolution: Mapped[str | None] = mapped_column(String(120), nullable=True)
    temporal_resolution: Mapped[str | None] = mapped_column(String(120), nullable=True)
    start_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    variables: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    scenarios: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    geographic_coverage: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="global",
    )
    status: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
        default="planned",
        index=True,
    )
    license_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    attribution: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class ClimateFeatureCache(Base):
    __tablename__ = "climate_feature_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    cache_key: Mapped[str] = mapped_column(
        String(700),
        unique=True,
        nullable=False,
        index=True,
    )
    query: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    resolved_name: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    warming_level: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    season: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    time_of_day: Mapped[str] = mapped_column(String(80), nullable=False)
    climate_scenario: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    climate_model: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    climate_region_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    data_completeness: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    confidence: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    fallback_feature_names: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    feature_vector_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
