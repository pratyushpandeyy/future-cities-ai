from app.models.schemas import (
    AdvisorQueryRequest,
    AdvisorResponse,
    ExplanationRequest,
    RecommendationRequest,
    ScenarioScoreRequest,
)
from app.services.advisor_parser import parse_advisor_query
from app.services.ai_explanation import explain_climate_impact
from app.services.climate_engine import compute_scenario_score
from app.services.recommendation_engine import generate_recommendations
from app.services.simulation import resolve_location


def answer_advisor_query(payload: AdvisorQueryRequest) -> AdvisorResponse:
    extracted = parse_advisor_query(
        query_text=payload.query_text,
        selected_preferences=payload.selected_preferences,
        current_scenario_state=payload.current_scenario_state,
    )
    location = resolve_location(extracted.primary_location)
    scenario = ScenarioScoreRequest(
        location=location.location_name,
        year=extracted.target_year,
        warmingLevel=extracted.warming_level,
        season=extracted.season,
        timeOfDay="Afternoon",
        overlayTypes=overlay_types_for(extracted),
    )
    score = compute_scenario_score(scenario, location)
    recommendations = generate_recommendations(
        recommendation_request_for(extracted.primary_location, extracted),
    )
    explanation = explain_climate_impact(
        ExplanationRequest(
            location=score.location.location_name,
            region=score.location.region,
            climate_region_type=score.climate_region_type,
            year=extracted.target_year,
            warming_level=extracted.warming_level,
            season=extracted.season,
            time_of_day="Afternoon",
            livability_score=score.livability_score,
            heat_risk=score.heat_risk,
            flood_risk=score.flood_risk,
            outdoor_comfort=score.outdoor_comfort,
            dominant_risk_driver=score.dominant_risk_driver,
        ),
    )
    comparison_locations = extracted.comparison_locations
    recommendation_pool = [
        *recommendations.recommended_regions,
        *recommendations.fallback_alternatives,
    ]
    comparison_recommendations = [
        region
        for region in recommendation_pool
        if region.location_name in comparison_locations
    ]
    suggested_comparisons = comparison_recommendations or recommendations.recommended_regions[:3]

    return AdvisorResponse(
        interpreted_query=build_interpreted_query(payload.query_text, extracted),
        extracted_inputs=extracted,
        primary_location_score=score,
        recommendation_summary=recommendations.explanation_summary,
        key_risks=key_risks_for(score, extracted),
        suggested_comparison_locations=suggested_comparisons,
        fallback_locations=recommendations.fallback_alternatives,
        human_explanation=explanation,
        confidence_note=confidence_note_for(extracted, payload),
    )


def recommendation_request_for(
    current_location: str,
    extracted,
) -> RecommendationRequest:
    health_constraints = set(extracted.health_constraints)
    lifestyle_constraints = set(extracted.lifestyle_constraints)

    return RecommendationRequest(
        current_location=current_location,
        target_year=extracted.target_year,
        warming_tolerance=extracted.warming_level,
        heat_sensitivity=82 if "heat sensitivity" in health_constraints else 58,
        respiratory_sensitivity=86
        if "respiratory sensitivity" in health_constraints
        else 42,
        flood_risk_tolerance=28 if extracted.risk_tolerance == "low" else 52,
        outdoor_lifestyle_preference=78
        if "outdoor lifestyle" in lifestyle_constraints
        else 52,
        urban_vs_quieter_preference="balanced",
        coastal_preference=(
            "coastal"
            if "coastal preference" in lifestyle_constraints
            else "inland"
            if extracted.risk_tolerance == "low"
            else "neutral"
        ),
        family_elderly_sensitivity=82
        if "family or elderly sensitivity" in health_constraints
        else 44,
        remote_work_flexibility=78
        if "remote work flexibility" in lifestyle_constraints
        else 46,
    )


def overlay_types_for(extracted) -> list[str]:
    overlays = ["Heat Risk"]

    if extracted.risk_tolerance == "low" or extracted.season == "Monsoon":
        overlays.append("Flood Risk")
    if "respiratory sensitivity" in extracted.health_constraints:
        overlays.append("Air Quality")
    if "outdoor lifestyle" in extracted.lifestyle_constraints:
        overlays.append("Outdoor Comfort")

    return overlays


def key_risks_for(score, extracted) -> list[str]:
    risks = [
        f"{score.heat_risk} heat risk by {extracted.target_year}",
        f"{score.flood_risk} flood exposure under {extracted.season.lower()} conditions",
        f"{score.outdoor_comfort} outdoor comfort at +{extracted.warming_level:.1f}C",
    ]

    if "respiratory sensitivity" in extracted.health_constraints:
        risks.append(f"{score.air_quality_proxy} air-quality proxy matters for asthma risk")
    if extracted.relocation_intent:
        risks.append("Relocation comparison requested; cooler or more resilient regions are ranked.")

    return risks


def build_interpreted_query(query_text: str, extracted) -> str:
    return (
        f"Assess {extracted.primary_location} for {extracted.target_year}, "
        f"+{extracted.warming_level:.1f}C, {extracted.season.lower()} conditions"
        f"{' with relocation comparison' if extracted.relocation_intent else ''}."
    )


def confidence_note_for(extracted, payload: AdvisorQueryRequest) -> str:
    missing = []

    if not extracted.primary_location:
        missing.append("primary location")
    if not payload.query_text.strip():
        missing.append("query text")

    if missing:
        return (
            "Confidence is medium-low because the advisor had to infer "
            f"{', '.join(missing)} from defaults."
        )

    return (
        "Confidence is medium: v1 uses deterministic parsing, real geocoding where "
        "available, and simulated climate/recommendation scoring."
    )
