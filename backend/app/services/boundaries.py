import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import AdministrativeBoundary
from app.db.session import SessionLocal, is_database_configured
from app.models.schemas import LocationResult, RegionBoundaryResponse
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


def get_region_boundary(location: str) -> RegionBoundaryResponse:
    location_result = resolve_location(location)
    database_boundary = find_database_boundary(location, location_result)

    if database_boundary:
        polygon = extract_polygon_ring(database_boundary.geometry_geojson)

        if polygon:
            return RegionBoundaryResponse(
                location=location_result,
                boundary_source="real_geojson",
                polygon=polygon,
                geojson=database_boundary.geometry_geojson,
            )

    boundary_file = find_boundary_file(location, location_result)

    if boundary_file:
        geojson = load_boundary_geojson(boundary_file)
        polygon = extract_polygon_ring(geojson)

        if polygon:
            return RegionBoundaryResponse(
                location=location_result,
                boundary_source="real_geojson",
                polygon=polygon,
                geojson=geojson,
            )

    return simulated_boundary(location_result)


def find_database_boundary(
    location: str,
    location_result: LocationResult,
) -> AdministrativeBoundary | None:
    if not is_database_configured() or SessionLocal is None:
        return None

    try:
        with SessionLocal() as session:
            return match_database_boundary(session, location, location_result)
    except SQLAlchemyError:
        return None


def match_database_boundary(
    session: Session,
    location: str,
    location_result: LocationResult,
) -> AdministrativeBoundary | None:
    searchable_text = build_searchable_text(location, location_result)
    boundaries = session.query(AdministrativeBoundary).all()

    for boundary in boundaries:
        boundary_terms = [boundary.name, boundary.country or "", *boundary.aliases]

        if any(term.strip().lower() in searchable_text for term in boundary_terms if term):
            return boundary

    return None


def find_boundary_file(location: str, location_result: LocationResult) -> str | None:
    searchable_text = build_searchable_text(location, location_result)

    for alias, boundary_file in BOUNDARY_ALIASES.items():
        if alias in searchable_text:
            return boundary_file

    return None


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
        polygon=polygon,
    )
