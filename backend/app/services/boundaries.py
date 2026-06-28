import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy import String, cast, or_
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
from app.services.online_boundaries import fetch_online_boundary
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

    online_geojson, online_match_reason = fetch_online_boundary(location, location_result)

    if online_geojson:
        polygon = extract_polygon_ring(online_geojson)

        if polygon:
            cached_boundary_id = cache_online_boundary(
                location_result,
                online_geojson,
                online_match_reason,
            )
            return RegionBoundaryResponse(
                location=location_result,
                boundary_source="online_osm",
                boundary_name=extract_boundary_name(online_geojson)
                or location_result.location_name,
                boundary_match_reason=online_match_reason,
                climate_region_type=infer_location_climate_region(location_result),
                db_boundary_id=cached_boundary_id,
                polygon=polygon,
                geojson=online_geojson,
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
    boundaries_by_id: dict[int, AdministrativeBoundary] = {}

    for candidate in candidates:
        normalized_candidate = normalize_boundary_candidate(candidate.value)

        if not normalized_candidate:
            continue

        for mode in ("exact_name", "fuzzy_name", "alias"):
            if mode != "exact_name" and len(normalized_candidate) < 3:
                continue

            matching_boundaries = query_database_boundaries(
                session,
                normalized_candidate,
                mode=mode,
            )

            for boundary in matching_boundaries:
                boundaries_by_id[boundary.id] = boundary

            for boundary in matching_boundaries:
                match = match_boundary_candidates(boundary, [candidate])

                if match:
                    return boundary, f"database hierarchy {match[1]}"

    for candidate in candidates:
        for boundary in boundaries_by_id.values():
            match = match_boundary_candidates(boundary, [candidate])

            if match:
                return boundary, f"database hierarchy {match[1]}"

    return None, "no database boundary matched search metadata"


def query_database_boundaries(
    session: Session,
    normalized_candidate: str,
    *,
    mode: str,
) -> list[AdministrativeBoundary]:
    if mode == "exact_name":
        filters = [
            AdministrativeBoundary.name.ilike(normalized_candidate),
            AdministrativeBoundary.country.ilike(normalized_candidate),
        ]
    elif mode == "alias":
        filters = [
            cast(AdministrativeBoundary.aliases, String).ilike(
                f"%{normalized_candidate}%",
            ),
        ]
    else:
        filters = [
            AdministrativeBoundary.name.ilike(f"%{normalized_candidate}%"),
        ]

    return (
        session.query(AdministrativeBoundary)
        .filter(or_(*filters))
        .order_by(AdministrativeBoundary.name.asc())
        .limit(60)
        .all()
    )


def normalize_boundary_candidate(value: str) -> str:
    return " ".join(value.strip().lower().replace(",", " ").split())


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


def cache_online_boundary(
    location_result: LocationResult,
    geojson: dict[str, object],
    match_reason: str | None,
) -> int | None:
    if not is_database_configured() or SessionLocal is None:
        return None

    boundary_name = online_boundary_record_name(location_result)
    aliases = online_boundary_aliases(location_result)
    source = online_boundary_source(match_reason)

    try:
        with SessionLocal() as session:
            existing = (
                session.query(AdministrativeBoundary)
                .filter(AdministrativeBoundary.name == boundary_name)
                .one_or_none()
            )

            if existing:
                existing.aliases = aliases
                existing.country = location_result.country
                existing.region_type = location_result.place_type or "online_boundary"
                existing.climate_region_type = infer_location_climate_region(
                    location_result,
                )
                existing.source = source
                existing.geometry_geojson = geojson
                session.commit()
                return existing.id

            boundary = AdministrativeBoundary(
                name=boundary_name,
                aliases=aliases,
                country=location_result.country,
                region_type=location_result.place_type or "online_boundary",
                climate_region_type=infer_location_climate_region(location_result),
                source=source,
                geometry_geojson=geojson,
            )
            session.add(boundary)
            session.commit()
            session.refresh(boundary)
            return boundary.id
    except SQLAlchemyError:
        return None


def online_boundary_record_name(location_result: LocationResult) -> str:
    parts = [
        location_result.locality,
        location_result.district,
        location_result.city,
        location_result.region,
        location_result.country,
    ]
    unique_parts = []

    for part in parts:
        if part and part not in unique_parts:
            unique_parts.append(part)

    if unique_parts:
        return " / ".join(unique_parts)

    return location_result.location_name


def online_boundary_aliases(location_result: LocationResult) -> list[str]:
    aliases = [
        location_result.location_name,
        location_result.locality,
        location_result.district,
        location_result.city,
        location_result.region,
        location_result.country,
        location_result.hierarchy_label,
    ]

    return sorted(set(filter(None, aliases)))


def online_boundary_source(match_reason: str | None) -> str:
    return f"online_osm:{match_reason or 'nominatim'}"[:120]


def infer_location_climate_region(location_result: LocationResult) -> str:
    region_text = " ".join(
        filter(
            None,
            [
                location_result.region,
                location_result.country,
                location_result.hierarchy_label,
            ],
        ),
    ).lower()

    if any(term in region_text for term in ["india", "mumbai", "maharashtra"]):
        return "tropical_humid"

    if any(term in region_text for term in ["spain", "madrid", "turkey", "istanbul"]):
        return "mediterranean"

    if any(term in region_text for term in ["united kingdom", "england", "ireland"]):
        return "temperate_oceanic"

    return "continental"


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
