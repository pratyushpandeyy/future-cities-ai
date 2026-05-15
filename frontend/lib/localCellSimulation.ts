export type UrbanDensity = "Low" | "Medium" | "High";
export type SurfaceType =
  | "concrete-heavy"
  | "mixed-use"
  | "green-buffered"
  | "coastal";

export interface LocalUrbanCellData {
  cellId: string;
  latitude: number;
  longitude: number;
  urbanDensity: UrbanDensity;
  surfaceType: SurfaceType;
  heatIslandModifier: number;
  floodExposureModifier: number;
  heatRiskAdjustment: number;
  floodRiskAdjustment: number;
  livabilityAdjustment: number;
  outdoorComfortAdjustment: number;
  greenCoverAdjustment: number;
  explanation: string;
}

function hashCoordinate(latitude: number, longitude: number) {
  const latSeed = Math.round((latitude + 90) * 1000);
  const lngSeed = Math.round((longitude + 180) * 1000);

  return Math.abs(latSeed * 31 + lngSeed * 17);
}

function createCellId(latitude: number, longitude: number) {
  const latBand = Math.abs(Math.round(latitude * 100))
    .toString()
    .padStart(4, "0");
  const lngBand = Math.abs(Math.round(longitude * 100))
    .toString()
    .padStart(5, "0");

  return `UC-${latBand}-${lngBand}`;
}

function getExplanation(surfaceType: SurfaceType, urbanDensity: UrbanDensity) {
  if (surfaceType === "green-buffered") {
    return "Why this cell differs: tree cover and softer surfaces create more shade and cooling, so the area feels more comfortable than nearby hardscape zones.";
  }

  if (surfaceType === "coastal") {
    return "Why this cell differs: proximity to water can moderate heat, but low-lying edges face stronger flood and humidity stress during future climate extremes.";
  }

  if (surfaceType === "concrete-heavy" || urbanDensity === "High") {
    return "Why this cell differs: dense buildings and hard surfaces store heat, reduce nighttime cooling, and make outdoor movement feel more stressful.";
  }

  return "Why this cell differs: mixed land use keeps the cell balanced, with moderate heat storage, usable street activity, and no single dominant climate pressure.";
}

export function simulateLocalUrbanCell(
  latitude: number,
  longitude: number,
): LocalUrbanCellData {
  const roundedLatitude = Number(latitude.toFixed(4));
  const roundedLongitude = Number(longitude.toFixed(4));
  const hash = hashCoordinate(roundedLatitude, roundedLongitude);
  const densityOptions: UrbanDensity[] = ["Low", "Medium", "High"];
  const surfaceOptions: SurfaceType[] = [
    "concrete-heavy",
    "mixed-use",
    "green-buffered",
    "coastal",
  ];
  const urbanDensity = densityOptions[hash % densityOptions.length];
  const surfaceType =
    surfaceOptions[
      (hash + Math.abs(Math.round(latitude))) % surfaceOptions.length
    ];
  const densityHeat =
    urbanDensity === "High" ? 0.9 : urbanDensity === "Medium" ? 0.45 : 0.1;
  const surfaceHeat =
    surfaceType === "concrete-heavy"
      ? 1
      : surfaceType === "green-buffered"
        ? -0.45
        : surfaceType === "coastal"
          ? 0.15
          : 0.35;
  const surfaceFlood =
    surfaceType === "coastal"
      ? 1.25
      : surfaceType === "concrete-heavy"
        ? 0.55
        : surfaceType === "green-buffered"
          ? -0.25
          : 0.2;
  const heatIslandModifier = Number(
    Math.max(
      0.1,
      0.6 + densityHeat + surfaceHeat + (hash % 5) * 0.08,
    ).toFixed(1),
  );
  const floodExposureModifier = Number(
    Math.max(0.1, 0.45 + surfaceFlood + (hash % 4) * 0.12).toFixed(
      1,
    ),
  );

  return {
    cellId: createCellId(roundedLatitude, roundedLongitude),
    latitude: roundedLatitude,
    longitude: roundedLongitude,
    urbanDensity,
    surfaceType,
    heatIslandModifier,
    floodExposureModifier,
    heatRiskAdjustment:
      (urbanDensity === "High" ? 12 : urbanDensity === "Medium" ? 5 : 0) +
      (surfaceType === "concrete-heavy"
        ? 14
        : surfaceType === "green-buffered"
          ? -10
          : 2),
    floodRiskAdjustment:
      surfaceType === "coastal"
        ? 18
        : surfaceType === "concrete-heavy"
          ? 7
          : surfaceType === "green-buffered"
            ? -6
            : 2,
    livabilityAdjustment:
      (urbanDensity === "High" ? -5 : urbanDensity === "Low" ? 2 : 0) +
      (surfaceType === "green-buffered"
        ? 6
        : surfaceType === "concrete-heavy"
          ? -6
          : surfaceType === "coastal"
            ? -3
            : 0),
    outdoorComfortAdjustment:
      (surfaceType === "green-buffered"
        ? 10
        : surfaceType === "concrete-heavy"
          ? -12
          : surfaceType === "coastal"
            ? -4
            : 0) +
      (urbanDensity === "High" ? -6 : urbanDensity === "Low" ? 3 : 0),
    greenCoverAdjustment:
      surfaceType === "green-buffered"
        ? 12
        : surfaceType === "concrete-heavy"
          ? -8
          : surfaceType === "coastal"
            ? 2
            : 0,
    explanation: getExplanation(surfaceType, urbanDensity),
  };
}
