from pydantic import BaseModel, Field
from datetime import datetime


class LocationResult(BaseModel):
    location_name: str
    region: str
    climate_zone: str
    latitude: float
    longitude: float
    locality: str | None = None
    district: str | None = None
    city: str | None = None
    country: str | None = None
    hierarchy_label: str | None = None
    place_type: str | None = None
    geocoder_provider: str | None = None
    geocoder_metadata: dict[str, object] | None = None
    bbox: list[float] | None = None
    known: bool
    extrapolated: bool
    location_id: str


class ScenarioScoreRequest(BaseModel):
    location: str
    year: int = Field(ge=2025, le=2100)
    warmingLevel: float = Field(ge=1.0, le=4.0)
    season: str
    timeOfDay: str
    overlayTypes: list[str] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    heat_score: int
    flood_score: int
    outdoor_comfort_score: int
    air_quality_score: int
    green_cover_stress_score: int
    water_stress_score: int
    livability_stress_score: int
    warming_pressure: float
    year_pressure: float
    season_modifier: str
    time_of_day_modifier: str


class ClimateRasterSample(BaseModel):
    sampled_value: float
    grid_cell_id: str
    raster_source: str
    dataset_name: str
    dataset_resolution: str
    layer_type: str


class ClimateSurfaceCell(BaseModel):
    grid_cell_id: str
    bounds: list[float]
    polygon: list[list[float]]
    sampled_value: float
    climate_intensity: float
    normalized_score: int
    raster_source: str
    confidence_level: str


class ClimateCellDetailResponse(BaseModel):
    grid_cell_id: str
    layer_type: str
    year: int
    warming_level: float
    season: str
    raw_sampled_value: float
    normalized_score: int
    score_explanation: str
    dominant_risk_factor: str
    confidence_level: str
    fallback_source_used: str


class ClimateSurfaceResponse(BaseModel):
    layer_type: str
    bbox: list[float]
    zoom: float
    grid_resolution: str
    sampled_cell_count: int
    climate_surface_source: str
    cells: list[ClimateSurfaceCell]
    geojson: dict[str, object]


class ClimateTimelineSnapshot(BaseModel):
    year: int
    warming_level: float
    livability_score: int
    heat_score: int
    flood_score: int
    outdoor_comfort_score: int
    heat_risk: str
    flood_risk: str
    outdoor_comfort: str
    dominant_risk_driver: str
    raster_grid_cell_id: str | None = None
    raster_sampled_value: float | None = None
    raster_source: str | None = None


class ClimateTimelineResponse(BaseModel):
    location: LocationResult
    warming_pathway: str
    layer_type: str
    season: str
    start_year: int
    end_year: int
    temporal_resolution: str
    value_mode: str
    climate_evolution_summary: str
    score_progression: list[dict[str, object]]
    dominant_risk_progression: list[dict[str, object]]
    raster_summary_progression: list[dict[str, object]]
    snapshots: list[ClimateTimelineSnapshot]


class ClimateInteractionRequest(BaseModel):
    scenario: ScenarioScoreRequest
    active_layers: list[str] = Field(default_factory=list)
    location: str | None = None
    selected_climate_cell: ClimateCellDetailResponse | None = None


class ClimateInteractionResponse(BaseModel):
    composite_risk_score: int
    dominant_interaction_chain: str
    resilience_score: int
    infrastructure_pressure: int
    human_exposure_score: int
    cascading_risks: list[str]
    mitigation_factors: list[str]
    visual_indicators: list[str]
    active_interaction_model: str
    interaction_weights: dict[str, float]
    resilience_modifiers: dict[str, float]
    cascading_chain_depth: int


class RecommendationRequest(BaseModel):
    current_location: str
    target_year: int = Field(ge=2025, le=2100)
    warming_tolerance: float = Field(ge=1.0, le=4.0)
    heat_sensitivity: int = Field(ge=0, le=100)
    respiratory_sensitivity: int = Field(ge=0, le=100)
    flood_risk_tolerance: int = Field(ge=0, le=100)
    outdoor_lifestyle_preference: int = Field(ge=0, le=100)
    urban_vs_quieter_preference: str
    coastal_preference: str
    family_elderly_sensitivity: int = Field(ge=0, le=100)
    remote_work_flexibility: int = Field(ge=0, le=100)


class RecommendedRegion(BaseModel):
    region_name: str
    location_name: str
    latitude: float
    longitude: float
    suitability_score: int
    resilience_score: int
    dominant_future_risks: list[str]
    expected_livability_trajectory: str
    major_tradeoffs: list[str]
    explanation: str


class RegionComparisonProjection(BaseModel):
    location_name: str
    region: str
    livability_score: int
    heat_risk: str
    flood_risk: str
    outdoor_comfort: str
    resilience_score: int
    dominant_risk_driver: str


class RecommendationResponse(BaseModel):
    current_location: RegionComparisonProjection
    recommended_regions: list[RecommendedRegion]
    fallback_alternatives: list[RecommendedRegion]
    comparison_projection: list[RegionComparisonProjection]
    explanation_summary: str
    timeline_narratives: list[str]
    recommendation_model: str


class AdvisorQueryRequest(BaseModel):
    query_text: str
    selected_preferences: list[str] = Field(default_factory=list)
    current_scenario_state: dict[str, object] | None = None


class AdvisorExtractedInputs(BaseModel):
    primary_location: str
    comparison_locations: list[str]
    target_year: int
    warming_level: float
    season: str
    health_constraints: list[str]
    lifestyle_constraints: list[str]
    relocation_intent: bool
    risk_tolerance: str


class AdvisorResponse(BaseModel):
    interpreted_query: str
    extracted_inputs: AdvisorExtractedInputs
    primary_location_score: "ScenarioScoreResponse"
    recommendation_summary: str
    key_risks: list[str]
    suggested_comparison_locations: list[RecommendedRegion]
    fallback_locations: list[RecommendedRegion]
    human_explanation: "ExplanationResponse"
    confidence_note: str


class ExplanationRequest(BaseModel):
    location: str
    region: str
    climate_region_type: str
    year: int = Field(ge=2025, le=2100)
    warming_level: float = Field(ge=1.0, le=4.0)
    season: str
    time_of_day: str
    livability_score: int
    heat_risk: str
    flood_risk: str
    outdoor_comfort: str
    dominant_risk_driver: str
    selected_grid_cell: ClimateCellDetailResponse | None = None
    interaction_summary: ClimateInteractionResponse | None = None


class ExplanationResponse(BaseModel):
    human_summary: str
    commute_impact: str
    outdoor_activity_impact: str
    nighttime_recovery: str
    vulnerable_groups_note: str
    confidence_note: str
    explanation_source: str


class ScenarioScoreResponse(BaseModel):
    location: LocationResult
    livability_score: int
    heat_risk: str
    flood_risk: str
    outdoor_comfort: str
    air_quality_proxy: str
    green_cover: str
    green_cover_stress: str
    water_stress: str
    livability_stress: str
    wet_bulb_anomaly: float
    climate_region_type: str
    score_breakdown: ScoreBreakdown
    dominant_risk_driver: str
    raster_sample: ClimateRasterSample | None = None
    summary: str


class ScenarioInput(BaseModel):
    location: str
    year: int = Field(ge=2025, le=2100)
    warmingLevel: float = Field(ge=1.0, le=4.0)
    season: str
    timeOfDay: str
    overlayTypes: list[str] = Field(default_factory=list)


class ScenarioCompareRequest(BaseModel):
    scenarioA: ScenarioInput
    scenarioB: ScenarioInput


class ScenarioCompareResponse(BaseModel):
    heat_increase: int
    flood_increase: int
    comfort_decline: int
    livability_decline: int
    explanation: str


class RegionBoundaryResponse(BaseModel):
    location: LocationResult
    boundary_source: str
    boundary_name: str | None = None
    boundary_match_reason: str | None = None
    climate_region_type: str | None = None
    db_boundary_id: int | None = None
    polygon: list[list[float]]
    geojson: dict[str, object] | None = None


class AdminBoundarySummary(BaseModel):
    id: int
    name: str
    aliases: list[str]
    country: str | None
    region_type: str
    climate_region_type: str
    source: str
    created_at: datetime


class AdminBoundaryDetail(AdminBoundarySummary):
    geometry_geojson: dict[str, object]


class SavedScenarioCreate(BaseModel):
    name: str
    location_name: str
    region: str
    latitude: float
    longitude: float
    year: int = Field(ge=2025, le=2100)
    warming_level: float = Field(ge=1.0, le=4.0)
    season: str
    time_of_day: str
    active_layer: str
    livability_score: int
    heat_risk: str
    flood_risk: str
    outdoor_comfort: str


class SavedScenarioResponse(SavedScenarioCreate):
    id: int
    created_at: datetime
