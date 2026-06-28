import json
import os
import urllib.error
import urllib.request

from app.models.schemas import ExplanationRequest, ExplanationResponse


def explain_climate_impact(payload: ExplanationRequest) -> ExplanationResponse:
    template_response = template_explanation(payload)

    if not os.getenv("OPENAI_API_KEY"):
        return template_response

    try:
        return llm_explanation(payload)
    except (OSError, KeyError, TypeError, ValueError, urllib.error.URLError):
        return template_response


def template_explanation(payload: ExplanationRequest) -> ExplanationResponse:
    cell_phrase = ""

    if payload.selected_grid_cell:
        cell_phrase = (
            f" The selected grid cell {payload.selected_grid_cell.grid_cell_id} "
            f"has a normalized {payload.selected_grid_cell.layer_type.replace('_', ' ')} "
            f"score of {payload.selected_grid_cell.normalized_score}/100."
        )
    interaction_phrase = ""

    if payload.interaction_summary:
        interaction_phrase = (
            f" System interaction modeling gives a composite risk score of "
            f"{payload.interaction_summary.composite_risk_score}/100. "
            f"The dominant chain is: "
            f"{payload.interaction_summary.dominant_interaction_chain}"
        )
    rag_phrase = ""

    if payload.retrieved_knowledge:
        titles = ", ".join(chunk.title for chunk in payload.retrieved_knowledge[:2])
        rag_phrase = f" Research context retrieved for this answer includes: {titles}."

    heat_phrase = risk_phrase(payload.heat_risk, "heat")
    flood_phrase = risk_phrase(payload.flood_risk, "flood")
    comfort_phrase = comfort_phrase_for(payload.outdoor_comfort)

    return ExplanationResponse(
        human_summary=(
            f"{payload.location} is evaluated within {payload.region} as a "
            f"{payload.climate_region_type.replace('_', ' ')} climate region for "
            f"{payload.year}, +{payload.warming_level:.1f}C, {payload.season.lower()} "
            f"{payload.time_of_day.lower()} conditions. Livability is "
            f"{payload.livability_score}/100, with {payload.heat_risk.lower()} heat risk, "
            f"{payload.flood_risk.lower()} flood risk, and "
            f"{payload.outdoor_comfort.lower()} outdoor comfort. "
            f"The main driver is {payload.dominant_risk_driver}.{cell_phrase}"
            f"{interaction_phrase}"
            f"{rag_phrase}"
        ),
        commute_impact=(
            f"Commutes are most sensitive to {payload.dominant_risk_driver}; "
            f"{heat_phrase} and {flood_phrase} shape waiting, walking, and transfer comfort. "
            f"{interaction_commute_phrase(payload)}"
        ),
        outdoor_activity_impact=(
            f"Outdoor activity should be planned around {payload.time_of_day.lower()} "
            f"conditions because {comfort_phrase}. "
            f"{interaction_outdoor_phrase(payload)}"
        ),
        nighttime_recovery=nighttime_recovery_for(payload),
        vulnerable_groups_note=(
            "Older adults, children, outdoor workers, and people with heat or respiratory "
            "sensitivity should get priority access to shade, cooling, and lower-exposure routes."
        ),
        confidence_note=confidence_note_for(payload),
        explanation_source="template",
    )


def llm_explanation(payload: ExplanationRequest) -> ExplanationResponse:
    request_body = {
        "model": os.getenv("OPENAI_EXPLANATION_MODEL", "gpt-4o-mini"),
        "instructions": (
            "You explain computed climate intelligence for an urban map product. "
            "Do not invent or alter scores. Only explain the exact values supplied. "
            "Return valid JSON with keys: human_summary, commute_impact, "
            "outdoor_activity_impact, nighttime_recovery, vulnerable_groups_note, "
            "confidence_note."
        ),
        "input": json.dumps(payload.model_dump(), default=str),
        "temperature": 0.2,
        "max_output_tokens": 450,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=12) as response:
        response_body = json.loads(response.read().decode("utf-8"))

    text = extract_response_text(response_body)
    parsed = json.loads(text)

    return ExplanationResponse(
        human_summary=str(parsed["human_summary"]),
        commute_impact=str(parsed["commute_impact"]),
        outdoor_activity_impact=str(parsed["outdoor_activity_impact"]),
        nighttime_recovery=str(parsed["nighttime_recovery"]),
        vulnerable_groups_note=str(parsed["vulnerable_groups_note"]),
        confidence_note=str(parsed["confidence_note"]),
        explanation_source="llm",
    )


def extract_response_text(response_body: dict[str, object]) -> str:
    output_text = response_body.get("output_text")

    if isinstance(output_text, str):
        return output_text

    for item in response_body.get("output", []):
        if not isinstance(item, dict):
            continue

        for content in item.get("content", []):
            if isinstance(content, dict) and isinstance(content.get("text"), str):
                return content["text"]

    raise ValueError("LLM response did not include text output")


def risk_phrase(label: str, risk_type: str) -> str:
    normalized = label.lower()

    if normalized == "high":
        return f"{risk_type} exposure is a major constraint"
    if normalized == "elevated":
        return f"{risk_type} exposure is meaningfully elevated"
    if normalized == "moderate":
        return f"{risk_type} exposure is present but manageable"

    return f"{risk_type} exposure is comparatively low"


def comfort_phrase_for(label: str) -> str:
    normalized = label.lower()

    if normalized == "high":
        return "outdoor comfort remains relatively supportive"
    if normalized == "moderate":
        return "outdoor comfort is usable but time-sensitive"

    return "outdoor comfort is constrained and needs cooling support"


def nighttime_recovery_for(payload: ExplanationRequest) -> str:
    if payload.time_of_day.lower() == "night" or payload.heat_risk.lower() == "high":
        return (
            "Nighttime recovery may weaken because retained urban heat can keep "
            "streets and homes warmer after sunset."
        )

    return (
        "Nighttime recovery remains possible, but shaded streets and cooler indoor "
        "refuge still matter during warmer periods."
    )


def confidence_note_for(payload: ExplanationRequest) -> str:
    interaction_note = (
        " Interaction-aware text uses deterministic urban-system coupling rules."
        if payload.interaction_summary
        else ""
    )

    if payload.selected_grid_cell:
        return (
            f"Confidence is {payload.selected_grid_cell.confidence_level.lower()} "
            f"for the selected grid cell because the explanation uses computed scores "
            f"and {payload.selected_grid_cell.fallback_source_used}."
            f"{rag_confidence_phrase(payload)}"
            f"{interaction_note}"
        )

    return (
        "Confidence is medium because the explanation uses deterministic backend "
        "scores and regional assumptions, without a selected grid-cell inspection."
        f"{rag_confidence_phrase(payload)}"
        f"{interaction_note}"
    )


def rag_confidence_phrase(payload: ExplanationRequest) -> str:
    if not payload.retrieved_knowledge:
        return ""

    if payload.rag_grounding_summary:
        return f" {payload.rag_grounding_summary}"

    return " Local RAG evidence was retrieved for qualitative grounding."


def interaction_commute_phrase(payload: ExplanationRequest) -> str:
    if not payload.interaction_summary:
        return ""

    pressure = payload.interaction_summary.infrastructure_pressure

    if pressure >= 70:
        return "Infrastructure pressure is high, so delays and access strain may compound during extremes."
    if pressure >= 45:
        return "Infrastructure pressure is elevated enough to affect reliability during peak exposure."

    return "Infrastructure pressure remains comparatively buffered in this scenario."


def interaction_outdoor_phrase(payload: ExplanationRequest) -> str:
    if not payload.interaction_summary:
        return ""

    resilience = payload.interaction_summary.resilience_score

    if resilience >= 60:
        return "Urban resilience factors are still buffering some exposure."
    if resilience >= 38:
        return "Some resilience remains, but compounding risks are reducing comfort margins."

    return "Compounding risks leave limited resilience for sustained outdoor activity."
