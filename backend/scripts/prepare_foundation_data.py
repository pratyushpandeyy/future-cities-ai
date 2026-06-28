"""Plan or run the foundation data workflow for Future Cities AI.

This script is intentionally an orchestrator around the focused downloader and
training scripts. Use it to keep long-running data prep reproducible while the
individual scripts stay small and testable.

Examples:
    python scripts/prepare_foundation_data.py --profile mvp --dry-run
    python scripts/prepare_foundation_data.py --profile mvp --execute
    python scripts/prepare_foundation_data.py --profile ml-only --execute
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class WorkflowStep:
    name: str
    description: str
    command: list[str]
    needs_network: bool = False
    large_download: bool = False


MVP_CITIES = [
    "bengaluru",
    "mumbai",
    "pune",
    "manchester",
    "istanbul",
    "madrid",
    "varanasi",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or run climate, urban-context, and ML preparation steps."
        ),
    )
    parser.add_argument(
        "--profile",
        choices=["mvp", "ml-only", "downloads-only", "heavy-offline"],
        default="mvp",
        help=(
            "mvp = compact useful setup; ml-only = harvest/train from existing "
            "data; downloads-only = data files only; heavy-offline = includes "
            "large GHSL global products."
        ),
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run the planned commands. Default only prints the plan.",
    )
    parser.add_argument(
        "--yes-large-downloads",
        action="store_true",
        help="Allow steps marked as large downloads.",
    )
    parser.add_argument(
        "--worldclim-models",
        nargs="+",
        default=["MPI-ESM1-2-HR", "MIROC6", "CNRM-CM6-1"],
        help="WorldClim CMIP6 models to download/use.",
    )
    parser.add_argument(
        "--worldclim-scenarios",
        nargs="+",
        default=["ssp245", "ssp585"],
        help="WorldClim CMIP6 scenarios to download/use.",
    )
    parser.add_argument(
        "--worldclim-periods",
        nargs="+",
        default=["2021-2040", "2041-2060", "2061-2080", "2081-2100"],
        help="WorldClim CMIP6 20-year periods to download/use.",
    )
    parser.add_argument(
        "--worldclim-variables",
        nargs="+",
        default=["tmin", "tmax", "prec"],
        help="WorldClim future variables.",
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        default=MVP_CITIES,
        help="City presets for local land-cover tiles.",
    )
    parser.add_argument(
        "--training-locations",
        nargs="+",
        default=[
            "Mumbai",
            "Bengaluru",
            "Whitefield, Bengaluru",
            "Pune",
            "Paris",
            "Istanbul",
            "Manchester",
            "Madrid",
            "Varanasi",
        ],
        help="Locations for ML feature harvesting.",
    )
    return parser.parse_args()


def build_workflow(args: argparse.Namespace) -> list[WorkflowStep]:
    steps: list[WorkflowStep] = []

    if args.profile in {"mvp", "downloads-only", "heavy-offline"}:
        steps.extend(
            [
                WorkflowStep(
                    name="worldclim-cmip6-future",
                    description=(
                        "Future monthly climate rasters: tmin/tmax/prec for "
                        "selected GCMs, SSP pathways, and 20-year periods."
                    ),
                    command=[
                        sys.executable,
                        "scripts/download_worldclim_cmip6.py",
                        "--models",
                        *args.worldclim_models,
                        "--scenarios",
                        *args.worldclim_scenarios,
                        "--periods",
                        *args.worldclim_periods,
                        "--variables",
                        *args.worldclim_variables,
                        "--resolution",
                        "2.5m",
                        "--workers",
                        "3",
                        "--retries",
                        "8",
                        "--timeout",
                        "180",
                        "--confirm",
                    ],
                    needs_network=True,
                ),
                WorkflowStep(
                    name="worldclim-baseline",
                    description=(
                        "Historical baseline rasters, including elevation, for "
                        "anomaly and terrain features."
                    ),
                    command=[
                        sys.executable,
                        "scripts/download_worldclim_baseline.py",
                        "--variables",
                        "tmin",
                        "tmax",
                        "prec",
                        "elev",
                        "--resolution",
                        "2.5m",
                        "--workers",
                        "2",
                        "--confirm",
                        "--extract",
                    ],
                    needs_network=True,
                ),
                WorkflowStep(
                    name="worldcover-city-tiles",
                    description=(
                        "ESA WorldCover 10m land-cover tiles for MVP cities. "
                        "This is the green-cover/built-up proxy layer."
                    ),
                    command=[
                        sys.executable,
                        "scripts/download_worldcover_bbox.py",
                        "--cities",
                        *args.cities,
                        "--workers",
                        "2",
                        "--confirm",
                    ],
                    needs_network=True,
                    large_download=True,
                ),
            ],
        )

    if args.profile == "heavy-offline":
        steps.append(
            WorkflowStep(
                name="ghsl-global-urban-context",
                description=(
                    "Large GHSL population and built-up-surface archives. "
                    "Use only when disk/network budget is available."
                ),
                command=[
                    sys.executable,
                    "scripts/download_ghsl.py",
                    "--products",
                    "population",
                    "built_surface",
                    "--workers",
                    "1",
                    "--confirm-large-download",
                ],
                needs_network=True,
                large_download=True,
            ),
        )

    if args.profile in {"mvp", "ml-only"}:
        harvest_command = [
            sys.executable,
            "scripts/harvest_training_features.py",
            "--overwrite",
        ]

        for location in args.training_locations:
            harvest_command.extend(["--location", location])

        steps.extend(
            [
                WorkflowStep(
                    name="harvest-ml-features",
                    description=(
                        "Build a compact training table from climate rasters, "
                        "urban proxies, and deterministic target labels."
                    ),
                    command=harvest_command,
                ),
                WorkflowStep(
                    name="train-ml-model",
                    description=(
                        "Train the current lightweight ML artifact consumed by "
                        "scenario scoring and advisor evidence."
                    ),
                    command=[
                        sys.executable,
                        "scripts/train_climate_model.py",
                        "--overwrite",
                    ],
                ),
            ],
        )

    return steps


def print_workflow(steps: list[WorkflowStep]) -> None:
    print(f"Planned steps: {len(steps)}")

    for index, step in enumerate(steps, start=1):
        flags = []

        if step.needs_network:
            flags.append("network")
        if step.large_download:
            flags.append("large")

        suffix = f" [{' / '.join(flags)}]" if flags else ""
        print(f"\n{index}. {step.name}{suffix}")
        print(f"   {step.description}")
        print(f"   command: {format_command(step.command)}")


def run_workflow(
    steps: list[WorkflowStep],
    *,
    allow_large_downloads: bool,
) -> int:
    for step in steps:
        if step.large_download and not allow_large_downloads:
            print(
                f"Skipping large step '{step.name}'. "
                "Pass --yes-large-downloads to run it.",
            )
            continue

        print(f"\nRunning {step.name}...")
        result = subprocess.run(step.command, cwd=BACKEND_ROOT, check=False)

        if result.returncode != 0:
            print(f"Step failed: {step.name} ({result.returncode})")
            return result.returncode

    return 0


def format_command(command: list[str]) -> str:
    return " ".join(quote_if_needed(part) for part in command)


def quote_if_needed(value: str) -> str:
    if any(character.isspace() for character in value):
        return f'"{value}"'

    return value


def main() -> int:
    args = parse_args()
    steps = build_workflow(args)
    print_workflow(steps)

    if not args.execute:
        print("\nDry plan only. Add --execute to run these steps.")
        return 0

    return run_workflow(
        steps,
        allow_large_downloads=args.yes_large_downloads,
    )


if __name__ == "__main__":
    raise SystemExit(main())
