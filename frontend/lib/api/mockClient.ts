import type { AreaRiskData } from "@/components/AreaRiskInspector";
import type { MapCityNodeData } from "@/components/MapCityNode";
import type { RegionalMappingData } from "@/components/regionalTypes";
import type {
  RegionBoundaryFeatureCollection,
  Season,
} from "@/lib/climateOverlaySimulation";
import type { LocalUrbanCellData } from "@/lib/localCellSimulation";
import { knownCityNodes } from "@/lib/api/mockData";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export interface ScenarioScorePayload {
  city: MapCityNodeData;
  year: number;
  warming: number;
  season: Season;
  timeOfDay?: string;
  overlayTypes?: string[];
  localUrbanCell?: LocalUrbanCellData | null;
}

export interface ScoreBreakdown {
  heatScore: number;
  floodScore: number;
  outdoorComfortScore: number;
  airQualityScore: number;
  greenCoverStressScore: number;
  waterStressScore: number;
  livabilityStressScore: number;
  warmingPressure: number;
  yearPressure: number;
  seasonModifier: string;
  timeOfDayModifier: string;
}

export interface ScenarioScoreResult {
  city: MapCityNodeData;
  outdoorComfort: string;
  wetBulbAnomaly: number;
  climateRegionType: string;
  scoreBreakdown: ScoreBreakdown;
  dominantRiskDriver: string;
  summary: string;
}

export interface ScenarioComparisonConfig {
  year: number;
  warming: number;
  season: Season;
  overlays?: Partial<Record<string, boolean>>;
}

export interface CompareScenariosPayload {
  city: MapCityNodeData;
  scenarioA: ScenarioComparisonConfig;
  scenarioB: ScenarioComparisonConfig;
  localUrbanCell?: LocalUrbanCellData | null;
}

export interface ComparisonMetrics {
  heatIncrease: number;
  livabilityDecline: number;
  outdoorComfortChange: number;
  scientificMetric: string;
  humanTranslation: string;
}

export interface SearchLocationPayload {
  query: string;
  fallbackCenter: [number, number];
}

export interface SearchLocationResult {
  kind: "known" | "regional";
  city: MapCityNodeData;
  regionalMapping: RegionalMappingData;
}

export interface HumanImpactExplanationPayload {
  city: MapCityNodeData;
  scenarioA?: ScenarioComparisonConfig;
  scenarioB?: ScenarioComparisonConfig;
}

interface ApiLocationResult {
  location_name: string;
  region: string;
  climate_zone: string;
  latitude: number;
  longitude: number;
  locality?: string | null;
  district?: string | null;
  city?: string | null;
  country?: string | null;
  hierarchy_label?: string | null;
  place_type?: string | null;
  geocoder_provider?: string | null;
  geocoder_metadata?: Record<string, unknown> | null;
  bbox?: number[] | null;
  known: boolean;
  extrapolated: boolean;
  location_id: string;
}

interface ApiScenarioScoreResult {
  location: ApiLocationResult;
  livability_score: number;
  heat_risk: string;
  flood_risk: string;
  outdoor_comfort: string;
  air_quality_proxy: string;
  green_cover: string;
  green_cover_stress: string;
  water_stress: string;
  livability_stress: string;
  wet_bulb_anomaly: number;
  climate_region_type: string;
  score_breakdown: {
    heat_score: number;
    flood_score: number;
    outdoor_comfort_score: number;
    air_quality_score: number;
    green_cover_stress_score: number;
    water_stress_score: number;
    livability_stress_score: number;
    warming_pressure: number;
    year_pressure: number;
    season_modifier: string;
    time_of_day_modifier: string;
  };
  dominant_risk_driver: string;
  summary: string;
}

interface ApiComparisonResult {
  heat_increase: number;
  flood_increase: number;
  comfort_decline: number;
  livability_decline: number;
  explanation: string;
}

interface ApiRegionBoundaryResult {
  location: ApiLocationResult;
  boundary_source: "real_geojson" | "simulated_fallback" | "simulated";
  polygon: [number, number][];
  geojson?: RegionBoundaryFeatureCollection | null;
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}

function apiLocationToRegionalMapping(
  location: ApiLocationResult,
): RegionalMappingData {
  return {
    inputLocation: location.location_name,
    mappedRegion: location.region,
    climateZone: location.climate_zone,
    confidence: location.known ? "High" : "Medium",
    nearestGridCell: location.location_id.toUpperCase(),
    boundarySource: "simulated_fallback",
    longitude: location.longitude,
    latitude: location.latitude,
    locality: location.locality,
    district: location.district,
    city: location.city,
    country: location.country,
    hierarchyLabel: location.hierarchy_label,
    placeType: location.place_type,
  };
}

function apiLocationToCity(location: ApiLocationResult): MapCityNodeData {
  const knownCity = knownCityNodes.find(
    (city) => city.name.toLowerCase() === location.location_name.toLowerCase(),
  );

  if (knownCity) {
    return {
      ...knownCity,
      region: location.region,
      longitude: location.longitude,
      latitude: location.latitude,
    };
  }

  return {
    name: location.location_name,
    region: location.region,
    longitude: location.longitude,
    latitude: location.latitude,
    x: 50,
    y: 50,
    livabilityScore: 72,
    heatRisk: "Moderate",
    floodRisk: "Moderate",
    greenCover: "22%",
    futureSummary:
      "Regional extrapolation estimates future comfort and climate pressure from nearby simulated climate cells.",
    sportsCultureImpact:
      "Local outdoor routines, neighborhood sport, and high-street culture become more sensitive to heat timing and cooling access.",
    accent: "bg-fuchsia-400/20",
  };
}

function apiScenarioToScore(
  baseCity: MapCityNodeData,
  payload: ApiScenarioScoreResult,
): ScenarioScoreResult {
  return {
    city: {
      ...baseCity,
      name: payload.location.location_name,
      region: payload.location.region,
      longitude: payload.location.longitude,
      latitude: payload.location.latitude,
      livabilityScore: payload.livability_score,
      heatRisk: payload.heat_risk,
      floodRisk: payload.flood_risk,
      greenCover: payload.green_cover,
      futureSummary: payload.summary,
    },
    outdoorComfort: payload.outdoor_comfort,
    wetBulbAnomaly: payload.wet_bulb_anomaly,
    climateRegionType: payload.climate_region_type,
    scoreBreakdown: {
      heatScore: payload.score_breakdown.heat_score,
      floodScore: payload.score_breakdown.flood_score,
      outdoorComfortScore: payload.score_breakdown.outdoor_comfort_score,
      airQualityScore: payload.score_breakdown.air_quality_score,
      greenCoverStressScore: payload.score_breakdown.green_cover_stress_score,
      waterStressScore: payload.score_breakdown.water_stress_score,
      livabilityStressScore: payload.score_breakdown.livability_stress_score,
      warmingPressure: payload.score_breakdown.warming_pressure,
      yearPressure: payload.score_breakdown.year_pressure,
      seasonModifier: payload.score_breakdown.season_modifier,
      timeOfDayModifier: payload.score_breakdown.time_of_day_modifier,
    },
    dominantRiskDriver: payload.dominant_risk_driver,
    summary: payload.summary,
  };
}

export async function searchLocation({
  query,
}: SearchLocationPayload): Promise<SearchLocationResult> {
  const params = new URLSearchParams({ query: query.trim() || "Unknown" });
  const location = await requestJson<ApiLocationResult>(
    `/api/search?${params.toString()}`,
  );

  return {
    kind: location.known ? "known" : "regional",
    city: apiLocationToCity(location),
    regionalMapping: apiLocationToRegionalMapping(location),
  };
}

export async function getScenarioScore({
  city,
  year,
  warming,
  season,
  timeOfDay = "Afternoon",
  overlayTypes = [],
}: ScenarioScorePayload): Promise<ScenarioScoreResult> {
  const payload = await requestJson<ApiScenarioScoreResult>(
    "/api/scenario/score",
    {
      method: "POST",
      body: JSON.stringify({
        location: city.name,
        year,
        warmingLevel: warming,
        season,
        timeOfDay,
        overlayTypes,
      }),
    },
  );

  return apiScenarioToScore(city, payload);
}

export async function getOutdoorComfort(
  payload: ScenarioScorePayload,
): Promise<string> {
  const score = await getScenarioScore(payload);

  return score.outdoorComfort;
}

export async function getHumanImpactExplanation({
  city,
  scenarioA,
  scenarioB,
}: HumanImpactExplanationPayload): Promise<string> {
  if (scenarioA && scenarioB) {
    const comparison = await compareScenarios({ city, scenarioA, scenarioB });

    return comparison.humanTranslation;
  }

  const score = await getScenarioScore({
    city,
    year: 2030,
    warming: 1.7,
    season: "Summer",
  });

  return score.summary;
}

export async function compareScenarios({
  city,
  scenarioA,
  scenarioB,
}: CompareScenariosPayload): Promise<ComparisonMetrics> {
  const result = await requestJson<ApiComparisonResult>(
    "/api/scenario/compare",
    {
      method: "POST",
      body: JSON.stringify({
        scenarioA: {
          location: city.name,
          year: scenarioA.year,
          warmingLevel: scenarioA.warming,
          season: scenarioA.season,
          timeOfDay: "Afternoon",
          overlayTypes: scenarioA.overlays
            ? Object.keys(scenarioA.overlays).filter(
                (overlay) => scenarioA.overlays?.[overlay],
              )
            : [],
        },
        scenarioB: {
          location: city.name,
          year: scenarioB.year,
          warmingLevel: scenarioB.warming,
          season: scenarioB.season,
          timeOfDay: "Afternoon",
          overlayTypes: scenarioB.overlays
            ? Object.keys(scenarioB.overlays).filter(
                (overlay) => scenarioB.overlays?.[overlay],
              )
            : [],
        },
      }),
    },
  );

  return {
    heatIncrease: result.heat_increase,
    livabilityDecline: result.livability_decline,
    outdoorComfortChange: result.comfort_decline,
    scientificMetric: `Wet bulb anomaly +${Math.max(
      0,
      scenarioB.warming - scenarioA.warming + 0.6,
    ).toFixed(1)}C`,
    humanTranslation: result.explanation,
  };
}

export async function getRegionBoundary(
  location: RegionalMappingData,
): Promise<RegionBoundaryFeatureCollection> {
  const params = new URLSearchParams({ location: location.inputLocation });
  const result = await requestJson<ApiRegionBoundaryResult>(
    `/api/region-boundary?${params.toString()}`,
  );
  if (result.geojson) {
    return {
      ...result.geojson,
      features: result.geojson.features.map((feature) => ({
        ...feature,
        properties: {
          id: result.location.location_id,
          label: result.location.region,
          ...feature.properties,
          boundarySource: result.boundary_source,
        },
      })),
    };
  }

  const coordinates = result.polygon;
  const closedCoordinates =
    coordinates.length > 0 &&
    (coordinates[0][0] !== coordinates[coordinates.length - 1][0] ||
      coordinates[0][1] !== coordinates[coordinates.length - 1][1])
      ? [...coordinates, coordinates[0]]
      : coordinates;

  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: {
          id: result.location.location_id,
          label: result.location.region,
          boundarySource: result.boundary_source,
        },
        geometry: {
          type: "Polygon",
          coordinates: [closedCoordinates],
        },
      },
    ],
  };
}

export function getLocalAreaRisk(x: number, y: number): AreaRiskData {
  const roundedX = Math.round(x * 10) / 10;
  const roundedY = Math.round(y * 10) / 10;
  const localHeatIndex = Math.round(48 + roundedY * 0.34 + roundedX * 0.12);
  const floodScore = Math.round(
    24 + roundedY * 0.42 + Math.abs(50 - roundedX) * 0.18,
  );
  const greenCoverScore = Math.max(
    8,
    Math.round(42 - roundedY * 0.22 + (100 - roundedX) * 0.08),
  );
  const walkabilityScore = Math.max(
    18,
    Math.round(78 - Math.abs(roundedX - 52) * 0.28 - roundedY * 0.18),
  );
  const overallRiskScore = Math.round(
    localHeatIndex * 0.45 + floodScore * 0.35 + (100 - walkabilityScore) * 0.2,
  );

  return {
    x: roundedX,
    y: roundedY,
    localHeatIndex,
    floodExposure: getRiskLabel(floodScore),
    greenCoverProxy: `${greenCoverScore}%`,
    walkabilityComfort: getComfortLabel(walkabilityScore),
    overallLocalRisk: getRiskLabel(overallRiskScore),
    explanation:
      "This area shows elevated future heat exposure due to dense built form and limited cooling cover.",
  };
}

function getRiskLabel(value: number) {
  if (value >= 76) {
    return "High";
  }

  if (value >= 52) {
    return "Elevated";
  }

  if (value >= 30) {
    return "Moderate";
  }

  return "Low";
}

function getComfortLabel(value: number) {
  if (value >= 72) {
    return "High";
  }

  if (value >= 52) {
    return "Moderate";
  }

  return "Low";
}
