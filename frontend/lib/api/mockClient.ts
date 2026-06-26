import type { AreaRiskData } from "@/components/AreaRiskInspector";
import type { MapCityNodeData } from "@/components/MapCityNode";
import type { RegionalMappingData } from "@/components/regionalTypes";
import type {
  RegionClimateFeatureCollection,
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

export interface RasterSample {
  sampledValue: number;
  gridCellId: string;
  rasterSource: string;
  datasetName: string;
  datasetResolution: string;
  layerType: string;
}

export interface ClimateDataEvidence {
  dataMode: string;
  sourceLabel: string;
  confidence: string;
  sampledVariable: string | null;
  sampledValue: number | null;
  sampledUnit: string | null;
  model: string | null;
  scenario: string | null;
  period: string | null;
  month: number | null;
  gridCellId: string | null;
  datasetResolution: string | null;
  cacheHit: boolean;
  warning: string | null;
}

export interface ClimateSurfaceMetadata {
  activeRasterLayer: string;
  renderedGridResolution: string;
  sampledCellCount: number;
  climateSurfaceSource: string;
}

export interface ClimateSurfaceResult {
  geojson: RegionClimateFeatureCollection;
  metadata: ClimateSurfaceMetadata;
}

export interface ClimateSurfacePayload {
  bbox: [number, number, number, number];
  zoom: number;
  layerType: string;
  warming: number;
  year: number;
  season: Season;
}

export interface ClimateCellDetail {
  gridCellId: string;
  layerType: string;
  year: number;
  warmingLevel: number;
  season: string;
  rawSampledValue: number;
  normalizedScore: number;
  scoreExplanation: string;
  dominantRiskFactor: string;
  confidenceLevel: string;
  fallbackSourceUsed: string;
}

export interface ClimateCellDetailPayload {
  gridCellId: string;
  layerType: string;
  year: number;
  warming: number;
  season: Season;
}

export interface AIExplanation {
  humanSummary: string;
  commuteImpact: string;
  outdoorActivityImpact: string;
  nighttimeRecovery: string;
  vulnerableGroupsNote: string;
  confidenceNote: string;
  explanationSource: "template" | "llm" | string;
}

export interface AIExplanationPayload {
  city: MapCityNodeData;
  year: number;
  warming: number;
  season: Season;
  timeOfDay: string;
  outdoorComfort: string;
  climateRegionType: string;
  dominantRiskDriver: string;
  selectedGridCell?: ClimateCellDetail | null;
  interactionSummary?: ClimateInteractionResult | null;
}

export interface SavedScenario {
  id: number;
  name: string;
  locationName: string;
  region: string;
  latitude: number;
  longitude: number;
  year: number;
  warmingLevel: number;
  season: Season;
  timeOfDay: string;
  activeLayer: string;
  livabilityScore: number;
  heatRisk: string;
  floodRisk: string;
  outdoorComfort: string;
  createdAt: string;
}

export type WarmingPathway = "optimistic" | "moderate" | "severe";

export interface ClimateTimelineSnapshot {
  year: number;
  warmingLevel: number;
  livabilityScore: number;
  heatScore: number;
  floodScore: number;
  outdoorComfortScore: number;
  heatRisk: string;
  floodRisk: string;
  outdoorComfort: string;
  dominantRiskDriver: string;
  rasterGridCellId: string | null;
  rasterSampledValue: number | null;
  rasterSource: string | null;
}

export interface ClimateTimelineResult {
  locationName: string;
  warmingPathway: WarmingPathway;
  layerType: string;
  season: Season;
  startYear: number;
  endYear: number;
  temporalResolution: string;
  valueMode: string;
  climateEvolutionSummary: string;
  snapshots: ClimateTimelineSnapshot[];
}

export interface ClimateTimelinePayload {
  location: string;
  startYear: number;
  endYear: number;
  warmingPathway: WarmingPathway;
  layerType: string;
  season: Season;
}

export interface ClimateInteractionResult {
  compositeRiskScore: number;
  dominantInteractionChain: string;
  resilienceScore: number;
  infrastructurePressure: number;
  humanExposureScore: number;
  cascadingRisks: string[];
  mitigationFactors: string[];
  visualIndicators: string[];
  activeInteractionModel: string;
  interactionWeights: Record<string, number>;
  resilienceModifiers: Record<string, number>;
  cascadingChainDepth: number;
}

export interface ClimateInteractionPayload {
  city: MapCityNodeData;
  year: number;
  warming: number;
  season: Season;
  timeOfDay: string;
  activeLayers: string[];
  selectedGridCell?: ClimateCellDetail | null;
}

export interface RecommendationPreferences {
  targetYear: number;
  warmingTolerance: number;
  heatSensitivity: number;
  respiratorySensitivity: number;
  floodRiskTolerance: number;
  outdoorLifestylePreference: number;
  urbanVsQuieterPreference: "urban" | "quieter" | "balanced";
  coastalPreference: "coastal" | "inland" | "neutral";
  familyElderlySensitivity: number;
  remoteWorkFlexibility: number;
}

export interface RecommendedRegion {
  regionName: string;
  locationName: string;
  latitude: number;
  longitude: number;
  suitabilityScore: number;
  resilienceScore: number;
  dominantFutureRisks: string[];
  expectedLivabilityTrajectory: string;
  majorTradeoffs: string[];
  explanation: string;
}

export interface RegionComparisonProjection {
  locationName: string;
  region: string;
  livabilityScore: number;
  heatRisk: string;
  floodRisk: string;
  outdoorComfort: string;
  resilienceScore: number;
  dominantRiskDriver: string;
}

export interface RecommendationResult {
  currentLocation: RegionComparisonProjection;
  recommendedRegions: RecommendedRegion[];
  fallbackAlternatives: RecommendedRegion[];
  comparisonProjection: RegionComparisonProjection[];
  explanationSummary: string;
  timelineNarratives: string[];
  recommendationModel: string;
}

export interface RecommendationPayload {
  city: MapCityNodeData;
  preferences: RecommendationPreferences;
}

export interface AdvisorExtractedInputs {
  primaryLocation: string;
  comparisonLocations: string[];
  targetYear: number;
  warmingLevel: number;
  season: Season;
  healthConstraints: string[];
  lifestyleConstraints: string[];
  relocationIntent: boolean;
  riskTolerance: string;
}

export interface AdvisorResult {
  interpretedQuery: string;
  extractedInputs: AdvisorExtractedInputs;
  primaryLocationScore: ScenarioScoreResult;
  recommendationSummary: string;
  keyRisks: string[];
  suggestedComparisonLocations: RecommendedRegion[];
  fallbackLocations: RecommendedRegion[];
  humanExplanation: AIExplanation;
  confidenceNote: string;
}

export interface AdvisorQueryPayload {
  queryText: string;
  selectedPreferences: string[];
  currentScenarioState?: {
    location: string;
    year: number;
    warming: number;
    season: Season;
  };
}

export interface SaveScenarioPayload {
  name: string;
  city: MapCityNodeData;
  year: number;
  warming: number;
  season: Season;
  timeOfDay: string;
  activeLayer: string;
  outdoorComfort: string;
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
  rasterSample: RasterSample | null;
  dataEvidence: ClimateDataEvidence | null;
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
  raster_sample?: {
    sampled_value: number;
    grid_cell_id: string;
    raster_source: string;
    dataset_name: string;
    dataset_resolution: string;
    layer_type: string;
  } | null;
  data_evidence?: {
    data_mode: string;
    source_label: string;
    confidence: string;
    sampled_variable?: string | null;
    sampled_value?: number | null;
    sampled_unit?: string | null;
    model?: string | null;
    scenario?: string | null;
    period?: string | null;
    month?: number | null;
    grid_cell_id?: string | null;
    dataset_resolution?: string | null;
    cache_hit: boolean;
    warning?: string | null;
  } | null;
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
  boundary_source: "database" | "real_geojson" | "simulated_fallback" | "simulated";
  boundary_name?: string | null;
  boundary_match_reason?: string | null;
  climate_region_type?: string | null;
  db_boundary_id?: number | null;
  polygon: [number, number][];
  geojson?: RegionBoundaryFeatureCollection | null;
}

interface ApiClimateSurfaceResult {
  layer_type: string;
  bbox: number[];
  zoom: number;
  grid_resolution: string;
  sampled_cell_count: number;
  climate_surface_source: string;
  geojson: RegionClimateFeatureCollection;
}

interface ApiClimateCellDetailResult {
  grid_cell_id: string;
  layer_type: string;
  year: number;
  warming_level: number;
  season: string;
  raw_sampled_value: number;
  normalized_score: number;
  score_explanation: string;
  dominant_risk_factor: string;
  confidence_level: string;
  fallback_source_used: string;
}

interface ApiExplanationResult {
  human_summary: string;
  commute_impact: string;
  outdoor_activity_impact: string;
  nighttime_recovery: string;
  vulnerable_groups_note: string;
  confidence_note: string;
  explanation_source: string;
}

interface ApiSavedScenario {
  id: number;
  name: string;
  location_name: string;
  region: string;
  latitude: number;
  longitude: number;
  year: number;
  warming_level: number;
  season: string;
  time_of_day: string;
  active_layer: string;
  livability_score: number;
  heat_risk: string;
  flood_risk: string;
  outdoor_comfort: string;
  created_at: string;
}

interface ApiClimateTimelineSnapshot {
  year: number;
  warming_level: number;
  livability_score: number;
  heat_score: number;
  flood_score: number;
  outdoor_comfort_score: number;
  heat_risk: string;
  flood_risk: string;
  outdoor_comfort: string;
  dominant_risk_driver: string;
  raster_grid_cell_id?: string | null;
  raster_sampled_value?: number | null;
  raster_source?: string | null;
}

interface ApiClimateTimelineResult {
  location: ApiLocationResult;
  warming_pathway: WarmingPathway;
  layer_type: string;
  season: string;
  start_year: number;
  end_year: number;
  temporal_resolution: string;
  value_mode: string;
  climate_evolution_summary: string;
  snapshots: ApiClimateTimelineSnapshot[];
}

interface ApiClimateInteractionResult {
  composite_risk_score: number;
  dominant_interaction_chain: string;
  resilience_score: number;
  infrastructure_pressure: number;
  human_exposure_score: number;
  cascading_risks: string[];
  mitigation_factors: string[];
  visual_indicators: string[];
  active_interaction_model: string;
  interaction_weights: Record<string, number>;
  resilience_modifiers: Record<string, number>;
  cascading_chain_depth: number;
}

interface ApiRecommendedRegion {
  region_name: string;
  location_name: string;
  latitude: number;
  longitude: number;
  suitability_score: number;
  resilience_score: number;
  dominant_future_risks: string[];
  expected_livability_trajectory: string;
  major_tradeoffs: string[];
  explanation: string;
}

interface ApiRegionComparisonProjection {
  location_name: string;
  region: string;
  livability_score: number;
  heat_risk: string;
  flood_risk: string;
  outdoor_comfort: string;
  resilience_score: number;
  dominant_risk_driver: string;
}

interface ApiRecommendationResult {
  current_location: ApiRegionComparisonProjection;
  recommended_regions: ApiRecommendedRegion[];
  fallback_alternatives: ApiRecommendedRegion[];
  comparison_projection: ApiRegionComparisonProjection[];
  explanation_summary: string;
  timeline_narratives: string[];
  recommendation_model: string;
}

interface ApiAdvisorExtractedInputs {
  primary_location: string;
  comparison_locations: string[];
  target_year: number;
  warming_level: number;
  season: string;
  health_constraints: string[];
  lifestyle_constraints: string[];
  relocation_intent: boolean;
  risk_tolerance: string;
}

interface ApiAdvisorResult {
  interpreted_query: string;
  extracted_inputs: ApiAdvisorExtractedInputs;
  primary_location_score: ApiScenarioScoreResult;
  recommendation_summary: string;
  key_risks: string[];
  suggested_comparison_locations: ApiRecommendedRegion[];
  fallback_locations: ApiRecommendedRegion[];
  human_explanation: ApiExplanationResult;
  confidence_note: string;
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
    rasterSample: payload.raster_sample
      ? {
          sampledValue: payload.raster_sample.sampled_value,
          gridCellId: payload.raster_sample.grid_cell_id,
          rasterSource: payload.raster_sample.raster_source,
          datasetName: payload.raster_sample.dataset_name,
          datasetResolution: payload.raster_sample.dataset_resolution,
          layerType: payload.raster_sample.layer_type,
        }
      : null,
    dataEvidence: payload.data_evidence
      ? {
          dataMode: payload.data_evidence.data_mode,
          sourceLabel: payload.data_evidence.source_label,
          confidence: payload.data_evidence.confidence,
          sampledVariable: payload.data_evidence.sampled_variable ?? null,
          sampledValue: payload.data_evidence.sampled_value ?? null,
          sampledUnit: payload.data_evidence.sampled_unit ?? null,
          model: payload.data_evidence.model ?? null,
          scenario: payload.data_evidence.scenario ?? null,
          period: payload.data_evidence.period ?? null,
          month: payload.data_evidence.month ?? null,
          gridCellId: payload.data_evidence.grid_cell_id ?? null,
          datasetResolution: payload.data_evidence.dataset_resolution ?? null,
          cacheHit: payload.data_evidence.cache_hit,
          warning: payload.data_evidence.warning ?? null,
        }
      : null,
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

export async function getAIExplanation({
  city,
  year,
  warming,
  season,
  timeOfDay,
  outdoorComfort,
  climateRegionType,
  dominantRiskDriver,
  selectedGridCell,
  interactionSummary,
}: AIExplanationPayload): Promise<AIExplanation> {
  const result = await requestJson<ApiExplanationResult>("/api/explain", {
    method: "POST",
    body: JSON.stringify({
      location: city.name,
      region: city.region,
      climate_region_type: climateRegionType,
      year,
      warming_level: warming,
      season,
      time_of_day: timeOfDay,
      livability_score: city.livabilityScore,
      heat_risk: city.heatRisk,
      flood_risk: city.floodRisk,
      outdoor_comfort: outdoorComfort,
      dominant_risk_driver: dominantRiskDriver,
      selected_grid_cell: selectedGridCell
        ? {
            grid_cell_id: selectedGridCell.gridCellId,
            layer_type: selectedGridCell.layerType,
            year: selectedGridCell.year,
            warming_level: selectedGridCell.warmingLevel,
            season: selectedGridCell.season,
            raw_sampled_value: selectedGridCell.rawSampledValue,
            normalized_score: selectedGridCell.normalizedScore,
            score_explanation: selectedGridCell.scoreExplanation,
            dominant_risk_factor: selectedGridCell.dominantRiskFactor,
            confidence_level: selectedGridCell.confidenceLevel,
            fallback_source_used: selectedGridCell.fallbackSourceUsed,
          }
        : null,
      interaction_summary: interactionSummary
        ? {
            composite_risk_score: interactionSummary.compositeRiskScore,
            dominant_interaction_chain:
              interactionSummary.dominantInteractionChain,
            resilience_score: interactionSummary.resilienceScore,
            infrastructure_pressure: interactionSummary.infrastructurePressure,
            human_exposure_score: interactionSummary.humanExposureScore,
            cascading_risks: interactionSummary.cascadingRisks,
            mitigation_factors: interactionSummary.mitigationFactors,
            visual_indicators: interactionSummary.visualIndicators,
            active_interaction_model: interactionSummary.activeInteractionModel,
            interaction_weights: interactionSummary.interactionWeights,
            resilience_modifiers: interactionSummary.resilienceModifiers,
            cascading_chain_depth: interactionSummary.cascadingChainDepth,
          }
        : null,
    }),
  });

  return {
    humanSummary: result.human_summary,
    commuteImpact: result.commute_impact,
    outdoorActivityImpact: result.outdoor_activity_impact,
    nighttimeRecovery: result.nighttime_recovery,
    vulnerableGroupsNote: result.vulnerable_groups_note,
    confidenceNote: result.confidence_note,
    explanationSource: result.explanation_source,
  };
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
          boundaryName: result.boundary_name,
          boundaryMatchReason: result.boundary_match_reason,
          dbBoundaryId: result.db_boundary_id,
          boundaryClimateRegionType: result.climate_region_type,
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
          boundaryName: result.boundary_name,
          boundaryMatchReason: result.boundary_match_reason,
          dbBoundaryId: result.db_boundary_id,
          boundaryClimateRegionType: result.climate_region_type,
        },
        geometry: {
          type: "Polygon",
          coordinates: [closedCoordinates],
        },
      },
    ],
  };
}

export async function getClimateSurface({
  bbox,
  zoom,
  layerType,
  warming,
  year,
  season,
}: ClimateSurfacePayload): Promise<ClimateSurfaceResult> {
  const params = new URLSearchParams({
    bbox: bbox.map((value) => value.toFixed(5)).join(","),
    zoom: zoom.toFixed(2),
    layer_type: layerType,
    warming_level: warming.toFixed(2),
    year: String(year),
    season,
  });
  const result = await requestJson<ApiClimateSurfaceResult>(
    `/api/climate/surface?${params.toString()}`,
  );

  return {
    geojson: result.geojson,
    metadata: {
      activeRasterLayer: result.layer_type,
      renderedGridResolution: result.grid_resolution,
      sampledCellCount: result.sampled_cell_count,
      climateSurfaceSource: result.climate_surface_source,
    },
  };
}

export async function getClimateCellDetail({
  gridCellId,
  layerType,
  year,
  warming,
  season,
}: ClimateCellDetailPayload): Promise<ClimateCellDetail> {
  const params = new URLSearchParams({
    grid_cell_id: gridCellId,
    layer_type: layerType,
    year: String(year),
    warming_level: warming.toFixed(2),
    season,
  });
  const result = await requestJson<ApiClimateCellDetailResult>(
    `/api/climate/cell-detail?${params.toString()}`,
  );

  return {
    gridCellId: result.grid_cell_id,
    layerType: result.layer_type,
    year: result.year,
    warmingLevel: result.warming_level,
    season: result.season,
    rawSampledValue: result.raw_sampled_value,
    normalizedScore: result.normalized_score,
    scoreExplanation: result.score_explanation,
    dominantRiskFactor: result.dominant_risk_factor,
    confidenceLevel: result.confidence_level,
    fallbackSourceUsed: result.fallback_source_used,
  };
}

export async function getClimateTimeline({
  location,
  startYear,
  endYear,
  warmingPathway,
  layerType,
  season,
}: ClimateTimelinePayload): Promise<ClimateTimelineResult> {
  const params = new URLSearchParams({
    location,
    start_year: String(startYear),
    end_year: String(endYear),
    warming_pathway: warmingPathway,
    layer_type: layerType,
    season,
  });
  const result = await requestJson<ApiClimateTimelineResult>(
    `/api/climate/timeline?${params.toString()}`,
  );

  return {
    locationName: result.location.location_name,
    warmingPathway: result.warming_pathway,
    layerType: result.layer_type,
    season: result.season as Season,
    startYear: result.start_year,
    endYear: result.end_year,
    temporalResolution: result.temporal_resolution,
    valueMode: result.value_mode,
    climateEvolutionSummary: result.climate_evolution_summary,
    snapshots: result.snapshots.map((snapshot) => ({
      year: snapshot.year,
      warmingLevel: snapshot.warming_level,
      livabilityScore: snapshot.livability_score,
      heatScore: snapshot.heat_score,
      floodScore: snapshot.flood_score,
      outdoorComfortScore: snapshot.outdoor_comfort_score,
      heatRisk: snapshot.heat_risk,
      floodRisk: snapshot.flood_risk,
      outdoorComfort: snapshot.outdoor_comfort,
      dominantRiskDriver: snapshot.dominant_risk_driver,
      rasterGridCellId: snapshot.raster_grid_cell_id ?? null,
      rasterSampledValue: snapshot.raster_sampled_value ?? null,
      rasterSource: snapshot.raster_source ?? null,
    })),
  };
}

export async function getCompositeRisk({
  city,
  year,
  warming,
  season,
  timeOfDay,
  activeLayers,
  selectedGridCell,
}: ClimateInteractionPayload): Promise<ClimateInteractionResult> {
  const result = await requestJson<ApiClimateInteractionResult>(
    "/api/climate/composite-risk",
    {
      method: "POST",
      body: JSON.stringify({
        scenario: {
          location: city.name,
          year,
          warmingLevel: warming,
          season,
          timeOfDay,
          overlayTypes: activeLayers,
        },
        active_layers: activeLayers,
        location: city.name,
        selected_climate_cell: selectedGridCell
          ? {
              grid_cell_id: selectedGridCell.gridCellId,
              layer_type: selectedGridCell.layerType,
              year: selectedGridCell.year,
              warming_level: selectedGridCell.warmingLevel,
              season: selectedGridCell.season,
              raw_sampled_value: selectedGridCell.rawSampledValue,
              normalized_score: selectedGridCell.normalizedScore,
              score_explanation: selectedGridCell.scoreExplanation,
              dominant_risk_factor: selectedGridCell.dominantRiskFactor,
              confidence_level: selectedGridCell.confidenceLevel,
              fallback_source_used: selectedGridCell.fallbackSourceUsed,
            }
          : null,
      }),
    },
  );

  return {
    compositeRiskScore: result.composite_risk_score,
    dominantInteractionChain: result.dominant_interaction_chain,
    resilienceScore: result.resilience_score,
    infrastructurePressure: result.infrastructure_pressure,
    humanExposureScore: result.human_exposure_score,
    cascadingRisks: result.cascading_risks,
    mitigationFactors: result.mitigation_factors,
    visualIndicators: result.visual_indicators,
    activeInteractionModel: result.active_interaction_model,
    interactionWeights: result.interaction_weights,
    resilienceModifiers: result.resilience_modifiers,
    cascadingChainDepth: result.cascading_chain_depth,
  };
}

export async function getRecommendations({
  city,
  preferences,
}: RecommendationPayload): Promise<RecommendationResult> {
  const result = await requestJson<ApiRecommendationResult>("/api/recommendations", {
    method: "POST",
    body: JSON.stringify({
      current_location: city.name,
      target_year: preferences.targetYear,
      warming_tolerance: preferences.warmingTolerance,
      heat_sensitivity: preferences.heatSensitivity,
      respiratory_sensitivity: preferences.respiratorySensitivity,
      flood_risk_tolerance: preferences.floodRiskTolerance,
      outdoor_lifestyle_preference: preferences.outdoorLifestylePreference,
      urban_vs_quieter_preference: preferences.urbanVsQuieterPreference,
      coastal_preference: preferences.coastalPreference,
      family_elderly_sensitivity: preferences.familyElderlySensitivity,
      remote_work_flexibility: preferences.remoteWorkFlexibility,
    }),
  });

  return {
    currentLocation: apiProjectionToClient(result.current_location),
    recommendedRegions: result.recommended_regions.map(apiRegionToClient),
    fallbackAlternatives: result.fallback_alternatives.map(apiRegionToClient),
    comparisonProjection: result.comparison_projection.map(apiProjectionToClient),
    explanationSummary: result.explanation_summary,
    timelineNarratives: result.timeline_narratives,
    recommendationModel: result.recommendation_model,
  };
}

export async function queryClimateAdvisor({
  queryText,
  selectedPreferences,
  currentScenarioState,
}: AdvisorQueryPayload): Promise<AdvisorResult> {
  const result = await requestJson<ApiAdvisorResult>("/api/advisor/query", {
    method: "POST",
    body: JSON.stringify({
      query_text: queryText,
      selected_preferences: selectedPreferences,
      current_scenario_state: currentScenarioState
        ? {
            location: currentScenarioState.location,
            year: currentScenarioState.year,
            warming: currentScenarioState.warming,
            season: currentScenarioState.season,
          }
        : null,
    }),
  });

  return {
    interpretedQuery: result.interpreted_query,
    extractedInputs: {
      primaryLocation: result.extracted_inputs.primary_location,
      comparisonLocations: result.extracted_inputs.comparison_locations,
      targetYear: result.extracted_inputs.target_year,
      warmingLevel: result.extracted_inputs.warming_level,
      season: result.extracted_inputs.season as Season,
      healthConstraints: result.extracted_inputs.health_constraints,
      lifestyleConstraints: result.extracted_inputs.lifestyle_constraints,
      relocationIntent: result.extracted_inputs.relocation_intent,
      riskTolerance: result.extracted_inputs.risk_tolerance,
    },
    primaryLocationScore: apiScenarioToScore(
      apiLocationToCity(result.primary_location_score.location),
      result.primary_location_score,
    ),
    recommendationSummary: result.recommendation_summary,
    keyRisks: result.key_risks,
    suggestedComparisonLocations:
      result.suggested_comparison_locations.map(apiRegionToClient),
    fallbackLocations: result.fallback_locations.map(apiRegionToClient),
    humanExplanation: {
      humanSummary: result.human_explanation.human_summary,
      commuteImpact: result.human_explanation.commute_impact,
      outdoorActivityImpact: result.human_explanation.outdoor_activity_impact,
      nighttimeRecovery: result.human_explanation.nighttime_recovery,
      vulnerableGroupsNote: result.human_explanation.vulnerable_groups_note,
      confidenceNote: result.human_explanation.confidence_note,
      explanationSource: result.human_explanation.explanation_source,
    },
    confidenceNote: result.confidence_note,
  };
}

function apiRegionToClient(region: ApiRecommendedRegion): RecommendedRegion {
  return {
    regionName: region.region_name,
    locationName: region.location_name,
    latitude: region.latitude,
    longitude: region.longitude,
    suitabilityScore: region.suitability_score,
    resilienceScore: region.resilience_score,
    dominantFutureRisks: region.dominant_future_risks,
    expectedLivabilityTrajectory: region.expected_livability_trajectory,
    majorTradeoffs: region.major_tradeoffs,
    explanation: region.explanation,
  };
}

function apiProjectionToClient(
  projection: ApiRegionComparisonProjection,
): RegionComparisonProjection {
  return {
    locationName: projection.location_name,
    region: projection.region,
    livabilityScore: projection.livability_score,
    heatRisk: projection.heat_risk,
    floodRisk: projection.flood_risk,
    outdoorComfort: projection.outdoor_comfort,
    resilienceScore: projection.resilience_score,
    dominantRiskDriver: projection.dominant_risk_driver,
  };
}

function apiSavedScenarioToClient(scenario: ApiSavedScenario): SavedScenario {
  return {
    id: scenario.id,
    name: scenario.name,
    locationName: scenario.location_name,
    region: scenario.region,
    latitude: scenario.latitude,
    longitude: scenario.longitude,
    year: scenario.year,
    warmingLevel: scenario.warming_level,
    season: scenario.season as Season,
    timeOfDay: scenario.time_of_day,
    activeLayer: scenario.active_layer,
    livabilityScore: scenario.livability_score,
    heatRisk: scenario.heat_risk,
    floodRisk: scenario.flood_risk,
    outdoorComfort: scenario.outdoor_comfort,
    createdAt: scenario.created_at,
  };
}

export async function saveScenario({
  name,
  city,
  year,
  warming,
  season,
  timeOfDay,
  activeLayer,
  outdoorComfort,
}: SaveScenarioPayload): Promise<SavedScenario> {
  const result = await requestJson<ApiSavedScenario>("/api/scenarios/save", {
    method: "POST",
    body: JSON.stringify({
      name,
      location_name: city.name,
      region: city.region,
      latitude: city.latitude,
      longitude: city.longitude,
      year,
      warming_level: warming,
      season,
      time_of_day: timeOfDay,
      active_layer: activeLayer,
      livability_score: city.livabilityScore,
      heat_risk: city.heatRisk,
      flood_risk: city.floodRisk,
      outdoor_comfort: outdoorComfort,
    }),
  });

  return apiSavedScenarioToClient(result);
}

export async function listSavedScenarios(): Promise<SavedScenario[]> {
  const results = await requestJson<ApiSavedScenario[]>("/api/scenarios");

  return results.map(apiSavedScenarioToClient);
}

export async function getSavedScenario(id: number): Promise<SavedScenario> {
  const result = await requestJson<ApiSavedScenario>(`/api/scenarios/${id}`);

  return apiSavedScenarioToClient(result);
}

export async function deleteSavedScenario(id: number): Promise<void> {
  await requestJson<{ deleted: boolean }>(`/api/scenarios/${id}`, {
    method: "DELETE",
  });
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
