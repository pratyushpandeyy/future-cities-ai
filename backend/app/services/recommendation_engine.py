from app.models.schemas import (
    CandidateScreenRequest,
    CandidateScreenResponse,
    ClimateInteractionRequest,
    RecommendationRequest,
    RecommendationResponse,
    RecommendedRegion,
    RegionComparisonProjection,
    ScenarioScoreRequest,
)
from app.services.climate_interaction_engine import compute_composite_risk
from app.services.simulation import resolve_location
from app.services.simulation import score_scenario


RECOMMENDATION_MODEL_VERSION = "future_habitability_recommendations_v1"

CandidateRegion = dict[str, str | float | list[str]]

CANDIDATE_REGIONS: list[CandidateRegion] = [
    {
        "location": "Manchester",
        "region": "Greater Manchester / North West England",
        "profile": "temperate_oceanic",
        "tags": ["temperate", "urban", "non_coastal", "culture"],
    },
    {
        "location": "Bangalore",
        "region": "Karnataka highland urban region",
        "profile": "highland",
        "tags": ["highland", "urban", "non_coastal", "tech"],
    },
    {
        "location": "Pune",
        "region": "Maharashtra inland plateau region",
        "profile": "highland",
        "tags": ["highland", "urban", "non_coastal", "tech"],
    },
    {
        "location": "Chennai",
        "region": "Tamil Nadu coastal urban corridor",
        "profile": "tropical_humid_coastal",
        "tags": ["coastal", "humid", "urban", "heat"],
    },
    {
        "location": "Hyderabad",
        "region": "Telangana inland plateau region",
        "profile": "semi_arid_highland",
        "tags": ["highland", "urban", "non_coastal", "tech", "dry"],
    },
    {
        "location": "Delhi",
        "region": "National Capital Region",
        "profile": "continental_dense",
        "tags": ["dense", "urban", "non_coastal", "air_quality"],
    },
    {
        "location": "Kolkata",
        "region": "Lower Ganges delta urban region",
        "profile": "tropical_humid_delta",
        "tags": ["coastal", "humid", "flood", "dense"],
    },
    {
        "location": "Ahmedabad",
        "region": "Gujarat semi-arid urban region",
        "profile": "arid_urban",
        "tags": ["dry", "urban", "heat", "non_coastal"],
    },
    {
        "location": "Jaipur",
        "region": "Rajasthan arid urban region",
        "profile": "arid",
        "tags": ["dry", "heat", "non_coastal", "urban"],
    },
    {
        "location": "Madrid",
        "region": "Community of Madrid",
        "profile": "mediterranean",
        "tags": ["mediterranean", "urban", "dry", "culture"],
    },
    {
        "location": "Istanbul",
        "region": "Marmara region",
        "profile": "mediterranean_coastal",
        "tags": ["coastal", "urban", "culture"],
    },
    {
        "location": "Mumbai",
        "region": "Maharashtra coastal region",
        "profile": "tropical_humid_coastal",
        "tags": ["coastal", "dense", "humid", "megacity"],
    },
    {
        "location": "London",
        "region": "Greater London temperate urban region",
        "profile": "temperate_oceanic_dense",
        "tags": ["temperate", "urban", "dense", "culture"],
    },
    {
        "location": "Toronto",
        "region": "Great Lakes temperate urban region",
        "profile": "continental_temperate",
        "tags": ["temperate", "urban", "non_coastal", "water"],
    },
]


def generate_recommendations(
    payload: RecommendationRequest,
) -> RecommendationResponse:
    current_projection = evaluate_projection(
        location_name=payload.current_location,
        payload=payload,
    )
    recommendations = [
        evaluate_candidate(candidate, payload)
        for candidate in CANDIDATE_REGIONS
        if str(candidate["location"]).lower() != payload.current_location.lower()
    ]
    ranked = sorted(
        recommendations,
        key=lambda candidate: candidate.suitability_score,
        reverse=True,
    )
    fallback_alternatives = ranked[2:5]
    top_regions = ranked[:3]
    comparison_projection = [
        current_projection,
        *[
            projection_for_region(region, payload)
            for region in top_regions[:2]
        ],
    ]

    return RecommendationResponse(
        current_location=current_projection,
        recommended_regions=top_regions,
        fallback_alternatives=fallback_alternatives,
        comparison_projection=comparison_projection,
        explanation_summary=build_recommendation_summary(
            payload=payload,
            current_projection=current_projection,
            recommended_regions=top_regions,
        ),
        timeline_narratives=build_timeline_narratives(payload, current_projection),
        recommendation_model=RECOMMENDATION_MODEL_VERSION,
    )


def screen_candidate_locations(
    payload: CandidateScreenRequest,
) -> CandidateScreenResponse:
    current_projection = evaluate_projection(
        location_name=payload.current_location,
        payload=payload,
    )
    candidate_names = payload.candidate_locations or [
        str(candidate["location"]) for candidate in CANDIDATE_REGIONS
    ]
    ranked_candidates = sorted(
        [
            evaluate_candidate_location(location_name, payload)
            for location_name in unique_locations(candidate_names, payload.current_location)
        ],
        key=lambda candidate: candidate.suitability_score,
        reverse=True,
    )

    return CandidateScreenResponse(
        current_location=current_projection,
        ranked_candidates=ranked_candidates,
        recommendation_model=RECOMMENDATION_MODEL_VERSION,
        screening_note=(
            "Candidate screen uses the same geocoding, raster sampling, feature "
            "engineering, ML adjustment, and interaction scoring path as the advisor."
        ),
    )


def unique_locations(locations: list[str], current_location: str) -> list[str]:
    seen = {current_location.strip().lower()}
    unique = []

    for location in locations:
        normalized = location.strip().lower()

        if not normalized or normalized in seen:
            continue

        seen.add(normalized)
        unique.append(location)

    return unique


def evaluate_candidate(
    candidate: CandidateRegion,
    payload: RecommendationRequest,
) -> RecommendedRegion:
    projection = evaluate_projection(
        location_name=str(candidate["location"]),
        payload=payload,
    )
    tags = [str(tag) for tag in candidate["tags"]]
    risk_penalty = user_risk_penalty(payload, projection)
    preference_bonus = preference_bonus_for(tags, payload)
    remote_work_bonus = round(payload.remote_work_flexibility * 0.08)
    livability_component = projection.livability_score * 0.36
    resilience_component = projection.resilience_score * 0.32
    base_component = 34
    suitability = clamp_score(
        base_component
        + livability_component
        + resilience_component
        + preference_bonus
        + remote_work_bonus
        - risk_penalty,
    )
    ranking_breakdown = {
        "base_component": round(base_component, 2),
        "livability_component": round(livability_component, 2),
        "resilience_component": round(resilience_component, 2),
        "preference_bonus": round(preference_bonus, 2),
        "remote_work_bonus": round(remote_work_bonus, 2),
        "risk_penalty": round(risk_penalty, 2),
    }

    return RecommendedRegion(
        region_name=str(candidate["region"]),
        location_name=str(candidate["location"]),
        latitude=resolve_location(str(candidate["location"])).latitude,
        longitude=resolve_location(str(candidate["location"])).longitude,
        suitability_score=suitability,
        resilience_score=projection.resilience_score,
        dominant_future_risks=dominant_future_risks(projection),
        expected_livability_trajectory=livability_trajectory(
            payload.target_year,
            projection.livability_score,
        ),
        major_tradeoffs=tradeoffs_for(tags, payload, projection),
        ranking_breakdown=ranking_breakdown,
        explanation=(
            f"{candidate['region']} scores {suitability}/100 because it balances "
            f"{projection.livability_score}/100 livability, "
            f"{projection.resilience_score}/100 resilience, "
            f"{projection.heat_risk.lower()} heat risk and "
            f"{projection.flood_risk.lower()} flood risk. User constraints apply "
            f"a {round(risk_penalty, 1)} point risk penalty and a "
            f"{round(preference_bonus + remote_work_bonus, 1)} point preference bonus."
        ),
    )


def evaluate_candidate_location(
    location_name: str,
    payload: RecommendationRequest,
) -> RecommendedRegion:
    known_candidate = next(
        (
            candidate
            for candidate in CANDIDATE_REGIONS
            if str(candidate["location"]).lower() == location_name.lower()
        ),
        None,
    )

    if known_candidate:
        return evaluate_candidate(known_candidate, payload)

    location = resolve_location(location_name)
    tags = infer_candidate_tags(location)
    candidate: CandidateRegion = {
        "location": location.location_name,
        "region": location.region,
        "profile": location.climate_zone,
        "tags": tags,
    }

    return evaluate_candidate(candidate, payload)


def infer_candidate_tags(location) -> list[str]:
    text = " ".join(
        filter(
            None,
            [
                location.location_name,
                location.region,
                location.climate_zone,
                location.country,
                location.place_type,
            ],
        ),
    ).lower()
    tags = ["urban"]

    if any(term in text for term in ["coastal", "delta", "mumbai", "chennai", "kolkata"]):
        tags.append("coastal")
    else:
        tags.append("non_coastal")
    if any(term in text for term in ["highland", "plateau", "bangalore", "pune"]):
        tags.append("highland")
    if any(term in text for term in ["temperate", "england", "canada", "oceanic"]):
        tags.append("temperate")
    if any(term in text for term in ["arid", "dry", "jaipur", "ahmedabad", "delhi"]):
        tags.append("dry")
    if any(term in text for term in ["dense", "megacity", "delhi", "mumbai", "london"]):
        tags.append("dense")

    return tags


def evaluate_projection(
    *,
    location_name: str,
    payload: RecommendationRequest,
) -> RegionComparisonProjection:
    location = resolve_location(location_name)
    scenario = ScenarioScoreRequest(
        location=location.location_name,
        year=payload.target_year,
        warmingLevel=payload.warming_tolerance,
        season="Summer",
        timeOfDay="Afternoon",
        overlayTypes=["Heat Risk", "Flood Risk", "Water Stress"],
    )
    score = score_scenario(scenario)
    interaction = compute_composite_risk(
        ClimateInteractionRequest(
            scenario=scenario,
            active_layers=["Heat Risk", "Flood Risk", "Water Stress"],
            location=location.location_name,
        ),
    )

    return RegionComparisonProjection(
        location_name=location.location_name,
        region=location.region,
        livability_score=score.livability_score,
        heat_risk=score.heat_risk,
        flood_risk=score.flood_risk,
        outdoor_comfort=score.outdoor_comfort,
        resilience_score=interaction.resilience_score,
        dominant_risk_driver=score.dominant_risk_driver,
    )


def projection_for_region(
    region: RecommendedRegion,
    payload: RecommendationRequest,
) -> RegionComparisonProjection:
    return evaluate_projection(location_name=region.location_name, payload=payload)


def user_risk_penalty(
    payload: RecommendationRequest,
    projection: RegionComparisonProjection,
) -> float:
    heat_penalty = risk_level(projection.heat_risk) * payload.heat_sensitivity * 0.08
    respiratory_penalty = (
        risk_level(projection.heat_risk) * payload.respiratory_sensitivity * 0.02
    )
    flood_penalty = max(
        0,
        risk_level(projection.flood_risk) * 18 - payload.flood_risk_tolerance,
    ) * 0.16
    family_penalty = (
        (risk_level(projection.heat_risk) + risk_level(projection.flood_risk))
        * payload.family_elderly_sensitivity
        * 0.02
    )
    outdoor_penalty = (
        (3 - comfort_level(projection.outdoor_comfort))
        * payload.outdoor_lifestyle_preference
        * 0.055
    )

    return heat_penalty + respiratory_penalty + flood_penalty + family_penalty + outdoor_penalty


def preference_bonus_for(tags: list[str], payload: RecommendationRequest) -> float:
    bonus = 0.0

    if payload.urban_vs_quieter_preference == "urban" and "urban" in tags:
        bonus += 8
    if payload.urban_vs_quieter_preference == "quieter" and "dense" not in tags:
        bonus += 8
    if payload.coastal_preference == "coastal" and "coastal" in tags:
        bonus += 7
    if payload.coastal_preference == "inland" and "coastal" not in tags:
        bonus += 7
    if payload.outdoor_lifestyle_preference >= 65 and (
        "temperate" in tags or "highland" in tags
    ):
        bonus += 7

    return bonus


def dominant_future_risks(projection: RegionComparisonProjection) -> list[str]:
    risks = [
        f"{projection.heat_risk} heat risk",
        f"{projection.flood_risk} flood risk",
        f"{projection.outdoor_comfort} outdoor comfort",
    ]

    return risks


def livability_trajectory(target_year: int, livability_score: int) -> str:
    if target_year >= 2070 and livability_score < 58:
        return "Declining sharply after mid-century without adaptation."
    if target_year >= 2045 and livability_score < 70:
        return "Stable near term, then progressively more constrained after 2045."
    if livability_score >= 76:
        return "Relatively stable through the target year with adaptation buffers."

    return "Moderate decline, with comfort becoming more seasonal over time."


def tradeoffs_for(
    tags: list[str],
    payload: RecommendationRequest,
    projection: RegionComparisonProjection,
) -> list[str]:
    tradeoffs = []

    if "coastal" in tags:
        tradeoffs.append("Coastal access improves lifestyle fit but keeps flood exposure relevant.")
    if "urban" in tags and payload.urban_vs_quieter_preference == "quieter":
        tradeoffs.append("Urban access comes with density and heat-retention pressure.")
    if projection.heat_risk in {"High", "Elevated"}:
        tradeoffs.append("Hotter summers require schedule adaptation and cooling access.")
    if payload.remote_work_flexibility < 45:
        tradeoffs.append("Lower remote-work flexibility increases commute exposure.")

    return tradeoffs or ["Main tradeoff is uncertainty in future adaptation capacity."]


def build_recommendation_summary(
    *,
    payload: RecommendationRequest,
    current_projection: RegionComparisonProjection,
    recommended_regions: list[RecommendedRegion],
) -> str:
    if not recommended_regions:
        return "No suitable candidate regions were available for this prototype run."

    top_region = recommended_regions[0]

    return (
        f"For {payload.target_year}, {top_region.region_name} is the strongest "
        f"prototype recommendation at {top_region.suitability_score}/100. Compared "
        f"with {current_projection.location_name}, it offers "
        f"{top_region.resilience_score}/100 resilience and a more favorable balance "
        "of future heat, flood, lifestyle, and flexibility constraints."
    )


def build_timeline_narratives(
    payload: RecommendationRequest,
    current_projection: RegionComparisonProjection,
) -> list[str]:
    narratives = []

    if payload.target_year >= 2045 and current_projection.heat_risk in {"High", "Elevated"}:
        narratives.append(
            "Summers become progressively harder after 2045 under the selected warming tolerance."
        )
    if payload.target_year >= 2060 and current_projection.resilience_score < 55:
        narratives.append(
            "Livability resilience weakens after 2060 unless cooling, drainage, and water systems improve."
        )
    if payload.remote_work_flexibility >= 65:
        narratives.append(
            "Remote-work flexibility reduces commute exposure during future peak-risk periods."
        )

    return narratives or [
        "Future suitability remains sensitive to local adaptation and household exposure."
    ]


def risk_level(label: str) -> int:
    return {"Low": 1, "Moderate": 2, "Elevated": 3, "High": 4}.get(label, 2)


def comfort_level(label: str) -> int:
    return {"Low": 1, "Moderate": 2, "High": 3}.get(label, 2)


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))
