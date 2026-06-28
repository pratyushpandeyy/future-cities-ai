import argparse
import json
import sys
from pathlib import Path

from sqlalchemy import text


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_ROOT))

from app.db.models import AdministrativeBoundary  # noqa: E402
from app.db.session import Base, SessionLocal, engine, is_database_configured  # noqa: E402
from app.services.boundaries import (  # noqa: E402
    BOUNDARY_NAME_PROPERTY_KEYS,
    first_boundary_property,
    normalize_boundary_names,
)
from app.services.boundary_resolution import normalize_boundary_text  # noqa: E402


COUNTRY_PROPERTY_KEYS = [
    "shapeGroup",
    "shapeISO",
    "country",
    "COUNTRY",
    "NAME_0",
    "ISO_A3",
]

PARENT_PROPERTY_KEYS = [
    "shapeName",
    "NAME_1",
    "NAME_2",
    "NAME_3",
    "region",
    "district",
    "county",
]


def main() -> None:
    args = parse_args()

    if not is_database_configured() or engine is None or SessionLocal is None:
        raise RuntimeError("DATABASE_URL is not configured. Add it to backend/.env first.")

    input_path = Path(args.input).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Boundary input path not found: {input_path}")

    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))

    Base.metadata.create_all(bind=engine)

    files = list_boundary_files(input_path)
    imported = 0
    skipped = 0

    with SessionLocal() as session:
        for file_path in files:
            try:
                geojson = json.loads(file_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                skipped += 1
                continue

            for record in boundary_records_from_geojson(
                geojson,
                file_path=file_path,
                provider=args.provider,
                region_type=args.region_type,
                climate_region_type=args.climate_region_type,
            ):
                upsert_boundary(session, record)
                imported += 1

        session.commit()

    print(f"Imported or updated {imported} boundary records.")
    print(f"Skipped {skipped} unreadable GeoJSON files.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import GeoJSON administrative boundaries into the Future Cities AI database.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="GeoJSON file or directory containing GeoJSON files.",
    )
    parser.add_argument(
        "--provider",
        default="local_geojson_import",
        help="Source provider label, e.g. geoboundaries, gadm, osm, overture.",
    )
    parser.add_argument(
        "--region-type",
        default="administrative_boundary",
        help="Boundary type label stored in the database.",
    )
    parser.add_argument(
        "--climate-region-type",
        default="continental",
        help="Default climate region type until a stronger classifier exists.",
    )
    return parser.parse_args()


def list_boundary_files(input_path: Path) -> list[Path]:
    if input_path.is_file():
        return [input_path]

    return sorted(
        [
            *input_path.rglob("*.geojson"),
            *input_path.rglob("*.json"),
        ],
    )


def boundary_records_from_geojson(
    geojson: dict[str, object],
    *,
    file_path: Path,
    provider: str,
    region_type: str,
    climate_region_type: str,
) -> list[dict[str, object]]:
    features = geojson.get("features")

    if not isinstance(features, list):
        return []

    records = []

    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            continue

        properties = feature.get("properties")
        geometry = feature.get("geometry")

        if not isinstance(properties, dict) or not isinstance(geometry, dict):
            continue

        name = extract_record_name(properties, file_path, index)
        country = extract_first_string(properties, COUNTRY_PROPERTY_KEYS)
        aliases = extract_aliases(properties, file_path)
        record_name = unique_record_name(name, country, file_path, index)
        feature_collection = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": properties,
                    "geometry": geometry,
                },
            ],
        }

        records.append(
            {
                "name": record_name,
                "aliases": aliases,
                "country": country,
                "region_type": region_type,
                "climate_region_type": climate_region_type,
                "source": f"{provider}:{file_path.name}",
                "geometry_geojson": feature_collection,
            },
        )

    return records


def extract_record_name(
    properties: dict[str, object],
    file_path: Path,
    index: int,
) -> str:
    name = first_boundary_property(properties, BOUNDARY_NAME_PROPERTY_KEYS)

    if isinstance(name, str) and name.strip():
        return name.strip()

    return f"{file_path.stem} feature {index + 1}"


def extract_first_string(
    properties: dict[str, object],
    keys: list[str],
) -> str | None:
    value = first_boundary_property(properties, keys)

    if isinstance(value, str) and value.strip():
        return value.strip()

    return None


def extract_aliases(properties: dict[str, object], file_path: Path) -> list[str]:
    aliases = [file_path.stem.replace("_", " ").replace("-", " ")]

    for key in [*BOUNDARY_NAME_PROPERTY_KEYS, *PARENT_PROPERTY_KEYS, *COUNTRY_PROPERTY_KEYS]:
        value = properties.get(key)

        if isinstance(value, str):
            aliases.extend(normalize_boundary_names(value))

    return sorted(set(filter(None, aliases)))


def unique_record_name(
    name: str,
    country: str | None,
    file_path: Path,
    index: int,
) -> str:
    parts = [name]

    if country and normalize_boundary_text(country) not in normalize_boundary_text(name):
        parts.append(country)

    parts.append(file_path.stem)

    if index:
        parts.append(str(index + 1))

    return " / ".join(parts)


def upsert_boundary(session, record: dict[str, object]) -> None:
    existing = (
        session.query(AdministrativeBoundary)
        .filter(AdministrativeBoundary.name == record["name"])
        .one_or_none()
    )

    if existing:
        existing.aliases = record["aliases"]
        existing.country = record["country"]
        existing.region_type = record["region_type"]
        existing.climate_region_type = record["climate_region_type"]
        existing.source = record["source"]
        existing.geometry_geojson = record["geometry_geojson"]
        return

    session.add(AdministrativeBoundary(**record))


if __name__ == "__main__":
    main()
