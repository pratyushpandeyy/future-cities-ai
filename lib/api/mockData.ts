import type { MapCityNodeData } from "@/components/MapCityNode";

export const knownCityNodes: MapCityNodeData[] = [
  {
    name: "Mumbai",
    region: "Arabian Sea megacity corridor",
    longitude: 72.8777,
    latitude: 19.076,
    x: 69,
    y: 57,
    livabilityScore: 82,
    heatRisk: "High",
    floodRisk: "Elevated",
    greenCover: "14%",
    futureSummary:
      "Dense coastal districts require sharper flood buffers, cooler streets, and faster multimodal access by mid-century.",
    sportsCultureImpact:
      "Stadium precincts and film districts become high-value civic cooling zones during extreme heat windows.",
    accent: "bg-cyan-400/20",
  },
  {
    name: "Bangalore",
    region: "Deccan innovation plateau",
    longitude: 77.5946,
    latitude: 12.9716,
    x: 68,
    y: 68,
    livabilityScore: 88,
    heatRisk: "Medium",
    floodRisk: "Moderate",
    greenCover: "22%",
    futureSummary:
      "Distributed tech neighborhoods benefit from restored lake systems, shaded mobility, and mixed-use growth.",
    sportsCultureImpact:
      "Cricket, esports, and live music corridors strengthen nighttime activity around transit-linked districts.",
    accent: "bg-emerald-400/20",
  },
  {
    name: "Madrid",
    region: "Iberian civic core",
    longitude: -3.7038,
    latitude: 40.4168,
    x: 42,
    y: 39,
    livabilityScore: 91,
    heatRisk: "Rising",
    floodRisk: "Low",
    greenCover: "31%",
    futureSummary:
      "Heat-adapted plazas, tree canopies, and low-emission mobility keep central districts highly livable.",
    sportsCultureImpact:
      "Football, museums, and public squares anchor a resilient cultural economy through hotter summers.",
    accent: "bg-rose-400/20",
  },
  {
    name: "Istanbul",
    region: "Bosphorus cultural bridge",
    longitude: 28.9784,
    latitude: 41.0082,
    x: 51,
    y: 43,
    livabilityScore: 79,
    heatRisk: "Medium",
    floodRisk: "Variable",
    greenCover: "18%",
    futureSummary:
      "Waterfront adaptation and seismic-aware regeneration shape future livability across historic districts.",
    sportsCultureImpact:
      "Match-day mobility, bazaars, and waterfront venues intensify the need for crowd-aware climate planning.",
    accent: "bg-amber-300/20",
  },
  {
    name: "Manchester",
    region: "Northern UK regeneration zone",
    longitude: -2.2426,
    latitude: 53.4808,
    x: 40,
    y: 29,
    livabilityScore: 86,
    heatRisk: "Low",
    floodRisk: "Moderate",
    greenCover: "27%",
    futureSummary:
      "Canal corridors, media clusters, and retrofitted industrial zones support compact low-carbon growth.",
    sportsCultureImpact:
      "Football, music, and media venues drive visitor flows that benefit from greener streets and rain resilience.",
    accent: "bg-sky-300/20",
  },
];

export const climateLayerNames = [
  "Heat Risk",
  "Flood Risk",
  "Outdoor Comfort",
  "Air Quality",
  "Green Cover",
  "Livability Stress",
  "Water Stress",
  "Culture/Sports Lens",
] as const;

export const scenarioYears = [2025, 2030, 2040, 2050];

export const predictedWarmingByYear: Record<number, number> = {
  2025: 1.4,
  2030: 1.7,
  2040: 2.1,
  2050: 2.7,
};
