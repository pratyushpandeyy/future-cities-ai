"""Download geoBoundaries administrative GeoJSON files.

This is the boundary equivalent of the WorldClim downloader: it fetches
country/admin-level GeoJSONs into backend/data/raw/geoboundaries so the
import_boundaries.py script can normalize them into PostGIS.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from scripts.download_utils import (  # noqa: E402
    DownloadItem,
    print_plan,
    run_downloads,
    write_manifest,
)


GEBOUNDARIES_API_TEMPLATE = (
    "https://www.geoboundaries.org/api/current/{product}/{iso3}/{admin_level}/"
)
DEFAULT_COUNTRIES = ["IND", "GBR", "TUR", "ESP", "USA"]
DEFAULT_ADMIN_LEVELS = ["ADM2"]
COUNTRY_PRESETS = {
    "priority": DEFAULT_COUNTRIES,
    "top100-population": [
        "CHN",
        "IND",
        "USA",
        "IDN",
        "PAK",
        "NGA",
        "BRA",
        "BGD",
        "RUS",
        "MEX",
        "ETH",
        "JPN",
        "PHL",
        "EGY",
        "COD",
        "VNM",
        "IRN",
        "TUR",
        "DEU",
        "THA",
        "GBR",
        "TZA",
        "FRA",
        "ZAF",
        "ITA",
        "KEN",
        "MMR",
        "COL",
        "KOR",
        "UGA",
        "SDN",
        "ESP",
        "ARG",
        "DZA",
        "IRQ",
        "AFG",
        "POL",
        "CAN",
        "MAR",
        "SAU",
        "UKR",
        "AGO",
        "UZB",
        "YEM",
        "PER",
        "MYS",
        "GHA",
        "MOZ",
        "NPL",
        "MDG",
        "CIV",
        "VEN",
        "CMR",
        "NER",
        "AUS",
        "PRK",
        "SYR",
        "MLI",
        "BFA",
        "LKA",
        "MWI",
        "ZMB",
        "ROU",
        "CHL",
        "KAZ",
        "TCD",
        "ECU",
        "SOM",
        "GTM",
        "SEN",
        "NLD",
        "KHM",
        "ZWE",
        "GIN",
        "RWA",
        "BEN",
        "BDI",
        "TUN",
        "BOL",
        "BEL",
        "HTI",
        "CUB",
        "JOR",
        "DOM",
        "SWE",
        "HND",
        "CZE",
        "AZE",
        "GRC",
        "PNG",
        "PRT",
        "HUN",
        "TJK",
        "BLR",
        "ARE",
        "ISR",
        "AUT",
        "CHE",
        "SLE",
        "LAO",
    ],
}
USER_AGENT = "FutureCitiesAI-GeoBoundariesDownloader/1.0"


class BoundaryMetadataUnavailable(RuntimeError):
    pass


def main() -> None:
    args = parse_args()
    countries = resolve_countries(args.preset, args.countries)
    admin_levels = parse_csv_arg(args.admin_levels) or DEFAULT_ADMIN_LEVELS
    output_dir = BACKEND_ROOT / args.output_dir

    items = build_download_items(
        countries=countries,
        admin_levels=admin_levels,
        product=args.product,
        output_dir=output_dir,
        simplified=args.simplified,
        timeout=args.metadata_timeout,
        strict_metadata=args.strict_metadata,
    )

    print_plan(items)

    if not args.confirm:
        print()
        print("Dry run only. Add --confirm to download these files.")
        return

    results = run_downloads(
        items,
        workers=args.workers,
        retries=args.retries,
        timeout=args.timeout,
        force=args.force,
    )
    manifest_path = write_manifest(
        output_dir,
        source="geoBoundaries API",
        items=items,
        results=results,
    )
    print(f"Wrote manifest: {manifest_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download geoBoundaries GeoJSON files for PostGIS import.",
    )
    parser.add_argument(
        "--countries",
        default="",
        help=(
            "Comma-separated ISO3 country codes, e.g. IND,GBR,TUR,ESP. "
            "Overrides --preset when provided."
        ),
    )
    parser.add_argument(
        "--preset",
        default="priority",
        choices=sorted(COUNTRY_PRESETS),
        help="Country preset to download when --countries is not supplied.",
    )
    parser.add_argument(
        "--admin-levels",
        default=",".join(DEFAULT_ADMIN_LEVELS),
        help="Comma-separated admin levels, e.g. ADM1,ADM2,ADM3.",
    )
    parser.add_argument(
        "--product",
        default="gbOpen",
        help="geoBoundaries product, usually gbOpen.",
    )
    parser.add_argument(
        "--output-dir",
        default="data/raw/geoboundaries",
        help="Output directory relative to backend/.",
    )
    parser.add_argument(
        "--full-geometry",
        action="store_true",
        help="Download full GeoJSON instead of simplified GeoJSON.",
    )
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually download files. Without this, only prints the plan.",
    )
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--metadata-timeout", type=int, default=30)
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--strict-metadata",
        action="store_true",
        help="Fail immediately if a country/admin-level metadata endpoint is missing.",
    )
    args = parser.parse_args()
    args.simplified = not args.full_geometry
    return args


def parse_csv_arg(value: str) -> list[str]:
    return [
        item.strip().upper()
        for item in value.split(",")
        if item.strip()
    ]


def resolve_countries(preset: str, countries_arg: str) -> list[str]:
    explicit_countries = parse_csv_arg(countries_arg)

    if explicit_countries:
        return explicit_countries

    return COUNTRY_PRESETS[preset]


def build_download_items(
    *,
    countries: list[str],
    admin_levels: list[str],
    product: str,
    output_dir: Path,
    simplified: bool,
    timeout: int,
    strict_metadata: bool = False,
) -> list[DownloadItem]:
    items = []
    planned_count = len(countries) * len(admin_levels)
    checked_count = 0
    skipped_count = 0

    for country in countries:
        for admin_level in admin_levels:
            checked_count += 1
            print(
                f"[metadata {checked_count}/{planned_count}] "
                f"{country}/{admin_level}",
                flush=True,
            )

            try:
                metadata = fetch_boundary_metadata(
                    product=product,
                    iso3=country,
                    admin_level=admin_level,
                    timeout=timeout,
                )
            except BoundaryMetadataUnavailable as exc:
                skipped_count += 1
                print(f"  skipped: {exc}", flush=True)

                if strict_metadata:
                    raise

                continue

            download_url = select_download_url(metadata, simplified=simplified)
            filename = f"geoBoundaries-{country}-{admin_level}"

            if simplified:
                filename += "_simplified"

            filename += ".geojson"
            destination = output_dir / product / country / admin_level / filename
            items.append(
                DownloadItem(
                    dataset="geoboundaries",
                    key=f"{country}/{admin_level}",
                    url=download_url,
                    destination=destination,
                    metadata={
                        "country": country,
                        "admin_level": admin_level,
                        "product": product,
                        "simplified": simplified,
                        "boundary_id": metadata.get("boundaryID"),
                        "boundary_name": metadata.get("boundaryName"),
                        "unit_count": metadata.get("admUnitCount"),
                        "license": metadata.get("boundaryLicense"),
                        "source": metadata.get("boundarySource"),
                    },
                ),
            )

    if skipped_count:
        print(f"Skipped metadata for {skipped_count} unavailable boundaries.", flush=True)

    return items


def fetch_boundary_metadata(
    *,
    product: str,
    iso3: str,
    admin_level: str,
    timeout: int,
) -> dict[str, object]:
    url = GEBOUNDARIES_API_TEMPLATE.format(
        product=product,
        iso3=iso3,
        admin_level=admin_level,
    )
    request = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise BoundaryMetadataUnavailable(
            f"geoBoundaries metadata not found for {iso3}/{admin_level}: "
            f"HTTP {exc.code}",
        ) from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise BoundaryMetadataUnavailable(
            f"Could not fetch geoBoundaries metadata for {iso3}/{admin_level}: {exc}",
        ) from exc


def select_download_url(metadata: dict[str, object], *, simplified: bool) -> str:
    key = "simplifiedGeometryGeoJSON" if simplified else "gjDownloadURL"
    download_url = metadata.get(key) or metadata.get("gjDownloadURL")

    if not isinstance(download_url, str) or not download_url:
        raise RuntimeError(f"geoBoundaries metadata missing {key}/gjDownloadURL")

    return download_url


if __name__ == "__main__":
    main()
