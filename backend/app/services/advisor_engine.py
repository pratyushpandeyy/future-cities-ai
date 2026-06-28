from app.models.schemas import (
    AdvisorEvidenceBundle,
    AdvisorQueryRequest,
    AdvisorResponse,
    AdvisorSystemAudit,
    ExplanationRequest,
    RAGQueryRequest,
    RecommendationRequest,
    ScenarioScoreRequest,
)
from app.services.advisor_parser import parse_advisor_query
from app.services.ai_explanation import explain_climate_impact
from app.services.rag_retrieval import retrieve_climate_knowledge
from app.services.recommendation_engine import evaluate_candidate_location
from app.services.recommendation_engine import generate_recommendations
from app.services.simulation import resolve_location
from app.services.simulation import score_scenario


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
    score = score_scenario(scenario)
    rag_response = retrieve_climate_knowledge(
        RAGQueryRequest(
            query_text=payload.query_text,
            location=score.location.location_name,
            climate_region_type=score.climate_region_type,
            season=extracted.season,
            risks=[
                score.heat_risk,
                score.flood_risk,
                score.outdoor_comfort,
                score.dominant_risk_driver,
                *extracted.health_constraints,
                *extracted.lifestyle_constraints,
            ],
            max_chunks=4,
        ),
    )
    recommendation_request = recommendation_request_for(
        extracted.primary_location,
        extracted,
    )
    recommendations = generate_recommendations(recommendation_request)
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
            retrieved_knowledge=rag_response.chunks,
            rag_grounding_summary=rag_response.grounding_summary,
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
    comparison_names = {region.location_name.lower() for region in comparison_recommendations}
    for location_name in comparison_locations:
        if location_name.lower() not in comparison_names:
            comparison_recommendations.append(
                evaluate_candidate_location(location_name, recommendation_request),
            )
    suggested_comparisons = comparison_recommendations or recommendations.recommended_regions[:3]

    return AdvisorResponse(
        interpreted_query=build_interpreted_query(payload.query_text, extracted),
        extracted_inputs=extracted,
        primary_location_score=score,
        evidence_bundle=evidence_bundle_for(score),
        system_audit=system_audit_for(
            score=score,
            rag_response=rag_response,
            recommendation_model=recommendations.recommendation_model,
        ),
        retrieved_knowledge=rag_response.chunks,
        rag_grounding_summary=rag_response.grounding_summary,
        recommendation_summary=recommendations.explanation_summary,
        key_risks=key_risks_for(score, extracted),
        suggested_comparison_locations=suggested_comparisons,
        fallback_locations=recommendations.fallback_alternatives,
        human_explanation=explanation,
        confidence_note=confidence_note_for(extracted, payload),
    )


def system_audit_for(
    *,
    score,
    rag_response,
    recommendation_model: str,
) -> AdvisorSystemAudit:
    fallback_notes = []

    if score.raster_sample is None or score.raster_sample.is_fallback:
        fallback_notes.append("Climate raster sample used fallback mode.")
    if not score.model_version:
        fallback_notes.append("ML model artifact was unavailable; formula fallback used.")
    if not rag_response.chunks:
        fallback_notes.append("No RAG chunks retrieved.")

    return AdvisorSystemAudit(
        geocoder_provider=score.location.geocoder_provider,
        climate_data_mode=score.data_evidence.data_mode,
        ml_model_version=score.model_version,
        ml_scoring_source=score.scoring_source,
        rag_retrieval_mode=rag_response.retrieval_mode,
        rag_chunk_count=len(rag_response.chunks),
        recommendation_model=recommendation_model,
        fallback_notes=fallback_notes,
    )


def evidence_bundle_for(score) -> AdvisorEvidenceBundle:
    evidence = score.data_evidence

    return AdvisorEvidenceBundle(
        model_version=score.model_version,
        scoring_source=score.scoring_source,
        model_confidence=score.model_confidence,
        model_inputs_used=score.model_inputs_used,
        climate_data_mode=evidence.data_mode,
        climate_source_label=evidence.source_label,
        climate_source_confidence=evidence.confidence,
        sampled_variable=evidence.sampled_variable,
        sampled_value=evidence.sampled_value,
        sampled_unit=evidence.sampled_unit,
        grid_cell_id=evidence.grid_cell_id,
        boundary_source=None,
        explanation_grounding=(
            f"Advisor explanation is grounded in backend scenario score "
            f"{score.livability_score}/100, {score.heat_risk.lower()} heat risk, "
            f"{score.flood_risk.lower()} flood risk, model "
            f"{score.model_version or 'formula fallback'}, and "
            f"{evidence.source_label}."
        ),
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
        "available, trained ML scoring when the model artifact is present, and "
        "template/LLM explanations grounded in backend-computed values."
    )
