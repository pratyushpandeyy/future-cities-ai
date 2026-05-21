from app.models.schemas import (
    ClimateTimelineResponse,
    ClimateTimelineSnapshot,
    ScenarioInput,
)
from app.services.climate_engine import compute_scenario_score
from app.services.simulation import resolve_location


WARMING_PATHWAYS = {
    "optimistic": {
        2025: 1.4,
        2030: 1.6,
        2050: 1.8,
        2100: 2.0,
    },
    "moderate": {
        2025: 1.4,
        2030: 1.7,
        2050: 2.7,
        2100: 3.1,
    },
    "severe": {
        2025: 1.4,
        2030: 1.9,
        2050: 3.2,
        2100: 4.0,
    },
}


def generate_climate_timeline(
    *,
    location: str,
    start_year: int,
    end_year: int,
    warming_pathway: str,
    layer_type: str,
    season: str,
) -> ClimateTimelineResponse:
    pathway_key = warming_pathway.strip().lower()

    if pathway_key not in WARMING_PATHWAYS:
        raise ValueError(
            "warming_pathway must be one of optimistic, moderate, or severe",
        )

    if start_year > end_year:
        raise ValueError("start_year must be before or equal to end_year")

    bounded_start = max(2025, start_year)
    bounded_end = min(2100, end_year)
    resolved_location = resolve_location(location)
    snapshots: list[ClimateTimelineSnapshot] = []

    for year in range(bounded_start, bounded_end + 1):
        warming_level = interpolate_warming(year, pathway_key)
        scenario = ScenarioInput(
            location=resolved_location.location_name,
            year=year,
            warmingLevel=warming_level,
            season=season,
            timeOfDay="Afternoon",
            overlayTypes=[layer_type],
        )
        score = compute_scenario_score(scenario, resolved_location)

        snapshots.append(
            ClimateTimelineSnapshot(
                year=year,
                warming_level=warming_level,
                livability_score=score.livability_score,
                heat_score=score.score_breakdown.heat_score,
                flood_score=score.score_breakdown.flood_score,
                outdoor_comfort_score=score.score_breakdown.outdoor_comfort_score,
                heat_risk=score.heat_risk,
                flood_risk=score.flood_risk,
                outdoor_comfort=score.outdoor_comfort,
                dominant_risk_driver=score.dominant_risk_driver,
                raster_grid_cell_id=(
                    score.raster_sample.grid_cell_id if score.raster_sample else None
                ),
                raster_sampled_value=(
                    score.raster_sample.sampled_value if score.raster_sample else None
                ),
                raster_source=(
                    score.raster_sample.raster_source if score.raster_sample else None
                ),
            ),
        )

    return ClimateTimelineResponse(
        location=resolved_location,
        warming_pathway=pathway_key,
        layer_type=layer_type,
        season=season,
        start_year=bounded_start,
        end_year=bounded_end,
        temporal_resolution="yearly",
        value_mode="sampled raster blended with deterministic formula",
        climate_evolution_summary=build_evolution_summary(
            snapshots=snapshots,
            pathway=pathway_key,
            location_name=resolved_location.location_name,
        ),
        score_progression=[
            {
                "year": snapshot.year,
                "livability_score": snapshot.livability_score,
                "heat_score": snapshot.heat_score,
                "flood_score": snapshot.flood_score,
                "outdoor_comfort_score": snapshot.outdoor_comfort_score,
            }
            for snapshot in snapshots
        ],
        dominant_risk_progression=[
            {
                "year": snapshot.year,
                "dominant_risk_driver": snapshot.dominant_risk_driver,
            }
            for snapshot in snapshots
        ],
        raster_summary_progression=[
            {
                "year": snapshot.year,
                "grid_cell_id": snapshot.raster_grid_cell_id,
                "sampled_value": snapshot.raster_sampled_value,
                "source": snapshot.raster_source,
            }
            for snapshot in snapshots
        ],
        snapshots=snapshots,
    )


def interpolate_warming(year: int, pathway: str) -> float:
    anchors = WARMING_PATHWAYS[pathway]
    anchor_years = sorted(anchors)

    if year <= anchor_years[0]:
        return anchors[anchor_years[0]]

    if year >= anchor_years[-1]:
        return anchors[anchor_years[-1]]

    for index, start_anchor in enumerate(anchor_years[:-1]):
        end_anchor = anchor_years[index + 1]

        if start_anchor <= year <= end_anchor:
            start_value = anchors[start_anchor]
            end_value = anchors[end_anchor]
            progress = (year - start_anchor) / (end_anchor - start_anchor)
            return round(start_value + (end_value - start_value) * progress, 2)

    return anchors[anchor_years[-1]]


def build_evolution_summary(
    *,
    snapshots: list[ClimateTimelineSnapshot],
    pathway: str,
    location_name: str,
) -> str:
    if not snapshots:
        return "No timeline snapshots were generated for this request."

    first_snapshot = snapshots[0]
    last_snapshot = snapshots[-1]
    heat_overtake_year = find_heat_overtake_year(snapshots)
    livability_change = first_snapshot.livability_score - last_snapshot.livability_score
    livability_phrase = (
        f"declines by {livability_change} points"
        if livability_change >= 0
        else f"improves by {abs(livability_change)} points"
    )

    if heat_overtake_year:
        return (
            f"Heat stress overtakes flood exposure after {heat_overtake_year} "
            f"under the {pathway} pathway for {location_name}. Livability "
            f"{livability_phrase} across the playback range."
        )

    return (
        f"{last_snapshot.dominant_risk_driver.capitalize()} remains the dominant "
        f"risk signal by {last_snapshot.year} under the {pathway} pathway for "
        f"{location_name}. Livability {livability_phrase} across the playback range."
    )


def find_heat_overtake_year(
    snapshots: list[ClimateTimelineSnapshot],
) -> int | None:
    for previous, current in zip(snapshots, snapshots[1:]):
        previous_heat_delta = previous.heat_score - previous.flood_score
        current_heat_delta = current.heat_score - current.flood_score

        if previous_heat_delta <= 0 < current_heat_delta:
            return current.year

    return None
