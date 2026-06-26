"""Download selected global GHSL 2020 urban foundation products."""

from __future__ import annotations

import argparse
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


BACKEND_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BACKEND_ROOT / "data" / "raw" / "ghsl"
PRODUCTS = {
    "population": {
        "filename": "GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0.zip",
        "url": (
            "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/"
            "GHS_POP_GLOBE_R2023A/"
            "GHS_POP_E2020_GLOBE_R2023A_54009_100/V1-0/"
            "GHS_POP_E2020_GLOBE_R2023A_54009_100_V1_0.zip"
        ),
        "description": "2020 population count, Mollweide, 100m",
        "approximate_size": "4.75 GB",
    },
    "built_surface": {
        "filename": "GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0.zip",
        "url": (
            "https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/"
            "GHS_BUILT_S_GLOBE_R2023A/"
            "GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100/V1-0/"
            "GHS_BUILT_S_E2020_GLOBE_R2023A_54009_100_V1_0.zip"
        ),
        "description": "2020 built-up surface, Mollweide, 100m",
        "approximate_size": "1.90 GB",
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download selected GHSL global 2020 products.",
    )
    parser.add_argument(
        "--products",
        nargs="+",
        default=["population", "built_surface"],
        choices=sorted(PRODUCTS),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--retries", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--confirm-large-download", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser.parse_args()


def build_download_plan(
    *,
    products: list[str],
    output_dir: Path,
) -> list[DownloadItem]:
    items = []

    for product_key in products:
        product = PRODUCTS[product_key]
        items.append(
            DownloadItem(
                dataset="ghsl_r2023a",
                key=product_key,
                url=product["url"],
                destination=output_dir / product["filename"],
                metadata={
                    "description": product["description"],
                    "approximate_size": product["approximate_size"],
                    "epoch": 2020,
                    "resolution": "100m",
                    "crs": "ESRI:54009",
                },
            ),
        )

    return items


def main() -> int:
    args = parse_args()
    items = build_download_plan(
        products=args.products,
        output_dir=args.output_dir.resolve(),
    )
    print_plan(items)
    selected_sizes = ", ".join(
        f"{item.key}: {item.metadata['approximate_size']}"
        for item in items
    )
    print(f"Approximate archive sizes: {selected_sizes}")

    if args.dry_run:
        return 0
    if not args.confirm_large_download:
        print(
            "Add --confirm-large-download after checking free disk space.",
            file=sys.stderr,
        )
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
        source="Global Human Settlement Layer R2023A",
        items=items,
        results=results,
    )
    print(f"Manifest: {manifest}")
    return 1 if status_counts(results).get("failed", 0) else 0


if __name__ == "__main__":
    raise SystemExit(main())
