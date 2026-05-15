import type { AreaRiskData } from "@/components/AreaRiskInspector";
import type { MapCityNodeData } from "@/components/MapCityNode";
import type { RegionalMappingData } from "@/components/regionalTypes";
import {
  createKnownRegionalMapping,
  createRegionBoundary,
  type RegionBoundaryFeatureCollection,
  type Season,
} from "@/lib/climateOverlaySimulation";
import type { LocalUrbanCellData } from "@/lib/localCellSimulation";
import { knownCityNodes } from "@/lib/api/mockData";

export interface ScenarioScorePayload {
  city: MapCityNodeData;
  warming: number;
  localUrbanCell?: LocalUrbanCellData | null;
}

export interface ScenarioScoreResult {
  city: MapCityNodeData;
  outdoorComfort: string;
}

export interface ScenarioComparisonConfig {
  year: number;
  warming: number;
  season: Season;
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

function getRiskScoreFromLabel(label: string) {
  if (label === "High") {
    return 78;
  }

  if (label === "Elevated" || label === "Rising") {
    return 62;
  }

  if (label === "Moderate" || label === "Variable" || label === "Medium") {
    return 42;
  }

  return 22;
}

function getGreenCoverScore(value: string) {
  const parsedValue = Number.parseInt(value.replace("%", ""), 10);

  return Number.isFinite(parsedValue) ? parsedValue : 20;
}

function formatGreenCover(value: number) {
  return `${Math.min(48, Math.max(4, Math.round(value)))}%`;
}

function getQueryHash(value: string) {
  return value
    .trim()
    .toLowerCase()
    .split("")
    .reduce((total, character) => total + character.charCodeAt(0), 0);
}

function createRegionalMapping(
  query: string,
  center: [number, number],
): RegionalMappingData {
  const hash = getQueryHash(query);
  const climateZones = [
    "Tropical urban belt",
    "Semi-arid transition zone",
    "Temperate maritime cell",
    "Humid subtropical corridor",
  ];
  const longitude = Number(
    (center[0] + ((hash % 17) - 8) * 0.08).toFixed(4),
  );
  const latitude = Number(
    (center[1] + ((hash % 13) - 6) * 0.08).toFixed(4),
  );

  return {
    inputLocation: query.trim(),
    mappedRegion: `Simulated Region ${String.fromCharCode(65 + (hash % 6))}`,
    climateZone: climateZones[hash % climateZones.length],
    confidence: hash % 3 === 0 ? "Medium" : "High",
    nearestGridCell: `FC-GRID-${(1000 + (hash % 9000)).toString()}`,
    boundarySource: "simulated",
    longitude,
    latitude,
  };
}

function createRegionalCity(mapping: RegionalMappingData): MapCityNodeData {
  const hash = getQueryHash(mapping.inputLocation);

  return {
    name: mapping.inputLocation,
    region: mapping.mappedRegion,
    longitude: mapping.longitude,
    latitude: mapping.latitude,
    x: 50,
    y: 50,
    livabilityScore: Math.max(58, 78 - (hash % 18)),
    heatRisk: hash % 2 === 0 ? "Elevated" : "Moderate",
    floodRisk: hash % 3 === 0 ? "Elevated" : "Moderate",
    greenCover: `${18 + (hash % 16)}%`,
    futureSummary:
      "Regional extrapolation estimates future comfort and climate pressure from nearby simulated climate cells.",
    sportsCultureImpact:
      "Local outdoor routines, neighborhood sport, and high-street culture become more sensitive to heat timing and cooling access.",
    accent: "bg-fuchsia-400/20",
  };
}

export function getOutdoorComfort(
  warming: number,
  localCell?: LocalUrbanCellData | null,
) {
  const comfortScore = Math.max(
    18,
    Math.round(86 - warming * 15 + (localCell?.outdoorComfortAdjustment ?? 0)),
  );

  return getComfortLabel(comfortScore);
}

export function searchLocation({
  query,
  fallbackCenter,
}: SearchLocationPayload): SearchLocationResult {
  const normalizedQuery = query.trim().toLowerCase();
  const matchedCity = knownCityNodes.find(
    (city) => city.name.toLowerCase() === normalizedQuery,
  );

  if (matchedCity) {
    return {
      kind: "known",
      city: matchedCity,
      regionalMapping: createKnownRegionalMapping(matchedCity.name),
    };
  }

  const fallbackQuery = query.trim() || "Unmapped urban cell";
  const regionalMapping = createRegionalMapping(fallbackQuery, fallbackCenter);

  return {
    kind: "regional",
    city: createRegionalCity(regionalMapping),
    regionalMapping,
  };
}

export function getScenarioScore({
  city,
  warming,
  localUrbanCell,
}: ScenarioScorePayload): ScenarioScoreResult {
  const heatPressure = Math.max(0, warming - 1);
  const livabilityScore = Math.max(
    42,
    Math.round(
      city.livabilityScore -
        heatPressure * 6 +
        (localUrbanCell?.livabilityAdjustment ?? 0),
    ),
  );
  const heatScore =
    getRiskScoreFromLabel(city.heatRisk) +
    heatPressure * 14 +
    (localUrbanCell?.heatRiskAdjustment ?? 0);
  const floodScore =
    getRiskScoreFromLabel(city.floodRisk) +
    (localUrbanCell?.floodRiskAdjustment ?? 0);

  return {
    city: {
      ...city,
      livabilityScore,
      heatRisk: getRiskLabel(heatScore),
      floodRisk: getRiskLabel(floodScore),
      greenCover: formatGreenCover(
        getGreenCoverScore(city.greenCover) +
          (localUrbanCell?.greenCoverAdjustment ?? 0),
      ),
    },
    outdoorComfort: getOutdoorComfort(warming, localUrbanCell),
  };
}

export function getHumanImpactExplanation({
  scenarioA,
  scenarioB,
}: HumanImpactExplanationPayload) {
  if (scenarioA && scenarioB) {
    return "Summer nighttime cooling becomes significantly weaker, increasing discomfort during heatwaves.";
  }

  return "Future comfort is shaped by heat timing, cooling access, mobility patterns, and the local urban form around the selected area.";
}

export function compareScenarios({
  city,
  scenarioA,
  scenarioB,
  localUrbanCell,
}: CompareScenariosPayload): ComparisonMetrics {
  const cityA = getScenarioScore({
    city,
    warming: scenarioA.warming,
    localUrbanCell,
  }).city;
  const cityB = getScenarioScore({
    city,
    warming: scenarioB.warming,
    localUrbanCell,
  }).city;
  const heatIncrease = Math.max(
    0,
    Math.round((scenarioB.warming - scenarioA.warming) * 16),
  );
  const livabilityDecline = Math.max(
    0,
    cityA.livabilityScore - cityB.livabilityScore,
  );
  const localComfortAdjustment = localUrbanCell?.outdoorComfortAdjustment ?? 0;
  const comfortA = Math.max(
    18,
    Math.round(86 - scenarioA.warming * 15 + localComfortAdjustment),
  );
  const comfortB = Math.max(
    18,
    Math.round(86 - scenarioB.warming * 15 + localComfortAdjustment),
  );

  return {
    heatIncrease,
    livabilityDecline,
    outdoorComfortChange: Math.max(0, comfortA - comfortB),
    scientificMetric: `Wet bulb anomaly +${Math.max(
      0,
      scenarioB.warming - scenarioA.warming + 0.6,
    ).toFixed(1)}C`,
    humanTranslation: getHumanImpactExplanation({ city, scenarioA, scenarioB }),
  };
}

export function getRegionBoundary(
  locationId: RegionalMappingData,
): RegionBoundaryFeatureCollection {
  return createRegionBoundary(locationId);
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
