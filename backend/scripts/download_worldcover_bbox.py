"""Download only ESA WorldCover tiles intersecting a requested bbox."""

from __future__ import annotations

import argparse
import math
import sys
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


BASE_URL = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/"
    "v200/2021/map"
)
BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "raw" / "esa_worldcover"
PRESET_BBOXES = {
    "bengaluru": (77.2, 12.7, 77.9, 13.2),
    "mumbai": (72.6, 18.8, 73.1, 19.4),
    "pune": (73.5, 18.3, 74.2, 18.8),
    "manchester": (-2.8, 53.2, -1.8, 53.8),
    "istanbul": (28.4, 40.7, 29.5, 41.4),
    "madrid": (-4.1, 40.1, -3.2, 40.8),
    "varanasi": (82.7, 25.1, 83.3, 25.6),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download ESA WorldCover 2021 v200 tiles by bbox or city preset.",
    )
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--bbox", nargs=4, type=float, metavar=("W", "S", "E", "N"))
    target.add_argument(
        "--cities",
        nargs="+",
        choices=sorted(PRESET_BBOXES),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--retries", type=int, default=8)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def tile_ids_for_bbox(
    west: float,
    south: float,
    east: float,
    north: float,
) -> list[str]:
    if not (-180 <= west < east <= 180 and -60 <= south < north <= 84):
        raise ValueError(
            "Use west,south,east,north within the WorldCover extent "
            "(-180..180 longitude, -60..84 latitude)",
        )

    longitude_starts = coordinate_starts(west, east)
    latitude_starts = coordinate_starts(south, north)

    return [
        tile_id(latitude, longitude)
        for latitude in latitude_starts
        for longitude in longitude_starts
    ]


def coordinate_starts(minimum: float, maximum: float) -> list[int]:
    start = math.floor(minimum / 3) * 3
    end = math.floor((maximum - 1e-9) / 3) * 3
    return list(range(start, end + 1, 3))


def tile_id(latitude: int, longitude: int) -> str:
    latitude_label = f"{'N' if latitude >= 0 else 'S'}{abs(latitude):02d}"
    longitude_label = f"{'E' if longitude >= 0 else 'W'}{abs(longitude):03d}"
    return f"{latitude_label}{longitude_label}"


def build_download_plan(
    *,
    bboxes: list[tuple[float, float, float, float]],
    output_dir: Path,
) -> list[DownloadItem]:
    tile_ids = sorted(
        {
            tile
            for bbox in bboxes
            for tile in tile_ids_for_bbox(*bbox)
        },
    )
    items = []

    for tile in tile_ids:
        filename = f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
        items.append(
            DownloadItem(
                dataset="esa_worldcover_2021",
                key=tile,
                url=f"{BASE_URL}/{filename}",
                destination=output_dir / "v200" / "2021" / filename,
                metadata={
                    "tile_id": tile,
                    "resolution": "10m",
                    "year": 2021,
                },
            ),
        )

    return items


def main() -> int:
    args = parse_args()
    bboxes = (
        [tuple(args.bbox)]
        if args.bbox
        else [PRESET_BBOXES[city] for city in args.cities]
    )

    try:
        items = build_download_plan(
            bboxes=bboxes,
            output_dir=args.output_dir.resolve(),
        )
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    print_plan(items)

    if args.dry_run:
        return 0
    if not args.confirm:
        print("WorldCover tiles are large. Add --confirm.", file=sys.stderr)
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
        source="ESA WorldCover 2021 v200",
        items=items,
        results=results,
    )
    print(f"Manifest: {manifest}")
    return 1 if status_counts(results).get("failed", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
