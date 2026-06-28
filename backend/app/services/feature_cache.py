import hashlib
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError

from app.db.models import ClimateFeatureCache
from app.db.session import Base, SessionLocal, engine, is_database_configured
from app.models.schemas import (
    ClimateFeatureCacheRecord,
    ClimateFeatureCacheStats,
    ClimateFeatureVector,
)
from app.services.feature_engineering import FEATURE_SCHEMA_VERSION
from app.services.feature_harvesting import (
    count_fallback_rows,
    count_high_completeness_rows,
    count_locations,
    count_real_data_rows,
    numeric_features,
)
from app.services.ml_targets import TARGET_SOURCE, derive_training_targets
from app.services.ml_training import FEATURE_NAMES


def cache_feature_vector(
    vector: ClimateFeatureVector,
    *,
    climate_scenario: str,
    climate_model: str | None,
) -> bool:
    if not is_database_configured() or SessionLocal is None or engine is None:
        return False

    Base.metadata.create_all(bind=engine)
    cache_key = build_feature_cache_key(
        vector,
        climate_scenario=climate_scenario,
        climate_model=climate_model,
    )

    try:
        with SessionLocal() as session:
            record = (
                session.query(ClimateFeatureCache)
                .filter(ClimateFeatureCache.cache_key == cache_key)
                .one_or_none()
            )

            if record is None:
                record = ClimateFeatureCache(cache_key=cache_key)
                session.add(record)

            record.query = vector.input_query
            record.resolved_name = vector.resolved_name
            record.latitude = vector.latitude
            record.longitude = vector.longitude
            record.year = vector.year
            record.warming_level = vector.warming_level
            record.season = vector.season
            record.time_of_day = vector.time_of_day
            record.climate_scenario = climate_scenario
            record.climate_model = climate_model
            record.climate_region_type = vector.climate_region_type
            record.data_completeness = vector.data_completeness
            record.confidence = vector.confidence
            record.fallback_feature_names = vector.fallback_feature_names
            record.feature_vector_json = vector.model_dump(mode="json")

            session.commit()
            return True
    except SQLAlchemyError:
        return False


def build_feature_cache_key(
    vector: ClimateFeatureVector,
    *,
    climate_scenario: str,
    climate_model: str | None,
) -> str:
    payload = {
        "query": vector.input_query.strip().lower(),
        "lat": round(vector.latitude, 5),
        "lon": round(vector.longitude, 5),
        "year": vector.year,
        "warming": round(vector.warming_level, 3),
        "season": vector.season.strip().lower(),
        "time": vector.time_of_day.strip().lower(),
        "scenario": climate_scenario,
        "model": climate_model or "",
    }
    encoded = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def list_feature_cache_records(limit: int = 100) -> list[ClimateFeatureCacheRecord]:
    if not is_database_configured() or SessionLocal is None:
        return []

    with SessionLocal() as session:
        records = (
            session.query(ClimateFeatureCache)
            .order_by(ClimateFeatureCache.updated_at.desc())
            .limit(limit)
            .all()
        )

    return [
        ClimateFeatureCacheRecord(
            id=record.id,
            cache_key=record.cache_key,
            query=record.query,
            resolved_name=record.resolved_name,
            latitude=record.latitude,
            longitude=record.longitude,
            year=record.year,
            warming_level=record.warming_level,
            season=record.season,
            climate_scenario=record.climate_scenario,
            climate_model=record.climate_model,
            climate_region_type=record.climate_region_type,
            data_completeness=record.data_completeness,
            confidence=record.confidence,
            fallback_feature_count=len(record.fallback_feature_names),
            updated_at=record.updated_at,
        )
        for record in records
    ]


def feature_cache_stats() -> ClimateFeatureCacheStats:
    rows = feature_cache_training_rows()
    return ClimateFeatureCacheStats(
        cached_feature_count=len(rows),
        location_count=count_locations(rows),
        fallback_row_count=count_fallback_rows(rows),
        real_data_row_count=count_real_data_rows(rows),
        high_completeness_row_count=count_high_completeness_rows(rows),
    )


def export_feature_cache_training_dataset(output_path: Path) -> dict[str, object]:
    rows = feature_cache_training_rows()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dataset_name": "Future Cities AI cached feature training dataset v1",
        "created_at": datetime.utcnow().isoformat(),
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_names": FEATURE_NAMES,
        "training_source": "cached_api_feature_vectors_with_raster_anchored_proxy_targets",
        "target_source": TARGET_SOURCE,
        "rows": rows,
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return {
        "output_path": str(output_path),
        "row_count": len(rows),
        "location_count": count_locations(rows),
        "fallback_row_count": count_fallback_rows(rows),
        "real_data_row_count": count_real_data_rows(rows),
        "high_completeness_row_count": count_high_completeness_rows(rows),
    }


def feature_cache_training_rows() -> list[dict[str, object]]:
    if not is_database_configured() or SessionLocal is None:
        return []

    with SessionLocal() as session:
        records = session.query(ClimateFeatureCache).all()

    rows = []
    for record in records:
        vector = ClimateFeatureVector.model_validate(record.feature_vector_json)
        features = numeric_features(vector.features)
        rows.append(
            {
                "metadata": {
                    "location": vector.input_query,
                    "resolved_name": vector.resolved_name,
                    "latitude": vector.latitude,
                    "longitude": vector.longitude,
                    "resolution_level": vector.resolution_level,
                    "climate_region_type": vector.climate_region_type,
                    "year": vector.year,
                    "warming_level": vector.warming_level,
                    "season": vector.season,
                    "time_of_day": vector.time_of_day,
                    "data_completeness": vector.data_completeness,
                    "confidence": vector.confidence,
                    "fallback_feature_names": vector.fallback_feature_names,
                },
                "features": features,
                "targets": derive_training_targets(
                    features,
                    data_completeness=vector.data_completeness,
                ),
                "target_source": TARGET_SOURCE,
            },
        )

    return rows
