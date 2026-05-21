from app.models.schemas import (
    ClimateInteractionRequest,
    ClimateInteractionResponse,
)
from app.services.climate_engine import (
    compute_scenario_score,
    is_coastal,
    is_dense_urban,
)
from app.services.simulation import resolve_location


INTERACTION_MODEL_VERSION = "urban_system_interactions_v1"


def compute_composite_risk(
    payload: ClimateInteractionRequest,
) -> ClimateInteractionResponse:
    location_name = payload.location or payload.scenario.location
    location = resolve_location(location_name)
    scenario = payload.scenario.model_copy(update={"location": location.location_name})
    score = compute_scenario_score(scenario, location)
    breakdown = score.score_breakdown
    active_layers = {layer.strip().lower() for layer in payload.active_layers}
    coastal_exposure = 1.0 if is_coastal(location) else 0.0
    dense_urban = 1.0 if is_dense_urban(location) else 0.0
    population_density = density_proxy(location, dense_urban)
    green_buffer = green_buffer_score(score.green_cover)
    selected_cell_pressure = (
        payload.selected_climate_cell.normalized_score / 100
        if payload.selected_climate_cell
        else 0.0
    )

    interaction_weights = {
        "heat_green_compound": 0.24,
        "flood_density_infrastructure": 0.2,
        "coastal_humidity_night_heat": 0.16,
        "water_livability_resilience": 0.18,
        "air_quality_heat_feedback": 0.12,
        "selected_cell_signal": 0.1,
    }
    resilience_modifiers = {
        "green_cover_buffer": round(green_buffer, 2),
        "coastal_exposure": coastal_exposure,
        "population_density_proxy": round(population_density, 2),
        "active_layer_focus": layer_focus_modifier(active_layers),
    }

    heat_green_compound = (
        breakdown.heat_score / 100
        * (1 - green_buffer)
        * interaction_weights["heat_green_compound"]
    )
    flood_density_compound = (
        breakdown.flood_score / 100
        * population_density
        * interaction_weights["flood_density_infrastructure"]
    )
    coastal_heat_compound = (
        coastal_exposure
        * breakdown.heat_score / 100
        * interaction_weights["coastal_humidity_night_heat"]
    )
    water_resilience_compound = (
        breakdown.water_stress_score / 100
        * (1 - green_buffer * 0.45)
        * interaction_weights["water_livability_resilience"]
    )
    air_heat_compound = (
        breakdown.air_quality_score / 100
        * breakdown.heat_score / 100
        * interaction_weights["air_quality_heat_feedback"]
    )
    cell_compound = selected_cell_pressure * interaction_weights["selected_cell_signal"]
    active_layer_modifier = layer_focus_modifier(active_layers)
    total_compound_pressure = (
        heat_green_compound
        + flood_density_compound
        + coastal_heat_compound
        + water_resilience_compound
        + air_heat_compound
        + cell_compound
    ) * active_layer_modifier

    infrastructure_pressure = clamp_score(
        breakdown.flood_score * 0.42
        + breakdown.water_stress_score * 0.22
        + population_density * 26
        + total_compound_pressure * 42,
    )
    human_exposure_score = clamp_score(
        breakdown.heat_score * 0.38
        + breakdown.air_quality_score * 0.2
        + (1 - green_buffer) * 24
        + population_density * 18
        + selected_cell_pressure * 12,
    )
    resilience_score = clamp_score(
        88
        - breakdown.livability_stress_score * 0.38
        - total_compound_pressure * 52
        + green_buffer * 18
        - coastal_exposure * 5,
    )
    composite_risk_score = clamp_score(
        breakdown.livability_stress_score * 0.42
        + infrastructure_pressure * 0.25
        + human_exposure_score * 0.25
        + total_compound_pressure * 34
        - green_buffer * 8,
    )
    cascading_risks = build_cascading_risks(
        heat_green_compound=heat_green_compound,
        flood_density_compound=flood_density_compound,
        coastal_heat_compound=coastal_heat_compound,
        water_resilience_compound=water_resilience_compound,
        air_heat_compound=air_heat_compound,
        selected_cell_pressure=selected_cell_pressure,
    )
    mitigation_factors = build_mitigation_factors(
        green_buffer=green_buffer,
        coastal_exposure=coastal_exposure,
        dense_urban=dense_urban,
        active_layers=active_layers,
    )

    return ClimateInteractionResponse(
        composite_risk_score=composite_risk_score,
        dominant_interaction_chain=dominant_chain(cascading_risks),
        resilience_score=resilience_score,
        infrastructure_pressure=infrastructure_pressure,
        human_exposure_score=human_exposure_score,
        cascading_risks=cascading_risks,
        mitigation_factors=mitigation_factors,
        visual_indicators=visual_indicators(
            composite_risk_score=composite_risk_score,
            resilience_score=resilience_score,
            cascading_risks=cascading_risks,
        ),
        active_interaction_model=INTERACTION_MODEL_VERSION,
        interaction_weights=interaction_weights,
        resilience_modifiers=resilience_modifiers,
        cascading_chain_depth=len(cascading_risks),
    )


def density_proxy(location, dense_urban: float) -> float:
    place_type = (location.place_type or "").lower()
    text = " ".join(
        filter(None, [location.location_name, location.region, location.city]),
    ).lower()

    if dense_urban:
        return 0.86
    if any(term in place_type for term in ["neighborhood", "locality", "district"]):
        return 0.74
    if any(term in text for term in ["urban", "metro", "city"]):
        return 0.68

    return 0.46


def green_buffer_score(green_cover: str) -> float:
    try:
        percentage = int(green_cover.replace("%", "").strip())
    except ValueError:
        percentage = 18

    return max(0.08, min(0.62, percentage / 100))


def layer_focus_modifier(active_layers: set[str]) -> float:
    compounding_layers = {
        "heat risk",
        "flood risk",
        "air quality",
        "water stress",
        "livability stress",
    }
    overlap = len(active_layers.intersection(compounding_layers))

    return 1 + min(0.18, overlap * 0.045)


def build_cascading_risks(
    *,
    heat_green_compound: float,
    flood_density_compound: float,
    coastal_heat_compound: float,
    water_resilience_compound: float,
    air_heat_compound: float,
    selected_cell_pressure: float,
) -> list[str]:
    risks: list[tuple[float, str]] = [
        (
            heat_green_compound,
            "High heat plus weak green cover worsens outdoor comfort.",
        ),
        (
            flood_density_compound,
            "Flood exposure in dense urban fabric amplifies infrastructure pressure.",
        ),
        (
            coastal_heat_compound,
            "Coastal humidity compounds nighttime heat retention.",
        ),
        (
            water_resilience_compound,
            "Water stress reduces livability resilience over time.",
        ),
        (
            air_heat_compound,
            "Heat and air-quality pressure reinforce human exposure.",
        ),
        (
            selected_cell_pressure * 0.1,
            "Selected climate cell adds localized surface stress to the system.",
        ),
    ]
    selected = [
        label
        for value, label in sorted(risks, key=lambda item: item[0], reverse=True)
        if value > 0.045
    ]

    return selected[:4] or ["No major cascading pathway dominates this scenario."]


def build_mitigation_factors(
    *,
    green_buffer: float,
    coastal_exposure: float,
    dense_urban: float,
    active_layers: set[str],
) -> list[str]:
    factors = []

    if green_buffer >= 0.24:
        factors.append("Green cover buffers local heat amplification.")
    else:
        factors.append("Expanding shade and canopy would improve heat resilience.")

    if coastal_exposure:
        factors.append("Coastal buffers and drainage capacity stabilize flood exposure.")

    if dense_urban:
        factors.append("Cool roofs, shaded transit, and night ventilation reduce exposure.")

    if "water stress" in active_layers:
        factors.append("Water-sensitive urban design improves resilience under hot years.")

    return factors


def visual_indicators(
    *,
    composite_risk_score: int,
    resilience_score: int,
    cascading_risks: list[str],
) -> list[str]:
    indicators = []

    if composite_risk_score >= 70:
        indicators.append("amplified risk")
    if resilience_score >= 58:
        indicators.append("buffered risk")
    if len(cascading_risks) >= 3:
        indicators.append("cascading pressure")

    return indicators or ["stable system"]


def dominant_chain(cascading_risks: list[str]) -> str:
    return cascading_risks[0] if cascading_risks else "No dominant interaction chain."


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))
