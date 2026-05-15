import type { RegionalMappingData } from "@/components/regionalTypes";
import type { LocalUrbanCellData } from "@/lib/localCellSimulation";
import type { Feature, FeatureCollection, Polygon } from "geojson";

export type ClimateOverlayName =
  | "Heat Risk"
  | "Flood Risk"
  | "Outdoor Comfort"
  | "Green Cover"
  | "Livability Stress";

export type ClimateSurfaceKind = "heat" | "flood" | "comfort" | "livability";
export type Season = "Spring" | "Summer" | "Monsoon" | "Winter";

type RegionClimateProperties = {
  id: string;
  heat: number;
  flood: number;
  comfort: number;
  livability: number;
  alpha: number;
};

export type RegionClimateFeatureCollection = FeatureCollection<
  Polygon,
  RegionClimateProperties
>;

export type RegionBoundaryFeatureCollection = FeatureCollection<
  Polygon,
  { id: string; label: string }
>;

export interface ClimateOverlayScenario {
  year: number;
  warming: number;
  season: Season;
  enabledLayers: Partial<Record<string, boolean>>;
  localUrbanCell: LocalUrbanCellData | null;
}

export interface ClimateOverlayRenderModel {
  id: ClimateOverlayName;
  kind: ClimateSurfaceKind;
  label: string;
  legendGradient: string;
  colorProperty: "heat" | "flood" | "comfort" | "livability";
  intensity: number;
  opacity: number;
  season: Season;
  coverage: number;
}

type RegionKey =
  | "mumbai"
  | "bangalore"
  | "madrid"
  | "istanbul"
  | "manchester";

const knownRegionBoundaries: Record<RegionKey, [number, number][]> = {
  mumbai: [
    [72.0, 21.2],
    [73.5, 21.0],
    [74.4, 20.3],
    [74.1, 18.9],
    [73.2, 17.4],
    [72.2, 16.9],
    [71.7, 18.5],
    [71.6, 20.1],
  ],
  bangalore: [
    [74.2, 15.0],
    [76.4, 15.4],
    [78.8, 14.8],
    [79.0, 12.3],
    [77.8, 10.8],
    [75.5, 11.0],
    [74.0, 12.6],
  ],
  madrid: [
    [-5.0, 41.2],
    [-3.8, 41.4],
    [-2.7, 40.8],
    [-2.6, 39.8],
    [-3.5, 39.3],
    [-4.8, 39.6],
    [-5.2, 40.4],
  ],
  istanbul: [
    [26.6, 41.6],
    [28.2, 42.0],
    [30.7, 41.7],
    [31.3, 40.7],
    [29.7, 40.2],
    [27.5, 40.3],
    [26.4, 40.9],
  ],
  manchester: [
    [-3.7, 54.0],
    [-2.4, 54.2],
    [-1.1, 53.8],
    [-1.2, 53.0],
    [-2.0, 52.6],
    [-3.5, 52.8],
    [-4.0, 53.4],
  ],
};

export function createKnownRegionalMapping(
  cityName: string,
): RegionalMappingData | null {
  const normalizedName = cityName.trim().toLowerCase() as RegionKey;
  const knownRegions: Record<RegionKey, Omit<RegionalMappingData, "boundarySource">> = {
    mumbai: {
      inputLocation: "Mumbai",
      mappedRegion: "Maharashtra coastal region",
      climateZone: "Tropical coastal heat and flood cell",
      confidence: "High",
      nearestGridCell: "FC-GRID-MH-2040",
      longitude: 72.8777,
      latitude: 19.076,
    },
    bangalore: {
      inputLocation: "Bangalore",
      mappedRegion: "Karnataka plateau region",
      climateZone: "Tropical highland urban heat cell",
      confidence: "High",
      nearestGridCell: "FC-GRID-KA-1337",
      longitude: 77.5946,
      latitude: 12.9716,
    },
    madrid: {
      inputLocation: "Madrid",
      mappedRegion: "Community of Madrid / central Spain",
      climateZone: "Mediterranean continental heat cell",
      confidence: "High",
      nearestGridCell: "FC-GRID-MD-4016",
      longitude: -3.7038,
      latitude: 40.4168,
    },
    istanbul: {
      inputLocation: "Istanbul",
      mappedRegion: "Marmara region",
      climateZone: "Mediterranean maritime transition cell",
      confidence: "High",
      nearestGridCell: "FC-GRID-MR-4100",
      longitude: 28.9784,
      latitude: 41.0082,
    },
    manchester: {
      inputLocation: "Manchester",
      mappedRegion: "Greater Manchester / North West England",
      climateZone: "Temperate maritime rainfall cell",
      confidence: "High",
      nearestGridCell: "FC-GRID-NW-5348",
      longitude: -2.2426,
      latitude: 53.4808,
    },
  };

  const mapping = knownRegions[normalizedName];

  return mapping ? { ...mapping, boundarySource: "simulated" } : null;
}

export function createRegionBoundary(
  mapping: RegionalMappingData,
): RegionBoundaryFeatureCollection {
  const ring = getRegionBoundaryRing(mapping);

  return {
    type: "FeatureCollection",
    features: [
      {
        type: "Feature",
        properties: {
          id: mapping.nearestGridCell,
          label: mapping.mappedRegion,
        },
        geometry: {
          type: "Polygon",
          coordinates: [[...ring, ring[0]]],
        },
      },
    ],
  };
}

export function createRegionClimateSurface(
  mapping: RegionalMappingData,
  overlay?: ClimateOverlayRenderModel,
): RegionClimateFeatureCollection {
  const ring = getRegionBoundaryRing(mapping);
  const center = getRingCenter(ring);
  const coverage = overlay?.coverage ?? 0.78;
  const scales = [
    coverage,
    coverage * 0.86,
    coverage * 0.72,
    coverage * 0.58,
    coverage * 0.44,
    coverage * 0.32,
    coverage * 0.22,
  ];
  const heatBias = getRegionHeatBias(mapping);
  const floodBias = getRegionFloodBias(mapping);
  const season = overlay?.season ?? "Summer";
  const heatSeasonBoost = season === "Summer" ? 12 : season === "Winter" ? -14 : 0;
  const floodSeasonBoost = season === "Monsoon" ? 18 : season === "Winter" ? -6 : 0;
  const comfortSeasonBoost = season === "Winter" ? 14 : season === "Summer" ? -12 : 0;

  return {
    type: "FeatureCollection",
    features: scales.flatMap((scale, index) => {
      const direction = index % 2 === 0 ? 1 : -1;
      const shiftedCenter: [number, number] = [
        center[0] + (index - 3) * 0.045 * direction,
        center[1] + (index % 3 === 0 ? 0.07 : -0.045),
      ];
      const polygon = scaleRing(ring, shiftedCenter, scale, index);
      const ridge = Math.sin(index * 1.9 + mapping.longitude * 0.07) * 8;
      const heat = clamp(heatBias + heatSeasonBoost + (6 - index) * 5 + ridge, 0, 100);
      const flood = clamp(floodBias + floodSeasonBoost + (index % 3) * 8 - ridge * 0.4, 0, 100);
      const comfort = clamp(
        88 + comfortSeasonBoost - heat * 0.56 - flood * 0.14 + index * 2.2,
        8,
        100,
      );
      const livability = clamp(94 - heat * 0.4 - flood * 0.22 - index * 1.6, 8, 100);

      return [
        feature(`${mapping.nearestGridCell}-band-${index}`, polygon, {
          heat,
          flood,
          comfort,
          livability,
          alpha: 0.18 + (6 - index) * 0.055,
        }),
      ];
    }),
  };
}

function getRegionBoundaryRing(mapping: RegionalMappingData): [number, number][] {
  const knownKey = mapping.inputLocation.trim().toLowerCase() as RegionKey;
  const knownRing = knownRegionBoundaries[knownKey];

  if (knownRing) {
    return knownRing;
  }

  return createIrregularBoundary(mapping.longitude, mapping.latitude);
}

function createIrregularBoundary(
  longitude: number,
  latitude: number,
): [number, number][] {
  const radiusLng = 1.4;
  const radiusLat = 1.0;
  const hash = Math.abs(Math.sin(longitude * 12.9898 + latitude * 78.233));

  return Array.from({ length: 9 }, (_, index) => {
    const angle = (Math.PI * 2 * index) / 9;
    const wobble = 0.78 + (((index * 37 + Math.round(hash * 100)) % 29) / 100);

    return [
      Number((longitude + Math.cos(angle) * radiusLng * wobble).toFixed(4)),
      Number((latitude + Math.sin(angle) * radiusLat * wobble).toFixed(4)),
    ];
  });
}

function scaleRing(
  ring: [number, number][],
  center: [number, number],
  scale: number,
  phase: number,
): [number, number][] {
  return ring.map(([longitude, latitude], index) => {
    const wobble = 1 + Math.sin(index * 1.7 + phase) * 0.045;

    return [
      Number((center[0] + (longitude - center[0]) * scale * wobble).toFixed(4)),
      Number((center[1] + (latitude - center[1]) * scale * wobble).toFixed(4)),
    ];
  });
}

function getRingCenter(ring: [number, number][]): [number, number] {
  const totals = ring.reduce(
    (sum, [longitude, latitude]) => [sum[0] + longitude, sum[1] + latitude],
    [0, 0],
  );

  return [totals[0] / ring.length, totals[1] / ring.length];
}

function feature(
  id: string,
  coordinates: [number, number][],
  properties: Omit<RegionClimateProperties, "id">,
): Feature<Polygon, RegionClimateProperties> {
  return {
    type: "Feature",
    properties: {
      id,
      ...properties,
    },
    geometry: {
      type: "Polygon",
      coordinates: [[...coordinates, coordinates[0]]],
    },
  };
}

function getRegionHeatBias(mapping: RegionalMappingData) {
  const name = `${mapping.inputLocation} ${mapping.mappedRegion}`.toLowerCase();

  if (name.includes("mumbai") || name.includes("maharashtra")) return 82;
  if (name.includes("bangalore") || name.includes("karnataka")) return 68;
  if (name.includes("madrid") || name.includes("spain")) return 62;
  if (name.includes("istanbul") || name.includes("marmara")) return 58;
  if (name.includes("manchester") || name.includes("england")) return 38;

  return 56 + (mapping.nearestGridCell.charCodeAt(mapping.nearestGridCell.length - 1) % 22);
}

function getRegionFloodBias(mapping: RegionalMappingData) {
  const name = `${mapping.inputLocation} ${mapping.mappedRegion}`.toLowerCase();

  if (name.includes("mumbai") || name.includes("coastal")) return 72;
  if (name.includes("manchester")) return 58;
  if (name.includes("istanbul") || name.includes("marmara")) return 48;
  if (name.includes("bangalore")) return 38;
  if (name.includes("madrid")) return 22;

  return 36 + (mapping.nearestGridCell.charCodeAt(0) % 24);
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function getActiveSurfaceKind(
  enabledLayers: Partial<Record<string, boolean>>,
): ClimateSurfaceKind | null {
  if (enabledLayers["Heat Risk"]) return "heat";
  if (enabledLayers["Flood Risk"]) return "flood";
  if (enabledLayers["Outdoor Comfort"]) return "comfort";
  if (enabledLayers["Livability Stress"]) return "livability";

  return null;
}

function getScenarioOpacity({
  warming,
  year,
  season,
  kind,
  localUrbanCell,
}: {
  warming: number;
  year: number;
  season: Season;
  kind: ClimateSurfaceKind;
  localUrbanCell: LocalUrbanCellData | null;
}) {
  const warmingPressure = clamp((warming - 1) / 3, 0, 1);
  const yearPressure = clamp((year - 2025) / 25, 0, 1);
  const seasonBoost =
    (kind === "heat" && season === "Summer") ||
    (kind === "flood" && season === "Monsoon")
      ? 0.08
      : 0;
  const localBoost =
    kind === "heat"
      ? (localUrbanCell?.heatRiskAdjustment ?? 0) / 280
      : kind === "flood"
        ? (localUrbanCell?.floodRiskAdjustment ?? 0) / 300
        : -(localUrbanCell?.outdoorComfortAdjustment ?? 0) / 320;

  return clamp(
    0.5 + warmingPressure * 0.14 + yearPressure * 0.06 + seasonBoost + localBoost,
    0.34,
    0.68,
  );
}

function getOverlayMeta(kind: ClimateSurfaceKind) {
  if (kind === "flood") {
    return {
      id: "Flood Risk" as const,
      label: "Flood Exposure",
      colorProperty: "flood" as const,
      legendGradient:
        "linear-gradient(90deg, transparent, #22d3ee, #2563eb, #581c87)",
    };
  }

  if (kind === "comfort") {
    return {
      id: "Outdoor Comfort" as const,
      label: "Outdoor Comfort",
      colorProperty: "comfort" as const,
      legendGradient:
        "linear-gradient(90deg, #ef4444, #f97316, #facc15, #14b8a6)",
    };
  }

  if (kind === "livability") {
    return {
      id: "Livability Stress" as const,
      label: "Livability Stress",
      colorProperty: "livability" as const,
      legendGradient:
        "linear-gradient(90deg, #14b8a6, #facc15, #f97316, #991b1b)",
    };
  }

  return {
    id: "Heat Risk" as const,
    label: "Heat Risk",
    colorProperty: "heat" as const,
    legendGradient:
      "linear-gradient(90deg, #facc15, #f97316, #dc2626, #7f1d1d)",
  };
}

export function generateClimateOverlays({
  year,
  warming,
  season,
  enabledLayers,
  localUrbanCell,
}: ClimateOverlayScenario): ClimateOverlayRenderModel[] {
  const kind = getActiveSurfaceKind(enabledLayers);

  if (!kind) {
    return [];
  }

  const meta = getOverlayMeta(kind);

  return [
    {
      ...meta,
      kind,
      opacity: getScenarioOpacity({
        warming,
        year,
        season,
        kind,
        localUrbanCell,
      }),
      intensity: clamp(0.84 + (warming - 1) * 0.16 + (year - 2025) / 130, 0.8, 1.42),
      season,
      coverage: clamp(
        0.62 +
          (warming - 1) * 0.08 +
          (year - 2025) / 110 +
          (season === "Summer" ? 0.08 : season === "Monsoon" ? 0.05 : -0.04),
        0.48,
        0.98,
      ),
    },
  ];
}
