import json
from datetime import UTC, datetime
from pathlib import Path

from app.models.schemas import (
    ClimateFeatureHarvestRequest,
    ClimateFeatureHarvestResponse,
    FeatureBuildRequest,
)
from app.services.feature_engineering import FEATURE_SCHEMA_VERSION, build_climate_feature_vector
from app.services.ml_targets import TARGET_SOURCE, derive_training_targets
from app.services.ml_training import FEATURE_NAMES
from app.services.spatial_resolution import resolve_spatial_context


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FEATURE_DATASET_PATH = (
    BACKEND_ROOT / "data" / "models" / "climate_training_features_v2.json"
)
DEFAULT_HARVEST_LOCATIONS = [
    "Mumbai",
    "Bangalore",
    "Whitefield",
    "Koramangala",
    "Bandra",
    "Chennai",
    "Hyderabad",
    "Delhi",
    "Gurgaon",
    "Noida",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
    "Istanbul",
    "Kadikoy",
    "Madrid",
    "Manchester",
    "London",
    "Chelsea London",
    "Brooklyn",
    "Toronto",
    "Pune",
    "Varanasi",
]


def harvest_climate_training_features(
    payload: ClimateFeatureHarvestRequest,
) -> ClimateFeatureHarvestResponse:
    output_path = Path(payload.output_path) if payload.output_path else DEFAULT_FEATURE_DATASET_PATH

    if output_path.exists() and not payload.overwrite:
        existing = load_harvested_training_rows(output_path)
        return ClimateFeatureHarvestResponse(
            output_path=str(output_path),
            row_count=len(existing),
            location_count=count_locations(existing),
            feature_schema_version=FEATURE_SCHEMA_VERSION,
            training_source="existing_harvested_feature_dataset",
            fallback_row_count=count_fallback_rows(existing),
            real_data_row_count=count_real_data_rows(existing),
            message=(
                "Harvested feature dataset already exists. Pass overwrite=true "
                "to rebuild it from the current data providers."
            ),
        )

    rows = build_harvest_rows(payload)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "dataset_name": "Future Cities AI harvested training features v2",
                "created_at": datetime.now(UTC).isoformat(),
                "feature_schema_version": FEATURE_SCHEMA_VERSION,
                "feature_names": FEATURE_NAMES,
                "training_source": "harvested_feature_vectors_with_raster_anchored_proxy_targets",
                "target_source": TARGET_SOURCE,
                "notes": [
                    "Rows are harvested through the same feature engineering path used by live scenario scoring.",
                    "Feature values may come from local WorldClim rasters, remote providers, environmental providers, or explicit fallback priors.",
                    "Targets are raster/feature-anchored proxy labels until observed urban outcome labels are available.",
                ],
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return ClimateFeatureHarvestResponse(
        output_path=str(output_path),
        row_count=len(rows),
        location_count=count_locations(rows),
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        training_source="harvested_feature_vectors_with_raster_anchored_proxy_targets",
        fallback_row_count=count_fallback_rows(rows),
        real_data_row_count=count_real_data_rows(rows),
        message="Harvested climate feature dataset for ML training.",
    )


def build_harvest_rows(payload: ClimateFeatureHarvestRequest) -> list[dict[str, object]]:
    locations = payload.locations or DEFAULT_HARVEST_LOCATIONS
    rows: list[dict[str, object]] = []

    for location in locations:
        spatial = resolve_spatial_context(location)

        for year in payload.years:
            for warming_level in payload.warming_levels:
                for season in payload.seasons:
                    feature_vector = build_climate_feature_vector(
                        FeatureBuildRequest(
                            query=location,
                            year=year,
                            warming_level=warming_level,
                            season=season,
                            time_of_day=payload.time_of_day,
                            climate_scenario=payload.climate_scenario,
                            climate_model=payload.climate_model,
                        ),
                        spatial=spatial,
                    )
                    features = numeric_features(feature_vector.features)
                    rows.append(
                        {
                            "metadata": {
                                "location": location,
                                "resolved_name": feature_vector.resolved_name,
                                "latitude": feature_vector.latitude,
                                "longitude": feature_vector.longitude,
                                "resolution_level": feature_vector.resolution_level,
                                "climate_region_type": feature_vector.climate_region_type,
                                "year": year,
                                "warming_level": warming_level,
                                "season": season,
                                "time_of_day": payload.time_of_day,
                                "data_completeness": feature_vector.data_completeness,
                                "confidence": feature_vector.confidence,
                                "fallback_feature_names": feature_vector.fallback_feature_names,
                            },
                            "features": features,
                            "targets": derive_training_targets(
                                features,
                                data_completeness=feature_vector.data_completeness,
                            ),
                            "target_source": TARGET_SOURCE,
                        },
                    )

    return rows


def numeric_features(features: dict) -> dict[str, float]:
    values: dict[str, float] = {}

    for feature_name in FEATURE_NAMES:
        feature = features.get(feature_name)
        values[feature_name] = float(feature.value) if feature else default_feature_value(feature_name)

    return values


def default_feature_value(feature_name: str) -> float:
    from app.services.ml_training import FEATURE_DEFAULTS

    return float(FEATURE_DEFAULTS[feature_name])


def load_harvested_training_rows(path: Path | None = None) -> list[dict[str, object]]:
    dataset_path = path or DEFAULT_FEATURE_DATASET_PATH

    if not dataset_path.exists():
        return []

    payload = json.loads(dataset_path.read_text(encoding="utf-8"))
    rows = payload.get("rows", [])

    return rows if isinstance(rows, list) else []


def count_locations(rows: list[dict[str, object]]) -> int:
    locations = {
        str(row.get("metadata", {}).get("location"))
        for row in rows
        if isinstance(row.get("metadata"), dict)
    }
    return len(locations)


def count_fallback_rows(rows: list[dict[str, object]]) -> int:
    return sum(
        1
        for row in rows
        if isinstance(row.get("metadata"), dict)
        and float(row["metadata"].get("data_completeness", 0)) < 0.5
    )


def count_real_data_rows(rows: list[dict[str, object]]) -> int:
    return len(rows) - count_fallback_rows(rows)
