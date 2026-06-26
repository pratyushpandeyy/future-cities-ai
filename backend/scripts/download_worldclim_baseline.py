"""Download WorldClim v2.1 historical climate and elevation archives."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

try:
    from scripts.download_utils import (
        DownloadItem,
        print_plan,
        run_downloads,
        status_counts,
        write_manifest,
    )
except ModuleNotFoundError:
    from download_utils import (
        DownloadItem,
        print_plan,
        run_downloads,
        status_counts,
        write_manifest,
    )


BASE_URL = "https://geodata.ucdavis.edu/climate/worldclim/2_1/base"
SUPPORTED_RESOLUTIONS = {"30s", "2.5m", "5m", "10m"}
SUPPORTED_VARIABLES = {"tmin", "tmax", "tavg", "prec", "srad", "wind", "vapr", "elev"}
DEFAULT_VARIABLES = ["tmin", "tmax", "prec", "elev"]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "raw" / "worldclim" / "historical"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download resumable WorldClim historical baseline archives.",
    )
    parser.add_argument("--variables", nargs="+", default=DEFAULT_VARIABLES)
    parser.add_argument(
        "--resolution",
        default="2.5m",
        choices=sorted(SUPPORTED_RESOLUTIONS),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--retries", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Extract completed ZIP archives after downloading.",
    )
    return parser.parse_args()


def build_download_plan(
    *,
    variables: list[str],
    resolution: str,
    output_dir: Path,
) -> list[DownloadItem]:
    items = []

    for variable in variables:
        filename = f"wc2.1_{resolution}_{variable}.zip"
        items.append(
            DownloadItem(
                dataset="worldclim_historical",
                key=variable,
                url=f"{BASE_URL}/{filename}",
                destination=output_dir / resolution / filename,
                metadata={
                    "variable": variable,
                    "resolution": resolution,
                    "baseline_period": "1970-2000",
                },
            ),
        )

    return items


def extract_archives(items: list[DownloadItem]) -> None:
    for item in items:
        archive = item.destination

        if not archive.exists():
            continue

        extract_dir = archive.parent / item.key
        extract_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive) as zipped:
            safe_extract(zipped, extract_dir)

        print(f"Extracted {archive.name} -> {extract_dir}")


def safe_extract(zipped: zipfile.ZipFile, destination: Path) -> None:
    resolved_destination = destination.resolve()

    for member in zipped.infolist():
        target = (destination / member.filename).resolve()

        if resolved_destination not in target.parents and target != resolved_destination:
            raise ValueError(f"Unsafe ZIP member path: {member.filename}")

    zipped.extractall(destination)


def main() -> int:
    args = parse_args()
    invalid = set(args.variables) - SUPPORTED_VARIABLES

    if invalid:
        print(f"Unsupported variables: {sorted(invalid)}", file=sys.stderr)
        return 2

    items = build_download_plan(
        variables=args.variables,
        resolution=args.resolution,
        output_dir=args.output_dir.resolve(),
    )
    print_plan(items)

    if args.dry_run:
        return 0
    if len(items) > 1 and not args.confirm:
        print("Add --confirm for a multi-file download.", file=sys.stderr)
        return 2

    results = run_downloads(
        items,
        workers=args.workers,
        retries=args.retries,
        timeout=args.timeout,
        force=args.force,
    )
    manifest = write_manifest(
        args.output_dir.resolve(),
        source="WorldClim v2.1 historical climate",
        items=items,
        results=results,
    )
    print(f"Manifest: {manifest}")

    if args.extract:
        extract_archives(items)

    return 1 if status_counts(results).get("failed", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
