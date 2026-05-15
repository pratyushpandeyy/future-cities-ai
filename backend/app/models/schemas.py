from pydantic import BaseModel, Field


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


class ScenarioScoreResponse(BaseModel):
    location: LocationResult
    livability_score: int
    heat_risk: str
    flood_risk: str
    outdoor_comfort: str
    green_cover: str
    wet_bulb_anomaly: float
    summary: str


class ScenarioInput(BaseModel):
    location: str
    year: int = Field(ge=2025, le=2100)
    warmingLevel: float = Field(ge=1.0, le=4.0)
    season: str
    timeOfDay: str


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
    polygon: list[list[float]]
    geojson: dict[str, object] | None = None
