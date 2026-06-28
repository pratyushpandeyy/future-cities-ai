import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from app.models.schemas import LocationResult
from app.services.boundary_resolution import (
    BoundaryCandidate,
    boundary_search_hierarchy,
    normalize_boundary_text,
)

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")


NOMINATIM_BOUNDARY_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_USER_AGENT = os.getenv(
    "NOMINATIM_USER_AGENT",
    "future-cities-ai-dev/0.1",
)
ONLINE_BOUNDARY_LOOKUP_ENABLED = os.getenv(
    "ONLINE_BOUNDARY_LOOKUP_ENABLED",
    "true",
).lower() in {"1", "true", "yes", "on"}


def fetch_online_boundary(
    location: str,
    location_result: LocationResult,
    *,
    timeout: int = 6,
) -> tuple[dict[str, object] | None, str | None]:
    if not ONLINE_BOUNDARY_LOOKUP_ENABLED:
        return None, "online boundary lookup disabled"

    for candidate in online_boundary_candidates(location, location_result):
        payload = query_nominatim_boundary(candidate.value, timeout=timeout)
        geojson = geojson_from_nominatim_payload(payload)

        if geojson:
            return geojson, f"online OSM/Nominatim polygon match: {candidate.level}={candidate.value}"

    return None, "no online OSM/Nominatim polygon matched search hierarchy"


def online_boundary_candidates(
    location: str,
    location_result: LocationResult,
) -> list[BoundaryCandidate]:
    candidates = boundary_search_hierarchy(location, location_result)
    filtered = []
    seen = set()

    for candidate in candidates:
        normalized = normalize_boundary_text(candidate.value)

        if not normalized or normalized in seen:
            continue

        if candidate.level in {"country"}:
            continue

        seen.add(normalized)
        filtered.append(candidate)

    return filtered


def query_nominatim_boundary(
    query: str,
    *,
    timeout: int,
) -> object | None:
    params = urlencode(
        {
            "q": query,
            "format": "jsonv2",
            "polygon_geojson": 1,
            "addressdetails": 1,
            "limit": 3,
        },
    )
    request = Request(
        f"{NOMINATIM_BOUNDARY_URL}?{params}",
        headers={"User-Agent": NOMINATIM_USER_AGENT},
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError):
        return None


def geojson_from_nominatim_payload(payload: object | None) -> dict[str, object] | None:
    if not isinstance(payload, list):
        return None

    for item in payload:
        if not isinstance(item, dict):
            continue

        geojson = item.get("geojson")

        if not is_supported_boundary_geometry(geojson):
            continue

        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {
                        "name": item.get("name") or item.get("display_name"),
                        "display_name": item.get("display_name"),
                        "osm_id": item.get("osm_id"),
                        "osm_type": item.get("osm_type"),
                        "class": item.get("class"),
                        "type": item.get("type"),
                        "source": "nominatim_openstreetmap",
                    },
                    "geometry": geojson,
                },
            ],
        }

    return None


def is_supported_boundary_geometry(geojson: object) -> bool:
    if not isinstance(geojson, dict):
        return False

    geometry_type = geojson.get("type")
    coordinates = geojson.get("coordinates")

    return geometry_type in {"Polygon", "MultiPolygon"} and isinstance(
        coordinates,
        list,
    )
