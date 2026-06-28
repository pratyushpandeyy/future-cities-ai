import re

from app.models.schemas import AdvisorExtractedInputs


KNOWN_PLACE_NAMES = [
    "Whitefield",
    "Pune",
    "Manchester",
    "Mumbai",
    "Bangalore",
    "Bengaluru",
    "Chennai",
    "Hyderabad",
    "Delhi",
    "New Delhi",
    "Kolkata",
    "Ahmedabad",
    "Jaipur",
    "Istanbul",
    "Madrid",
    "Koramangala",
    "Bandra",
    "Kadikoy",
    "Chelsea",
    "Brooklyn",
    "London",
    "Toronto",
    "New York",
    "Varanasi",
    "Gurgaon",
    "Gurugram",
    "Noida",
]

PREFERENCE_KEYWORDS = {
    "Asthma / respiratory sensitivity": {
        "health": "respiratory sensitivity",
        "risk": "low",
    },
    "Heat sensitive": {
        "health": "heat sensitivity",
        "risk": "low",
    },
    "Elderly family": {
        "health": "family or elderly sensitivity",
        "risk": "low",
    },
    "Outdoor lifestyle": {
        "lifestyle": "outdoor lifestyle",
    },
    "Walking commute": {
        "lifestyle": "walking commute",
    },
    "Remote work": {
        "lifestyle": "remote work flexibility",
    },
    "Flood risk avoidant": {
        "risk": "low",
    },
    "Prefer cooler cities": {
        "lifestyle": "cooler city preference",
    },
    "Prefer coastal cities": {
        "lifestyle": "coastal preference",
    },
    "Budget sensitive": {
        "lifestyle": "budget sensitivity",
    },
}


def parse_advisor_query(
    query_text: str,
    selected_preferences: list[str],
    current_scenario_state: dict[str, object] | None = None,
) -> AdvisorExtractedInputs:
    text = query_text.strip()
    lower_text = text.lower()
    mentioned_locations = extract_locations(text)
    primary_location = (
        mentioned_locations[0]
        if mentioned_locations
        else str((current_scenario_state or {}).get("location") or "Mumbai")
    )
    comparison_locations = [
        location for location in mentioned_locations[1:] if location != primary_location
    ]
    year = extract_year(lower_text, current_scenario_state)
    warming_level = extract_warming(lower_text, current_scenario_state)
    season = extract_season(lower_text, current_scenario_state)
    health_constraints = extract_health_constraints(lower_text, selected_preferences)
    lifestyle_constraints = extract_lifestyle_constraints(lower_text, selected_preferences)
    relocation_intent = any(
        term in lower_text
        for term in ["move", "relocate", "consider", "instead", "should i live"]
    )
    risk_tolerance = infer_risk_tolerance(lower_text, selected_preferences)

    return AdvisorExtractedInputs(
        primary_location=primary_location,
        comparison_locations=comparison_locations,
        target_year=year,
        warming_level=warming_level,
        season=season,
        health_constraints=health_constraints,
        lifestyle_constraints=lifestyle_constraints,
        relocation_intent=relocation_intent or bool(comparison_locations),
        risk_tolerance=risk_tolerance,
    )


def extract_locations(query_text: str) -> list[str]:
    locations = []

    for place in KNOWN_PLACE_NAMES:
        if re.search(rf"\b{re.escape(place)}\b", query_text, flags=re.IGNORECASE):
            normalized = {
                "Bengaluru": "Bangalore",
                "New Delhi": "Delhi",
                "Gurugram": "Gurgaon",
            }.get(place, place)

            if normalized not in locations:
                locations.append(normalized)

    return locations


def extract_year(
    lower_text: str,
    current_scenario_state: dict[str, object] | None,
) -> int:
    match = re.search(r"\b(20[2-9][0-9]|2100)\b", lower_text)

    if match:
        return max(2025, min(2100, int(match.group(1))))

    return int((current_scenario_state or {}).get("year") or 2050)


def extract_warming(
    lower_text: str,
    current_scenario_state: dict[str, object] | None,
) -> float:
    match = re.search(r"\+?\s*([1-4](?:\.\d)?)\s*(?:°c|c|degrees|warming)", lower_text)

    if match:
        return max(1.0, min(4.0, float(match.group(1))))

    return float((current_scenario_state or {}).get("warming") or 2.7)


def extract_season(
    lower_text: str,
    current_scenario_state: dict[str, object] | None,
) -> str:
    if "monsoon" in lower_text:
        return "Monsoon"
    if "winter" in lower_text:
        return "Winter"
    if "spring" in lower_text:
        return "Spring"
    if "summer" in lower_text or "heat" in lower_text:
        return "Summer"

    return str((current_scenario_state or {}).get("season") or "Summer")


def extract_health_constraints(
    lower_text: str,
    selected_preferences: list[str],
) -> list[str]:
    constraints = []

    if "asthma" in lower_text or "respiratory" in lower_text:
        constraints.append("respiratory sensitivity")
    if "heat sensitive" in lower_text or "heat-sensitive" in lower_text:
        constraints.append("heat sensitivity")
    if "elderly" in lower_text or "children" in lower_text or "family" in lower_text:
        constraints.append("family or elderly sensitivity")

    for preference in selected_preferences:
        health = PREFERENCE_KEYWORDS.get(preference, {}).get("health")

        if health and health not in constraints:
            constraints.append(health)

    return constraints


def extract_lifestyle_constraints(
    lower_text: str,
    selected_preferences: list[str],
) -> list[str]:
    constraints = []

    if "walk" in lower_text or "commute" in lower_text:
        constraints.append("walking commute")
    if "remote" in lower_text:
        constraints.append("remote work flexibility")
    if "outdoor" in lower_text or "football" in lower_text:
        constraints.append("outdoor lifestyle")
    if "budget" in lower_text:
        constraints.append("budget sensitivity")

    for preference in selected_preferences:
        lifestyle = PREFERENCE_KEYWORDS.get(preference, {}).get("lifestyle")

        if lifestyle and lifestyle not in constraints:
            constraints.append(lifestyle)

    return constraints


def infer_risk_tolerance(lower_text: str, selected_preferences: list[str]) -> str:
    if "avoid" in lower_text or "asthma" in lower_text or "elderly" in lower_text:
        return "low"

    for preference in selected_preferences:
        risk = PREFERENCE_KEYWORDS.get(preference, {}).get("risk")

        if risk:
            return risk

    return "medium"
