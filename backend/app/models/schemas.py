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
