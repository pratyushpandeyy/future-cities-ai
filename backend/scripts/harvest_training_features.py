import argparse
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.models.schemas import ClimateFeatureHarvestRequest  # noqa: E402
from app.services.feature_harvesting import harvest_climate_training_features  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Harvest compact climate feature rows for ML training.",
    )
    parser.add_argument(
        "--location",
        action="append",
        dest="locations",
        default=[],
        help="Location to include. Can be repeated. Defaults to built-in MVP places.",
    )
    parser.add_argument(
        "--year",
        action="append",
        dest="years",
        type=int,
        default=[],
        help="Year to include. Can be repeated.",
    )
    parser.add_argument(
        "--warming",
        action="append",
        dest="warming_levels",
        type=float,
        default=[],
        help="Warming level to include. Can be repeated.",
    )
    parser.add_argument(
        "--season",
        action="append",
        dest="seasons",
        default=[],
        help="Season to include. Can be repeated.",
    )
    parser.add_argument(
        "--scenario",
        default="ssp245",
        help="Climate scenario/pathway, for example ssp245 or ssp585.",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Optional climate model name, for example MPI-ESM1-2-HR.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output JSON path. Defaults to backend/data/models/.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing harvested feature dataset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = harvest_climate_training_features(
        ClimateFeatureHarvestRequest(
            locations=args.locations,
            years=args.years or [2030, 2050, 2070],
            warming_levels=args.warming_levels or [1.7, 2.7, 3.5],
            seasons=args.seasons or ["Summer", "Monsoon", "Winter"],
            climate_scenario=args.scenario,
            climate_model=args.model,
            output_path=str(args.output) if args.output else None,
            overwrite=args.overwrite,
        ),
    )
    print(result.message)
    print(f"output_path: {result.output_path}")
    print(f"row_count: {result.row_count}")
    print(f"location_count: {result.location_count}")
    print(f"fallback_row_count: {result.fallback_row_count}")
    print(f"real_data_row_count: {result.real_data_row_count}")
    print(f"high_completeness_row_count: {result.high_completeness_row_count}")


if __name__ == "__main__":
    main()
