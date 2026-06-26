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
    climateScenario: str = "ssp245"
    climateModel: str | None = None


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
    unit: str | None = None
    variable: str | None = None
    model: str | None = None
    scenario: str | None = None
    period: str | None = None
    month: int | None = None
    source_path: str | None = None
    is_fallback: bool = False
    provider: str | None = None
    cache_hit: bool = False


class ClimateDataEvidence(BaseModel):
    data_mode: str
    source_label: str
    confidence: str
    sampled_variable: str | None = None
    sampled_value: float | None = None
    sampled_unit: str | None = None
    model: str | None = None
    scenario: str | None = None
    period: str | None = None
    month: int | None = None
    grid_cell_id: str | None = None
    dataset_resolution: str | None = None
    cache_hit: bool = False
    warning: str | None = None


class ClimateProviderStatus(BaseModel):
    name: str
    kind: str
    enabled: bool
    description: str


class ClimateDataBrokerStatus(BaseModel):
    provider_order: list[str]
    cache_directory: str
    cache_entry_count: int
    providers: list[ClimateProviderStatus]


class EnvironmentalSample(BaseModel):
    variable: str
    value: float
    unit: str
    provider: str
    source_url: str
    resolution: str
    grid_cell_id: str
    confidence: str
    category: str | None = None


class EnvironmentalContext(BaseModel):
    latitude: float
    longitude: float
    elevation: EnvironmentalSample | None = None
    land_cover: EnvironmentalSample | None = None
    green_cover_proxy: float | None = None
    built_up_proxy: float | None = None
    providers_used: list[str] = Field(default_factory=list)


class OvertureUrbanContext(BaseModel):
    latitude: float
    longitude: float
    bbox: list[float]
    building_count: int
    place_count: int
    building_density_per_km2: float
    place_density_per_km2: float
    provider: str
    available: bool
    note: str


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
    data_evidence: ClimateDataEvidence
    scoring_source: str = "deterministic_formula"
    model_version: str | None = None
    model_confidence: str | None = None
    feature_schema_version: str | None = None
    model_inputs_used: list[str] = Field(default_factory=list)
    summary: str


class ScenarioInput(BaseModel):
    location: str
    year: int = Field(ge=2025, le=2100)
    warmingLevel: float = Field(ge=1.0, le=4.0)
    season: str
    timeOfDay: str
    overlayTypes: list[str] = Field(default_factory=list)
    climateScenario: str = "ssp245"
    climateModel: str | None = None


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


class SpatialResolveRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class SpatialResolutionResponse(BaseModel):
    input_query: str
    place_id: int | None = None
    place_persisted: bool
    resolved_location: LocationResult
    resolution_level: str
    boundary_id: int | None = None
    boundary_name: str | None = None
    boundary_source: str
    boundary_match_reason: str | None = None
    climate_region_type: str | None = None
    climate_grid_cell_id: str | None = None
    climate_sampled_value: float | None = None
    climate_sample_source: str | None = None
    dataset_name: str | None = None
    dataset_resolution: str | None = None
    confidence: str
    fallback_used: bool
    resolution_notes: list[str] = Field(default_factory=list)


class ClimateDatasetRecord(BaseModel):
    id: int | None = None
    dataset_key: str
    name: str
    category: str
    provider: str
    source_url: str | None = None
    storage_uri: str | None = None
    data_format: str
    spatial_resolution: str | None = None
    temporal_resolution: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    variables: list[str] = Field(default_factory=list)
    scenarios: list[str] = Field(default_factory=list)
    geographic_coverage: str
    status: str
    license_name: str | None = None
    attribution: str | None = None


class FeatureBuildRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    year: int = Field(ge=2025, le=2100)
    warming_level: float = Field(ge=1.0, le=4.0)
    season: str = "Summer"
    time_of_day: str = "Afternoon"
    climate_scenario: str = "ssp245"
    climate_model: str | None = None


class EngineeredFeature(BaseModel):
    value: float
    unit: str
    source: str
    dataset_key: str | None = None
    is_fallback: bool
    confidence: str


class ClimateFeatureVector(BaseModel):
    input_query: str
    place_id: int | None = None
    resolved_name: str
    latitude: float
    longitude: float
    resolution_level: str
    year: int
    warming_level: float
    season: str
    time_of_day: str
    climate_region_type: str
    features: dict[str, EngineeredFeature]
    available_dataset_keys: list[str]
    fallback_feature_names: list[str]
    data_completeness: float
    confidence: str
    feature_schema_version: str


class ClimateModelPrediction(BaseModel):
    heat_adjustment: float
    flood_adjustment: float
    comfort_adjustment: float
    water_stress_adjustment: float
    livability_adjustment: float
    model_version: str
    model_type: str
    confidence: str
    inputs_used: list[str] = Field(default_factory=list)
    fallback_used: bool


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
