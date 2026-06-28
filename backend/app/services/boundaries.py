import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import AdministrativeBoundary
from app.db.session import SessionLocal, is_database_configured
from app.models.schemas import (
    AdminBoundaryDetail,
    AdminBoundarySummary,
    LocationResult,
    RegionBoundaryResponse,
)
from app.services.boundary_resolution import (
    boundary_search_hierarchy,
    match_boundary_candidates,
)
from app.services.simulation import resolve_location


BOUNDARY_DIR = Path(__file__).resolve().parents[2] / "data" / "boundaries"

BOUNDARY_ALIASES = {
    "bangalore": "bangalore_urban.geojson",
    "bengaluru": "bangalore_urban.geojson",
    "bengaluru urban": "bangalore_urban.geojson",
    "bangalore urban": "bangalore_urban.geojson",
    "whitefield": "bangalore_urban.geojson",
    "koramangala": "bangalore_urban.geojson",
    "karnataka": "karnataka.geojson",
    "mumbai": "maharashtra.geojson",
    "bandra": "maharashtra.geojson",
    "maharashtra": "maharashtra.geojson",
    "manchester": "greater_manchester.geojson",
    "greater manchester": "greater_manchester.geojson",
    "north west england": "greater_manchester.geojson",
    "istanbul": "marmara_istanbul.geojson",
    "kadikoy": "marmara_istanbul.geojson",
    "marmara": "marmara_istanbul.geojson",
    "madrid": "community_of_madrid.geojson",
    "community of madrid": "community_of_madrid.geojson",
}

BOUNDARY_NAME_PROPERTY_KEYS = [
    "name",
    "shapeName",
    "shapeISO",
    "shapeGroup",
    "NAME",
    "NAME_0",
    "NAME_1",
    "NAME_2",
    "NAME_3",
    "VARNAME_1",
    "VARNAME_2",
    "NL_NAME_1",
    "NL_NAME_2",
]


def get_region_boundary(
    location: str,
    location_result: LocationResult | None = None,
) -> RegionBoundaryResponse:
    location_result = location_result or resolve_location(location)
    database_boundary, database_match_reason = find_database_boundary(
        location,
        location_result,
    )

    if database_boundary:
        polygon = extract_polygon_ring(database_boundary.geometry_geojson)

        if polygon:
            return RegionBoundaryResponse(
                location=location_result,
                boundary_source="database",
                boundary_name=database_boundary.name,
                boundary_match_reason=database_match_reason,
                climate_region_type=database_boundary.climate_region_type,
                db_boundary_id=database_boundary.id,
                polygon=polygon,
                geojson=database_boundary.geometry_geojson,
            )

    boundary_file, local_match_reason = find_boundary_file(location, location_result)

    if boundary_file:
        geojson = load_boundary_geojson(boundary_file)
        polygon = extract_polygon_ring(geojson)
        boundary_name = extract_boundary_name(geojson) or boundary_file.replace(
            ".geojson",
            "",
        )

        if polygon:
            return RegionBoundaryResponse(
                location=location_result,
                boundary_source="real_geojson",
                boundary_name=boundary_name,
                boundary_match_reason=local_match_reason,
                climate_region_type=infer_boundary_climate_region(boundary_file),
                polygon=polygon,
                geojson=geojson,
            )

    return simulated_boundary(location_result)


def find_database_boundary(
    location: str,
    location_result: LocationResult,
) -> tuple[AdministrativeBoundary | None, str | None]:
    if not is_database_configured() or SessionLocal is None:
        return None, "DATABASE_URL is not configured"

    try:
        with SessionLocal() as session:
            return match_database_boundary(session, location, location_result)
    except SQLAlchemyError:
        return None, "database lookup failed"


def match_database_boundary(
    session: Session,
    location: str,
    location_result: LocationResult,
) -> tuple[AdministrativeBoundary | None, str | None]:
    candidates = boundary_search_hierarchy(location, location_result)
    boundaries = session.query(AdministrativeBoundary).all()

    for candidate in candidates:
        for boundary in boundaries:
            match = match_boundary_candidates(boundary, [candidate])

            if match:
                return boundary, f"database hierarchy {match[1]}"

    return None, "no database boundary matched search metadata"


def find_boundary_file(
    location: str,
    location_result: LocationResult,
) -> tuple[str | None, str | None]:
    searchable_text = build_searchable_text(location, location_result)

    for alias, boundary_file in BOUNDARY_ALIASES.items():
        if alias in searchable_text:
            return boundary_file, f"local GeoJSON alias match: {alias}"

    catalog_match = find_catalog_boundary_file(searchable_text)

    if catalog_match:
        boundary_file, matched_name = catalog_match
        return boundary_file, f"local GeoJSON catalog match: {matched_name}"

    return None, "no local GeoJSON boundary matched search metadata"


def find_catalog_boundary_file(searchable_text: str) -> tuple[str, str] | None:
    for boundary_file, names in local_boundary_catalog().items():
        for name in sorted(names, key=len, reverse=True):
            if name and name in searchable_text:
                return boundary_file, name

    return None


@lru_cache(maxsize=1)
def local_boundary_catalog() -> dict[str, list[str]]:
    if not BOUNDARY_DIR.exists():
        return {}

    catalog = {}

    for boundary_path in BOUNDARY_DIR.glob("*.geojson"):
        try:
            geojson = json.loads(boundary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        names = extract_boundary_search_names(geojson)
        filename_name = boundary_path.stem.replace("_", " ").replace("-", " ").lower()
        names.append(filename_name)
        catalog[boundary_path.name] = sorted(set(filter(None, names)))

    return catalog


def extract_boundary_search_names(geojson: dict[str, object]) -> list[str]:
    features = geojson.get("features")

    if not isinstance(features, list):
        return []

    names = []

    for feature in features[:20]:
        if not isinstance(feature, dict):
            continue

        properties = feature.get("properties")

        if not isinstance(properties, dict):
            continue

        for key in BOUNDARY_NAME_PROPERTY_KEYS:
            raw_value = properties.get(key)

            if isinstance(raw_value, str):
                names.extend(normalize_boundary_names(raw_value))

    return names


def normalize_boundary_names(value: str) -> list[str]:
    names = []

    for item in value.replace("|", ",").replace(";", ",").split(","):
        normalized = item.strip().lower()

        if normalized:
            names.append(normalized)

    return names


def build_searchable_text(location: str, location_result: LocationResult) -> str:
    return " ".join(
        filter(
            None,
            [
                location,
                location_result.location_name,
                location_result.locality,
                location_result.district,
                location_result.city,
                location_result.region,
                location_result.country,
                location_result.hierarchy_label,
            ],
        ),
    ).lower()


@lru_cache(maxsize=16)
def load_boundary_geojson(boundary_file: str) -> dict[str, object]:
    boundary_path = BOUNDARY_DIR / boundary_file

    with boundary_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def extract_polygon_ring(geojson: dict[str, object]) -> list[list[float]]:
    features = geojson.get("features")

    if not isinstance(features, list) or not features:
        return []

    feature = features[0]

    if not isinstance(feature, dict):
        return []

    geometry = feature.get("geometry")

    if not isinstance(geometry, dict):
        return []

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if geometry_type == "Polygon" and isinstance(coordinates, list) and coordinates:
        return coordinates[0]

    if (
        geometry_type == "MultiPolygon"
        and isinstance(coordinates, list)
        and coordinates
        and coordinates[0]
    ):
        return coordinates[0][0]

    return []


def extract_boundary_name(geojson: dict[str, object]) -> str | None:
    features = geojson.get("features")

    if not isinstance(features, list) or not features:
        return None

    feature = features[0]

    if not isinstance(feature, dict):
        return None

    properties = feature.get("properties")

    if not isinstance(properties, dict):
        return None

    name = first_boundary_property(properties, BOUNDARY_NAME_PROPERTY_KEYS)

    return str(name) if name else None


def first_boundary_property(
    properties: dict[str, object],
    keys: list[str],
) -> object | None:
    for key in keys:
        value = properties.get(key)

        if value:
            return value

    return None


def infer_boundary_climate_region(boundary_file: str) -> str:
    if boundary_file in {"maharashtra.geojson"}:
        return "tropical_humid"

    if boundary_file in {"bangalore_urban.geojson", "karnataka.geojson"}:
        return "highland"

    if boundary_file in {"marmara_istanbul.geojson", "community_of_madrid.geojson"}:
        return "mediterranean"

    if boundary_file == "greater_manchester.geojson":
        return "temperate_oceanic"

    return "continental"


def list_database_boundaries() -> list[AdminBoundarySummary]:
    if not is_database_configured() or SessionLocal is None:
        return []

    try:
        with SessionLocal() as session:
            boundaries = (
                session.query(AdministrativeBoundary)
                .order_by(AdministrativeBoundary.name.asc())
                .all()
            )

            return [boundary_to_summary(boundary) for boundary in boundaries]
    except SQLAlchemyError:
        return []


def get_database_boundary_detail(boundary_id: int) -> AdminBoundaryDetail | None:
    if not is_database_configured() or SessionLocal is None:
        return None

    try:
        with SessionLocal() as session:
            boundary = session.get(AdministrativeBoundary, boundary_id)

            if not boundary:
                return None

            return AdminBoundaryDetail(
                **boundary_to_summary(boundary).model_dump(),
                geometry_geojson=boundary.geometry_geojson,
            )
    except SQLAlchemyError:
        return None


def boundary_to_summary(boundary: AdministrativeBoundary) -> AdminBoundarySummary:
    return AdminBoundarySummary(
        id=boundary.id,
        name=boundary.name,
        aliases=boundary.aliases,
        country=boundary.country,
        region_type=boundary.region_type,
        climate_region_type=boundary.climate_region_type,
        source=boundary.source,
        created_at=boundary.created_at,
    )


def simulated_boundary(location_result: LocationResult) -> RegionBoundaryResponse:
    if location_result.bbox:
        west, south, east, north = location_result.bbox
        polygon = [
            [west, north],
            [east, north],
            [east, south],
            [west, south],
            [west, north],
        ]
    else:
        lon = location_result.longitude
        lat = location_result.latitude
        polygon = [
            [round(lon - 1.4, 4), round(lat + 0.9, 4)],
            [round(lon - 0.2, 4), round(lat + 1.2, 4)],
            [round(lon + 1.3, 4), round(lat + 0.5, 4)],
            [round(lon + 1.0, 4), round(lat - 0.9, 4)],
            [round(lon - 0.6, 4), round(lat - 1.1, 4)],
            [round(lon - 1.5, 4), round(lat - 0.2, 4)],
            [round(lon - 1.4, 4), round(lat + 0.9, 4)],
        ]

    return RegionBoundaryResponse(
        location=location_result,
        boundary_source="simulated_fallback",
        boundary_name="Simulated regional boundary",
        boundary_match_reason="generated from geocoded bbox or point fallback",
        climate_region_type=None,
        polygon=polygon,
    )
