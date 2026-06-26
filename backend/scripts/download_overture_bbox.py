"""Stream Overture buildings or POIs for a bbox into a local file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


SUPPORTED_TYPES = {
    "address",
    "building",
    "building_part",
    "division",
    "division_area",
    "division_boundary",
    "land",
    "land_cover",
    "land_use",
    "place",
    "segment",
    "water",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Download only Overture features intersecting a bbox from its "
            "public cloud-hosted GeoParquet release."
        ),
    )
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        required=True,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
    )
    parser.add_argument(
        "--types",
        nargs="+",
        default=["building", "place"],
    )
    parser.add_argument(
        "--format",
        choices=["geojson", "geojsonseq", "geoparquet"],
        default="geoparquet",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "data"
        / "raw"
        / "overture",
    )
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def output_suffix(output_format: str) -> str:
    return {
        "geojson": ".geojson",
        "geojsonseq": ".geojsonseq",
        "geoparquet": ".parquet",
    }[output_format]


def main() -> int:
    args = parse_args()
    invalid = set(args.types) - SUPPORTED_TYPES

    if invalid:
        print(f"Unsupported Overture types: {sorted(invalid)}", file=sys.stderr)
        return 2

    west, south, east, north = args.bbox

    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        print("Invalid bbox. Use west south east north.", file=sys.stderr)
        return 2

    outputs = [
        args.output_dir.resolve()
        / f"{theme}_{west}_{south}_{east}_{north}{output_suffix(args.format)}"
        for theme in args.types
    ]

    for theme, output in zip(args.types, outputs, strict=True):
        print(f"- {theme}: bbox={west},{south},{east},{north} -> {output}")

    if args.dry_run:
        return 0
    if not args.confirm:
        print("Add --confirm after reviewing the bbox and outputs.", file=sys.stderr)
        return 2

    try:
        from overturemaps import record_batch_reader
        from overturemaps.writers import copy, get_writer
    except ImportError:
        print(
            "Install backend requirements before running this script.",
            file=sys.stderr,
        )
        return 2

    args.output_dir.mkdir(parents=True, exist_ok=True)
    bbox = tuple(args.bbox)

    for theme, output in zip(args.types, outputs, strict=True):
        reader = record_batch_reader(theme, bbox=bbox)

        if reader is None:
            print(f"No {theme} features found.")
            continue

        with get_writer(args.format, str(output), schema=reader.schema) as writer:
            copy(reader, writer)

        print(f"Saved {theme} -> {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
