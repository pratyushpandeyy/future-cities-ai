import argparse
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.services.feature_cache import export_feature_cache_training_dataset  # noqa: E402


DEFAULT_OUTPUT_PATH = (
    BACKEND_ROOT / "data" / "models" / "cached_feature_training_dataset_v1.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export cached API feature vectors into an ML training dataset.",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = export_feature_cache_training_dataset(args.output.resolve())

    print("Exported cached feature training dataset.")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
