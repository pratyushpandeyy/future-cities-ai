from app.models.schemas import (
    LocationResult,
    RegionBoundaryResponse,
    ScenarioCompareRequest,
    ScenarioCompareResponse,
    ScenarioInput,
    ScenarioScoreRequest,
    ScenarioScoreResponse,
)
from app.services.geocoding import geocode_location


KNOWN_LOCATIONS = {
    "mumbai": {
        "location_name": "Mumbai",
        "region": "Maharashtra coastal region",
        "climate_zone": "Tropical coastal megacity",
        "latitude": 19.076,
        "longitude": 72.8777,
        "base_livability": 82,
        "base_heat": 78,
        "base_flood": 62,
        "green_cover": 14,
    },
    "bangalore": {
        "location_name": "Bangalore",
        "region": "Karnataka region",
        "climate_zone": "Deccan plateau urban zone",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "base_livability": 88,
        "base_heat": 42,
        "base_flood": 42,
        "green_cover": 22,
    },
    "madrid": {
        "location_name": "Madrid",
        "region": "Community of Madrid",
        "climate_zone": "Mediterranean continental basin",
        "latitude": 40.4168,
        "longitude": -3.7038,
        "base_livability": 91,
        "base_heat": 62,
        "base_flood": 22,
        "green_cover": 31,
    },
    "istanbul": {
        "location_name": "Istanbul",
        "region": "Marmara region",
        "climate_zone": "Bosphorus maritime transition",
        "latitude": 41.0082,
        "longitude": 28.9784,
        "base_livability": 79,
        "base_heat": 42,
        "base_flood": 42,
        "green_cover": 18,
    },
    "manchester": {
        "location_name": "Manchester",
        "region": "Greater Manchester / North West England",
        "climate_zone": "Temperate maritime urban corridor",
        "latitude": 53.4808,
        "longitude": -2.2426,
        "base_livability": 86,
        "base_heat": 22,
        "base_flood": 42,
        "green_cover": 27,
    },
}

KNOWN_BOUNDARIES = {
    "mumbai": [
        [72.0, 21.2],
        [73.5, 21.0],
        [74.4, 20.3],
        [74.1, 18.9],
        [73.2, 17.4],
        [72.2, 16.9],
        [71.7, 18.5],
        [71.6, 20.1],
        [72.0, 21.2],
    ],
    "bangalore": [
        [74.2, 15.0],
        [76.4, 15.4],
        [78.8, 14.8],
        [79.0, 12.3],
        [77.8, 10.8],
        [75.5, 11.0],
        [74.0, 12.6],
        [74.2, 15.0],
    ],
    "madrid": [
        [-4.8, 41.1],
        [-3.7, 41.3],
        [-2.8, 40.8],
        [-2.9, 39.9],
        [-3.9, 39.5],
        [-4.9, 40.0],
        [-4.8, 41.1],
    ],
    "istanbul": [
        [26.2, 41.8],
        [28.4, 42.0],
        [30.6, 41.7],
        [30.3, 40.4],
        [28.5, 40.0],
        [26.4, 40.5],
        [26.2, 41.8],
    ],
    "manchester": [
        [-3.5, 54.0],
        [-2.2, 54.1],
        [-1.4, 53.7],
        [-1.7, 53.0],
        [-2.7, 52.8],
        [-3.6, 53.3],
        [-3.5, 54.0],
    ],
}


def stable_hash(value: str) -> int:
    return sum(ord(character) for character in value.strip().lower())


def normalize_location(value: str) -> str:
    return value.strip().lower()


def risk_label(score: float) -> str:
    if score >= 76:
        return "High"
    if score >= 52:
        return "Elevated"
    if score >= 30:
        return "Moderate"
    return "Low"


def comfort_label(score: float) -> str:
    if score >= 72:
        return "High"
    if score >= 52:
        return "Moderate"
    return "Low"


def search_location(query: str) -> LocationResult:
    normalized = normalize_location(query)
    known = KNOWN_LOCATIONS.get(normalized)

    if known:
        return LocationResult(
            location_name=known["location_name"],
            region=known["region"],
            climate_zone=known["climate_zone"],
            latitude=known["latitude"],
            longitude=known["longitude"],
            city=known["location_name"],
            country=known.get("country"),
            hierarchy_label=f"{known['location_name']} / {known['region']}",
            place_type="place",
            geocoder_provider="simulated",
            known=True,
            extrapolated=False,
            location_id=normalized,
        )

    fallback = query.strip() or "Unknown location"
    hash_value = stable_hash(fallback)
    latitude = round(8 + (hash_value % 58) * 0.72, 4)
    longitude = round(-18 + (hash_value % 125) * 1.28, 4)

    return LocationResult(
        location_name=fallback,
        region=f"Simulated Region {chr(65 + hash_value % 6)}",
        climate_zone=[
            "Tropical urban belt",
            "Semi-arid transition zone",
            "Temperate maritime cell",
            "Humid subtropical corridor",
        ][hash_value % 4],
        latitude=latitude,
        longitude=longitude,
        locality=fallback,
        hierarchy_label=f"{fallback} / Simulated regional climate cell",
        place_type="extrapolated_location",
        geocoder_provider="simulated",
        known=False,
        extrapolated=True,
        location_id=f"sim-{hash_value % 10000}",
    )


def resolve_location(location: str) -> LocationResult:
    return geocode_location(location) or search_location(location)


def get_location_baseline(location: str) -> dict[str, float | int | str]:
    normalized = normalize_location(location)
    known = KNOWN_LOCATIONS.get(normalized)

    if known:
        return known

    hash_value = stable_hash(location)
    return {
        "base_livability": 78 - hash_value % 18,
        "base_heat": 38 + hash_value % 34,
        "base_flood": 30 + hash_value % 38,
        "green_cover": 18 + hash_value % 16,
    }


def season_adjustments(season: str) -> tuple[int, int, int]:
    normalized = season.strip().lower()
    if normalized == "summer":
        return 10, 0, -8
    if normalized == "monsoon":
        return 0, 16, -5
    if normalized == "winter":
        return -8, -3, 7
    return 2, 2, 0


def time_adjustment(time_of_day: str) -> int:
    normalized = time_of_day.strip().lower()
    if normalized in {"afternoon", "peak heat"}:
        return 7
    if normalized == "night":
        return -3
    return 0


def score_scenario(payload: ScenarioScoreRequest | ScenarioInput) -> ScenarioScoreResponse:
    location = resolve_location(payload.location)
    baseline = get_location_baseline(payload.location)
    heat_season, flood_season, comfort_season = season_adjustments(payload.season)
    heat_pressure = max(0, payload.warmingLevel - 1.0)
    year_pressure = max(0, payload.year - 2025) / 25

    heat_score = (
        float(baseline["base_heat"])
        + heat_pressure * 14
        + year_pressure * 6
        + heat_season
        + time_adjustment(payload.timeOfDay)
    )
    flood_score = float(baseline["base_flood"]) + year_pressure * 5 + flood_season
    comfort_score = max(
        18,
        86 - payload.warmingLevel * 15 + comfort_season - time_adjustment(payload.timeOfDay),
    )
    livability_score = max(
        42,
        round(
            float(baseline["base_livability"])
            - heat_pressure * 6
            - max(0, flood_score - 50) * 0.05
        ),
    )
    green_cover = max(4, min(48, round(float(baseline["green_cover"]) - heat_pressure * 1.5)))
    wet_bulb_anomaly = round(payload.warmingLevel * 0.72 + heat_season * 0.025, 1)

    return ScenarioScoreResponse(
        location=location,
        livability_score=livability_score,
        heat_risk=risk_label(heat_score),
        flood_risk=risk_label(flood_score),
        outdoor_comfort=comfort_label(comfort_score),
        green_cover=f"{green_cover}%",
        wet_bulb_anomaly=wet_bulb_anomaly,
        summary=(
            f"{location.region} shows simulated {risk_label(heat_score).lower()} heat risk "
            f"and {comfort_label(comfort_score).lower()} outdoor comfort in {payload.year}."
        ),
    )


def compare_scenarios(payload: ScenarioCompareRequest) -> ScenarioCompareResponse:
    score_a = score_scenario(payload.scenarioA)
    score_b = score_scenario(payload.scenarioB)
    heat_increase = max(
        0,
        round((payload.scenarioB.warmingLevel - payload.scenarioA.warmingLevel) * 16),
    )
    flood_increase = max(0, risk_numeric(score_b.flood_risk) - risk_numeric(score_a.flood_risk))
    comfort_decline = max(
        0,
        comfort_numeric(score_a.outdoor_comfort) - comfort_numeric(score_b.outdoor_comfort),
    )
    livability_decline = max(0, score_a.livability_score - score_b.livability_score)

    return ScenarioCompareResponse(
        heat_increase=heat_increase,
        flood_increase=flood_increase,
        comfort_decline=comfort_decline,
        livability_decline=livability_decline,
        explanation=(
            "Scenario B produces higher simulated climate pressure than Scenario A, "
            "with weaker outdoor comfort and lower livability under the warmer pathway."
        ),
    )


def risk_numeric(label: str) -> int:
    return {"Low": 1, "Moderate": 2, "Elevated": 3, "High": 4}.get(label, 2)


def comfort_numeric(label: str) -> int:
    return {"Low": 1, "Moderate": 2, "High": 3}.get(label, 2)


def region_boundary(location: str) -> RegionBoundaryResponse:
    normalized = normalize_location(location)
    location_result = resolve_location(location)
    known_polygon = KNOWN_BOUNDARIES.get(normalized)

    if known_polygon:
        polygon = known_polygon
    elif location_result.bbox:
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
        boundary_source="simulated",
        polygon=polygon,
    )
