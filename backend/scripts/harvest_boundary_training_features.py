"""Harvest ML training rows directly from imported boundary records.

This script is for scaling beyond the hand-picked demo locations. It samples
representative points from administrative boundary polygons already loaded into
the database, then sends those points through the same feature engineering path
used by the live scenario APIs.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.db.models import AdministrativeBoundary  # noqa: E402
from app.db.session import SessionLocal, is_database_configured  # noqa: E402
from app.models.schemas import (  # noqa: E402
    FeatureBuildRequest,
    LocationResult,
    SpatialResolutionResponse,
)
from app.services.climate_data.climate_raster_service import sample_climate_raster  # noqa: E402
from app.services.feature_engineering import (  # noqa: E402
    FEATURE_SCHEMA_VERSION,
    build_climate_feature_vector,
)
from app.services.feature_harvesting import (  # noqa: E402
    count_fallback_rows,
    count_high_completeness_rows,
    count_locations,
    count_real_data_rows,
    numeric_features,
)
from app.services.ml_targets import TARGET_SOURCE, derive_training_targets  # noqa: E402
from app.services.ml_training import FEATURE_NAMES  # noqa: E402


DEFAULT_OUTPUT_PATH = (
    BACKEND_ROOT / "data" / "models" / "boundary_training_features_v1.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a broader climate ML training table from imported boundary "
            "polygons instead of a tiny fixed city list."
        ),
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--limit", type=int, default=1200)
    parser.add_argument("--per-country", type=int, default=20)
    parser.add_argument("--year", action="append", type=int, dest="years", default=[])
    parser.add_argument(
        "--warming",
        action="append",
        type=float,
        dest="warming_levels",
        default=[],
    )
    parser.add_argument("--season", action="append", dest="seasons", default=[])
    parser.add_argument("--scenario", default="ssp245")
    parser.add_argument("--model", default=None)
    parser.add_argument("--time-of-day", default="Afternoon")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not is_database_configured() or SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured. Add it to backend/.env first.")

    output_path = args.output.resolve()

    if output_path.exists() and not args.overwrite:
        raise FileExistsError(f"{output_path} exists. Pass --overwrite to rebuild it.")

    boundary_samples = load_boundary_samples(
        limit=args.limit,
        per_country=args.per_country,
    )
    rows = build_rows(
        boundary_samples,
        years=args.years or [2030, 2050, 2070],
        warming_levels=args.warming_levels or [1.7, 2.7, 3.5],
        seasons=args.seasons or ["Summer", "Monsoon", "Winter"],
        time_of_day=args.time_of_day,
        scenario=args.scenario,
        model=args.model,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "dataset_name": "Future Cities AI boundary-derived training features v1",
                "created_at": datetime.now(UTC).isoformat(),
                "feature_schema_version": FEATURE_SCHEMA_VERSION,
                "feature_names": FEATURE_NAMES,
                "training_source": "database_boundary_centroids_with_raster_anchored_proxy_targets",
                "target_source": TARGET_SOURCE,
                "boundary_sample_count": len(boundary_samples),
                "notes": [
                    "Rows are sampled from imported administrative boundary polygons.",
                    "Representative points are bbox centers, not population-weighted centroids.",
                    "Targets remain raster/feature-anchored proxy labels until observed outcome labels are available.",
                ],
                "rows": rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Harvested boundary-derived climate feature dataset.")
    print(f"output_path: {output_path}")
    print(f"boundary_sample_count: {len(boundary_samples)}")
    print(f"row_count: {len(rows)}")
    print(f"location_count: {count_locations(rows)}")
    print(f"fallback_row_count: {count_fallback_rows(rows)}")
    print(f"real_data_row_count: {count_real_data_rows(rows)}")
    print(f"high_completeness_row_count: {count_high_completeness_rows(rows)}")


def load_boundary_samples(*, limit: int, per_country: int) -> list[dict[str, object]]:
    with SessionLocal() as session:
        boundaries = (
            session.query(AdministrativeBoundary)
            .order_by(
                AdministrativeBoundary.country.asc().nulls_last(),
                AdministrativeBoundary.name.asc(),
            )
            .all()
        )

    selected: list[dict[str, object]] = []
    country_counts: dict[str, int] = defaultdict(int)

    for boundary in boundaries:
        country = boundary.country or "unknown"

        if country_counts[country] >= per_country:
            continue

        bbox = geometry_bbox(boundary.geometry_geojson)

        if bbox is None:
            continue

        west, south, east, north = bbox
        latitude = (south + north) / 2
        longitude = (west + east) / 2

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            continue

        selected.append(
            {
                "boundary_id": boundary.id,
                "name": boundary.name,
                "country": country,
                "region_type": boundary.region_type,
                "climate_region_type": boundary.climate_region_type,
                "boundary_source": boundary.source,
                "latitude": latitude,
                "longitude": longitude,
                "bbox": bbox,
            },
        )
        country_counts[country] += 1

        if len(selected) >= limit:
            break

    return selected


def build_rows(
    boundary_samples: list[dict[str, object]],
    *,
    years: list[int],
    warming_levels: list[float],
    seasons: list[str],
    time_of_day: str,
    scenario: str,
    model: str | None,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    for sample in boundary_samples:
        spatial = spatial_context_from_boundary_sample(sample)

        for year in years:
            for warming_level in warming_levels:
                for season in seasons:
                    feature_vector = build_climate_feature_vector(
                        FeatureBuildRequest(
                            query=str(sample["name"]),
                            year=year,
                            warming_level=warming_level,
                            season=season,
                            time_of_day=time_of_day,
                            climate_scenario=scenario,
                            climate_model=model,
                        ),
                        spatial=spatial,
                    )
                    features = numeric_features(feature_vector.features)
                    rows.append(
                        {
                            "metadata": {
                                "location": sample["name"],
                                "boundary_id": sample["boundary_id"],
                                "boundary_source": sample["boundary_source"],
                                "resolved_name": feature_vector.resolved_name,
                                "latitude": feature_vector.latitude,
                                "longitude": feature_vector.longitude,
                                "resolution_level": feature_vector.resolution_level,
                                "country": sample["country"],
                                "climate_region_type": feature_vector.climate_region_type,
                                "year": year,
                                "warming_level": warming_level,
                                "season": season,
                                "time_of_day": time_of_day,
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


def spatial_context_from_boundary_sample(
    sample: dict[str, object],
) -> SpatialResolutionResponse:
    latitude = float(sample["latitude"])
    longitude = float(sample["longitude"])
    climate_sample = sample_climate_raster(
        latitude=latitude,
        longitude=longitude,
        layer_type="heat_stress",
    )
    country = str(sample["country"])
    name = str(sample["name"])
    climate_region_type = str(sample["climate_region_type"] or "continental")

    location = LocationResult(
        location_name=name,
        region=country,
        climate_zone=climate_region_type.replace("_", " "),
        latitude=latitude,
        longitude=longitude,
        country=country,
        hierarchy_label=f"{name} / {country}",
        place_type=str(sample["region_type"] or "administrative_boundary"),
        geocoder_provider="boundary_database",
        geocoder_metadata={"boundary_id": sample["boundary_id"]},
        bbox=[float(value) for value in sample["bbox"]],
        known=True,
        extrapolated=False,
        location_id=f"boundary:{sample['boundary_id']}",
    )

    return SpatialResolutionResponse(
        input_query=name,
        place_id=None,
        place_persisted=False,
        resolved_location=location,
        resolution_level="admin_boundary",
        boundary_id=int(sample["boundary_id"]),
        boundary_name=name,
        boundary_source="database",
        boundary_match_reason="training sample from imported boundary database",
        climate_region_type=climate_region_type,
        climate_grid_cell_id=climate_sample.grid_cell_id if climate_sample else None,
        climate_sampled_value=climate_sample.sampled_value if climate_sample else None,
        climate_sample_source=climate_sample.raster_source if climate_sample else None,
        dataset_name=climate_sample.dataset_name if climate_sample else None,
        dataset_resolution=climate_sample.dataset_resolution if climate_sample else None,
        confidence="high" if climate_sample else "medium",
        fallback_used=climate_sample is None,
        resolution_notes=[
            "Boundary-derived ML training row.",
            "Representative point comes from boundary bbox center.",
        ],
    )


def geometry_bbox(geojson: dict[str, object]) -> list[float] | None:
    coordinates = list(iter_coordinate_pairs(geojson))

    if not coordinates:
        return None

    longitudes = [point[0] for point in coordinates]
    latitudes = [point[1] for point in coordinates]

    return [
        min(longitudes),
        min(latitudes),
        max(longitudes),
        max(latitudes),
    ]


def iter_coordinate_pairs(value: object) -> Iterable[tuple[float, float]]:
    if isinstance(value, dict):
        for child in value.values():
            yield from iter_coordinate_pairs(child)
        return

    if isinstance(value, list):
        if (
            len(value) >= 2
            and isinstance(value[0], (int, float))
            and isinstance(value[1], (int, float))
        ):
            yield float(value[0]), float(value[1])
            return

        for child in value:
            yield from iter_coordinate_pairs(child)


if __name__ == "__main__":
    main()
