import argparse
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.ml_training import train_climate_adjustment_model  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the Future Cities AI climate adjustment model.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output artifact path. Defaults to backend/data/models/.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing model artifact.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = train_climate_adjustment_model(
        output_path=args.output,
        overwrite=args.overwrite,
    )
    print(result.message)
    print(f"model_version: {result.model_version}")
    print(f"model_type: {result.model_type}")
    print(f"artifact_path: {result.artifact_path}")
    print(f"training_row_count: {result.training_row_count}")
    print("metrics:")

    for metric, value in sorted(result.metrics.items()):
        print(f"  {metric}: {value}")


if __name__ == "__main__":
    main()
