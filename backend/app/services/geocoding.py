import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from app.models.schemas import LocationResult

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

MAPBOX_GEOCODING_TOKEN = os.getenv("MAPBOX_GEOCODING_TOKEN") or os.getenv(
    "MAPBOX_ACCESS_TOKEN",
)
NOMINATIM_USER_AGENT = os.getenv(
    "NOMINATIM_USER_AGENT",
    "future-cities-ai-dev/0.1",
)


def geocode_location(query: str) -> LocationResult | None:
    cleaned_query = query.strip()

    if not cleaned_query:
        return None

    if MAPBOX_GEOCODING_TOKEN:
        mapbox_result = geocode_with_mapbox(cleaned_query)

        if mapbox_result:
            return mapbox_result

    return geocode_with_nominatim(cleaned_query)


def geocode_with_mapbox(query: str) -> LocationResult | None:
    encoded_query = quote(query)
    params = urlencode(
        {
            "access_token": MAPBOX_GEOCODING_TOKEN,
            "limit": 1,
            "types": "country,region,district,place,locality,neighborhood,address",
        },
    )
    url = (
        "https://api.mapbox.com/geocoding/v5/mapbox.places/"
        f"{encoded_query}.json?{params}"
    )
    payload = fetch_json(url)

    if not payload:
        return None

    features = payload.get("features") or []

    if not features:
        return None

    feature = features[0]
    center = feature.get("center") or []

    if len(center) < 2:
        return None

    context = feature.get("context") or []
    properties = feature.get("properties") or {}
    place_type = get_primary_place_type(feature.get("place_type"))
    locality = feature.get("text") if place_type in {"locality", "neighborhood"} else None
    district = (
        extract_context_text(context, "district")
        or (feature.get("text") if place_type == "district" else None)
    )
    city = (
        extract_context_text(context, "place")
        or (feature.get("text") if place_type == "place" else None)
    )
    region = (
        extract_context_text(context, "region")
        or district
        or city
        or feature.get("place_name")
        or "Mapped region unavailable"
    )
    country = extract_context_text(context, "country")
    hierarchy_label = build_hierarchy_label(
        [locality, district, city, region, country],
    )

    return LocationResult(
        location_name=feature.get("text") or query,
        region=region,
        climate_zone="Geocoded regional climate cell",
        latitude=float(center[1]),
        longitude=float(center[0]),
        locality=locality,
        district=district,
        city=city,
        country=country,
        hierarchy_label=hierarchy_label,
        place_type=place_type,
        geocoder_provider="mapbox",
        geocoder_metadata={
            "mapbox_id": feature.get("id"),
            "place_name": feature.get("place_name"),
            "accuracy": properties.get("accuracy"),
            "relevance": feature.get("relevance"),
            "place_types": feature.get("place_type") or [],
        },
        bbox=feature.get("bbox"),
        known=True,
        extrapolated=False,
        location_id=feature.get("id") or slugify(query),
    )


def geocode_with_nominatim(query: str) -> LocationResult | None:
    params = urlencode(
        {
            "q": query,
            "format": "jsonv2",
            "addressdetails": 1,
            "limit": 1,
        },
    )
    url = f"https://nominatim.openstreetmap.org/search?{params}"
    payload = fetch_json(url, user_agent=NOMINATIM_USER_AGENT)

    if not payload:
        return None

    result = payload[0]
    address = result.get("address") or {}
    place_type = detect_nominatim_place_type(result, address)
    locality = first_present(
        address,
        [
            "neighbourhood",
            "suburb",
            "quarter",
            "city_district",
            "borough",
            "residential",
        ],
    )
    district = first_present(address, ["county", "state_district", "district"])
    city = first_present(
        address,
        ["city", "town", "village", "municipality", "hamlet"],
    )
    region = (
        address.get("state")
        or address.get("region")
        or district
        or city
        or result.get("display_name")
        or "Mapped region unavailable"
    )
    country = address.get("country")
    location_name = (
        locality
        or city
        or result.get("name")
        or query
    )
    hierarchy_label = build_hierarchy_label(
        [locality, district, city, region, country],
    )

    return LocationResult(
        location_name=location_name,
        region=region,
        climate_zone="Geocoded regional climate cell",
        latitude=float(result["lat"]),
        longitude=float(result["lon"]),
        locality=locality,
        district=district,
        city=city,
        country=country,
        hierarchy_label=hierarchy_label,
        place_type=place_type,
        geocoder_provider="nominatim",
        geocoder_metadata={
            "osm_id": result.get("osm_id"),
            "osm_type": result.get("osm_type"),
            "class": result.get("class"),
            "type": result.get("type"),
            "importance": result.get("importance"),
            "display_name": result.get("display_name"),
        },
        bbox=parse_nominatim_bounding_box(result.get("boundingbox")),
        known=True,
        extrapolated=False,
        location_id=f"osm-{result.get('osm_type', 'place')}-{result.get('osm_id', slugify(query))}",
    )


def fetch_json(url: str, user_agent: str | None = None) -> object | None:
    headers = {}

    if user_agent:
        headers["User-Agent"] = user_agent

    try:
        request = Request(url, headers=headers)

        with urlopen(request, timeout=4) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, ValueError, OSError):
        return None


def extract_context_text(context: list[dict], context_type: str) -> str | None:
    for item in context:
        item_id = item.get("id", "")

        if item_id.startswith(context_type):
            return item.get("text")

    return None


def get_primary_place_type(place_types: list[str] | None) -> str | None:
    if not place_types:
        return None

    return place_types[0]


def first_present(address: dict, keys: list[str]) -> str | None:
    for key in keys:
        value = address.get(key)

        if value:
            return value

    return None


def build_hierarchy_label(parts: list[str | None]) -> str | None:
    unique_parts = []

    for part in parts:
        if part and part not in unique_parts:
            unique_parts.append(part)

    if not unique_parts:
        return None

    return " / ".join(unique_parts)


def detect_nominatim_place_type(result: dict, address: dict) -> str:
    if first_present(address, ["neighbourhood", "suburb", "quarter", "city_district"]):
        return "neighborhood"

    if first_present(address, ["borough", "county", "state_district", "district"]):
        return "district"

    if first_present(address, ["city", "town", "village", "municipality"]):
        return "place"

    return str(result.get("type") or result.get("class") or "location")


def parse_nominatim_bounding_box(value: list[str] | None) -> list[float] | None:
    if not value or len(value) != 4:
        return None

    south, north, west, east = value

    return [float(west), float(south), float(east), float(north)]


def slugify(value: str) -> str:
    return value.strip().lower().replace(" ", "-")
