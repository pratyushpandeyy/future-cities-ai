from app.models.schemas import (
    LocationResult,
    ScenarioInput,
    ScenarioScoreRequest,
    ScenarioScoreResponse,
    ScoreBreakdown,
)


CLIMATE_REGION_PRESETS = {
    "tropical_humid": {
        "base_heat": 62,
        "base_flood": 58,
        "base_air": 54,
        "base_green_stress": 48,
        "base_water": 50,
        "base_livability": 78,
        "heat_sensitivity": 1.22,
        "flood_sensitivity": 1.18,
        "comfort_sensitivity": 1.18,
        "night_heat_retention": 1.14,
    },
    "mediterranean": {
        "base_heat": 42,
        "base_flood": 34,
        "base_air": 42,
        "base_green_stress": 45,
        "base_water": 58,
        "base_livability": 84,
        "heat_sensitivity": 1.18,
        "flood_sensitivity": 0.86,
        "comfort_sensitivity": 1.08,
        "night_heat_retention": 0.98,
    },
    "arid": {
        "base_heat": 72,
        "base_flood": 24,
        "base_air": 56,
        "base_green_stress": 70,
        "base_water": 82,
        "base_livability": 68,
        "heat_sensitivity": 1.35,
        "flood_sensitivity": 0.7,
        "comfort_sensitivity": 1.34,
        "night_heat_retention": 1.05,
    },
    "temperate_oceanic": {
        "base_heat": 24,
        "base_flood": 48,
        "base_air": 28,
        "base_green_stress": 26,
        "base_water": 32,
        "base_livability": 86,
        "heat_sensitivity": 0.78,
        "flood_sensitivity": 1.08,
        "comfort_sensitivity": 0.76,
        "night_heat_retention": 0.82,
    },
    "continental": {
        "base_heat": 40,
        "base_flood": 36,
        "base_air": 38,
        "base_green_stress": 42,
        "base_water": 46,
        "base_livability": 80,
        "heat_sensitivity": 1.0,
        "flood_sensitivity": 0.96,
        "comfort_sensitivity": 1.0,
        "night_heat_retention": 0.92,
    },
    "highland": {
        "base_heat": 32,
        "base_flood": 42,
        "base_air": 34,
        "base_green_stress": 34,
        "base_water": 45,
        "base_livability": 84,
        "heat_sensitivity": 0.9,
        "flood_sensitivity": 1.0,
        "comfort_sensitivity": 0.88,
        "night_heat_retention": 0.84,
    },
}


def compute_scenario_score(
    payload: ScenarioScoreRequest | ScenarioInput,
    location: LocationResult,
) -> ScenarioScoreResponse:
    climate_region_type = classify_climate_region(location)
    preset = CLIMATE_REGION_PRESETS[climate_region_type]
    warming_pressure = max(0.0, payload.warmingLevel - 1.0)
    year_pressure = max(0.0, payload.year - 2025) / 25
    season = payload.season.strip().lower()
    time_of_day = payload.timeOfDay.strip().lower()
    overlay_types = [overlay.lower() for overlay in payload.overlayTypes]
    coastal = is_coastal(location)
    dense_urban = is_dense_urban(location)

    heat_season = {"summer": 14, "winter": -9, "monsoon": 1, "spring": 4}.get(
        season,
        4,
    )
    flood_season = {"monsoon": 20, "winter": -4, "summer": -2, "spring": 3}.get(
        season,
        3,
    )
    comfort_season = {"winter": 10, "summer": -13, "monsoon": -6, "spring": 4}.get(
        season,
        0,
    )
    time_heat = {
        "afternoon": 8,
        "peak heat": 12,
        "night": 4 if dense_urban else -2,
        "morning": -4,
    }.get(time_of_day, 0)

    heat_score = (
        preset["base_heat"]
        + warming_pressure * 16 * preset["heat_sensitivity"]
        + year_pressure * 6
        + heat_season
        + time_heat * preset["night_heat_retention"]
        + (7 if dense_urban else 0)
        + (4 if "heat risk" in overlay_types else 0)
    )
    flood_score = (
        preset["base_flood"]
        + warming_pressure * 5 * preset["flood_sensitivity"]
        + year_pressure * 5
        + flood_season
        + (10 if coastal else 0)
        + (5 if "flood risk" in overlay_types else 0)
    )
    air_quality_score = (
        preset["base_air"]
        + heat_score * 0.12
        + warming_pressure * 3
        + (4 if dense_urban else 0)
    )
    green_cover_stress_score = (
        preset["base_green_stress"]
        + warming_pressure * 8
        + year_pressure * 3
        - (5 if "green cover" in overlay_types else 0)
    )
    water_stress_score = (
        preset["base_water"]
        + warming_pressure * 10
        + (8 if season == "summer" else -4 if season == "monsoon" else 0)
        + (4 if "water stress" in overlay_types else 0)
    )
    outdoor_comfort_score = (
        92
        - heat_score * 0.5 * preset["comfort_sensitivity"]
        - flood_score * 0.16
        - air_quality_score * 0.12
        + comfort_season
    )
    livability_stress_score = (
        heat_score * 0.34
        + flood_score * 0.2
        + air_quality_score * 0.13
        + green_cover_stress_score * 0.14
        + water_stress_score * 0.19
    )
    livability_score = preset["base_livability"] - livability_stress_score * 0.34

    breakdown = ScoreBreakdown(
        heat_score=round_score(heat_score),
        flood_score=round_score(flood_score),
        outdoor_comfort_score=round_score(outdoor_comfort_score),
        air_quality_score=round_score(air_quality_score),
        green_cover_stress_score=round_score(green_cover_stress_score),
        water_stress_score=round_score(water_stress_score),
        livability_stress_score=round_score(livability_stress_score),
        warming_pressure=round(warming_pressure, 2),
        year_pressure=round(year_pressure, 2),
        season_modifier=payload.season,
        time_of_day_modifier=payload.timeOfDay,
    )
    dominant_driver = get_dominant_driver(
        {
            "heat retention": heat_score,
            "flood exposure": flood_score,
            "air quality pressure": air_quality_score,
            "green cover stress": green_cover_stress_score,
            "water stress": water_stress_score,
        },
    )

    return ScenarioScoreResponse(
        location=location,
        livability_score=round_score(livability_score),
        heat_risk=risk_label(heat_score),
        flood_risk=risk_label(flood_score),
        outdoor_comfort=comfort_label(outdoor_comfort_score),
        air_quality_proxy=risk_label(air_quality_score),
        green_cover=f"{max(4, round(44 - green_cover_stress_score * 0.36))}%",
        green_cover_stress=risk_label(green_cover_stress_score),
        water_stress=risk_label(water_stress_score),
        livability_stress=risk_label(livability_stress_score),
        wet_bulb_anomaly=round(payload.warmingLevel * 0.64 + heat_season * 0.024, 1),
        climate_region_type=climate_region_type,
        score_breakdown=breakdown,
        dominant_risk_driver=dominant_driver,
        summary=build_summary(
            location=location,
            climate_region_type=climate_region_type,
            dominant_driver=dominant_driver,
            heat_risk=risk_label(heat_score),
            flood_risk=risk_label(flood_score),
            comfort=comfort_label(outdoor_comfort_score),
            dense_urban=dense_urban,
            coastal=coastal,
            time_of_day=payload.timeOfDay,
        ),
    )


def classify_climate_region(location: LocationResult) -> str:
    text = " ".join(
        filter(
            None,
            [
                location.location_name,
                location.region,
                location.climate_zone,
                location.country,
                location.hierarchy_label,
            ],
        ),
    ).lower()

    if any(term in text for term in ["mumbai", "maharashtra", "tropical", "humid"]):
        return "tropical_humid"
    if any(term in text for term in ["bangalore", "bengaluru", "karnataka", "plateau"]):
        return "highland"
    if any(term in text for term in ["madrid", "istanbul", "marmara", "spain", "turkiye", "türkiye", "mediterranean"]):
        return "mediterranean"
    if any(term in text for term in ["manchester", "england", "britain", "temperate", "oceanic", "maritime"]):
        return "temperate_oceanic"
    if any(term in text for term in ["desert", "arid", "saudi", "oman", "egypt"]):
        return "arid"

    return "continental"


def is_coastal(location: LocationResult) -> bool:
    text = f"{location.location_name} {location.region} {location.climate_zone}".lower()
    return any(
        term in text
        for term in ["coastal", "mumbai", "marmara", "istanbul", "maritime", "oceanic"]
    )


def is_dense_urban(location: LocationResult) -> bool:
    text = f"{location.location_name} {location.region} {location.place_type}".lower()
    return any(
        term in text
        for term in [
            "mumbai",
            "bangalore",
            "bengaluru",
            "madrid",
            "istanbul",
            "manchester",
            "urban",
            "neighborhood",
            "locality",
        ]
    )


def get_dominant_driver(scores: dict[str, float]) -> str:
    return max(scores.items(), key=lambda item: item[1])[0]


def build_summary(
    *,
    location: LocationResult,
    climate_region_type: str,
    dominant_driver: str,
    heat_risk: str,
    flood_risk: str,
    comfort: str,
    dense_urban: bool,
    coastal: bool,
    time_of_day: str,
) -> str:
    urban_phrase = "dense urban heat retention" if dense_urban else "regional exposure"
    coastal_phrase = " and coastal flood amplification" if coastal else ""

    return (
        f"{location.region} is treated as a {climate_region_type.replace('_', ' ')} "
        f"climate region. {dominant_driver.capitalize()}, {urban_phrase}{coastal_phrase} "
        f"drive {heat_risk.lower()} heat risk, {flood_risk.lower()} flood risk, "
        f"and {comfort.lower()} outdoor comfort during {time_of_day.lower()} conditions."
    )


def risk_label(score: float) -> str:
    if score >= 76:
        return "High"
    if score >= 52:
        return "Elevated"
    if score >= 30:
        return "Moderate"
    return "Low"


def comfort_label(score: float) -> str:
    if score >= 70:
        return "High"
    if score >= 48:
        return "Moderate"
    return "Low"


def round_score(value: float) -> int:
    return max(0, min(100, round(value)))
