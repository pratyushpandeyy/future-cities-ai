"use client";

import Link from "next/link";
import { useCallback, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Layers } from "lucide-react";
import type { AreaRiskData } from "@/components/AreaRiskInspector";
import ComparisonScenarioControls, {
  type ComparisonScenarioConfig,
} from "@/components/ComparisonScenarioControls";
import IntelligencePanel from "@/components/IntelligencePanel";
import LayerToggle from "@/components/LayerToggle";
import MapboxView, { type SyncedMapView } from "@/components/MapboxView";
import type { MapCityNodeData } from "@/components/MapCityNode";
import type { RegionalMappingData } from "@/components/regionalTypes";
import SearchScenarioBar, {
  type ScenarioMode,
  type SearchResult,
} from "@/components/SearchScenarioBar";

const cityNodes: MapCityNodeData[] = [
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

const layerNames = [
  "Heat Risk",
  "Flood Risk",
  "Air Quality",
  "Green Cover",
  "Water Stress",
  "Culture/Sports Lens",
] as const;

const years = [2025, 2030, 2040, 2050];
const predictedWarmingByYear: Record<number, number> = {
  2025: 1.4,
  2030: 1.7,
  2040: 2.1,
  2050: 2.7,
};

type LayerState = Record<(typeof layerNames)[number], boolean>;
type InspectedScenario = "A" | "B";

const initialLayers = layerNames.reduce<LayerState>(
  (layers, layerName, index) => ({
    ...layers,
    [layerName]: index < 3,
  }),
  {} as LayerState,
);

const scenarioAInitial: ComparisonScenarioConfig = {
  year: 2030,
  warming: 1.7,
  overlays: { ...initialLayers },
};

const scenarioBInitial: ComparisonScenarioConfig = {
  year: 2050,
  warming: 2.7,
  overlays: {
    ...initialLayers,
    "Green Cover": true,
    "Culture/Sports Lens": true,
  },
};

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

function createAreaRisk(x: number, y: number): AreaRiskData {
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

function createScenarioCity(
  city: MapCityNodeData,
  warming: number,
): MapCityNodeData {
  const heatPressure = Math.max(0, warming - 1);
  const livabilityScore = Math.max(
    42,
    Math.round(city.livabilityScore - heatPressure * 6),
  );
  const heatScore =
    city.heatRisk === "High" ? 78 : city.heatRisk === "Rising" ? 66 : 48;

  return {
    ...city,
    livabilityScore,
    heatRisk: getRiskLabel(heatScore + heatPressure * 14),
  };
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

function getOutdoorComfort(warming: number) {
  const comfortScore = Math.max(18, Math.round(86 - warming * 15));

  return getComfortLabel(comfortScore);
}

function createComparisonMetrics(
  city: MapCityNodeData,
  scenarioA: ComparisonScenarioConfig,
  scenarioB: ComparisonScenarioConfig,
) {
  const cityA = createScenarioCity(city, scenarioA.warming);
  const cityB = createScenarioCity(city, scenarioB.warming);
  const heatIncrease = Math.max(
    0,
    Math.round((scenarioB.warming - scenarioA.warming) * 16),
  );
  const livabilityDecline = Math.max(
    0,
    cityA.livabilityScore - cityB.livabilityScore,
  );
  const comfortA = Math.max(18, Math.round(86 - scenarioA.warming * 15));
  const comfortB = Math.max(18, Math.round(86 - scenarioB.warming * 15));
  const outdoorComfortChange = Math.max(0, comfortA - comfortB);

  return {
    heatIncrease,
    livabilityDecline,
    outdoorComfortChange,
    scientificMetric: `Wet bulb anomaly +${Math.max(
      0,
      scenarioB.warming - scenarioA.warming + 0.6,
    ).toFixed(1)}C`,
    humanTranslation:
      "Summer nighttime cooling becomes significantly weaker, increasing discomfort during heatwaves.",
  };
}

export default function MapPage() {
  const [selectedCity, setSelectedCity] = useState<MapCityNodeData>(
    cityNodes[0],
  );
  const [selectedYear, setSelectedYear] = useState(2030);
  const [layers, setLayers] = useState<LayerState>(initialLayers);
  const [areaRisk, setAreaRisk] = useState<AreaRiskData | null>(null);
  const [scenarioMode, setScenarioMode] = useState<ScenarioMode>("predicted");
  const [manualWarming, setManualWarming] = useState(2.1);
  const [focusedCityName, setFocusedCityName] = useState(selectedCity.name);
  const [focusRequestId, setFocusRequestId] = useState(0);
  const [comparisonMode, setComparisonMode] = useState(false);
  const [scientificView, setScientificView] = useState(false);
  const [scenarioA, setScenarioA] =
    useState<ComparisonScenarioConfig>(scenarioAInitial);
  const [scenarioB, setScenarioB] =
    useState<ComparisonScenarioConfig>(scenarioBInitial);
  const [syncedView, setSyncedView] = useState<SyncedMapView | null>(null);
  const [lastMapView, setLastMapView] = useState<SyncedMapView | null>(null);
  const [regionalMapping, setRegionalMapping] =
    useState<RegionalMappingData | null>(null);
  const [inspectedScenario, setInspectedScenario] =
    useState<InspectedScenario>("B");

  const activeLayers = layerNames.filter((layerName) => layers[layerName]);
  const predictedWarming = predictedWarmingByYear[selectedYear];
  const activeWarming =
    scenarioMode === "predicted" ? predictedWarming : manualWarming;
  const scenarioCity = createScenarioCity(selectedCity, activeWarming);
  const outdoorComfort = getOutdoorComfort(activeWarming);
  const inspectedScenarioConfig =
    inspectedScenario === "A" ? scenarioA : scenarioB;
  const panelCity = comparisonMode
    ? createScenarioCity(selectedCity, inspectedScenarioConfig.warming)
    : scenarioCity;
  const panelYear = comparisonMode ? inspectedScenarioConfig.year : selectedYear;
  const panelWarming = comparisonMode
    ? inspectedScenarioConfig.warming
    : activeWarming;
  const panelOutdoorComfort = comparisonMode
    ? getOutdoorComfort(inspectedScenarioConfig.warming)
    : outdoorComfort;
  const comparisonMetrics = createComparisonMetrics(
    selectedCity,
    scenarioA,
    scenarioB,
  );

  function toggleLayer(layerName: keyof LayerState) {
    setLayers((currentLayers) => ({
      ...currentLayers,
      [layerName]: !currentLayers[layerName],
    }));
  }

  const inspectArea = useCallback((position: { x: number; y: number }) => {
    setAreaRisk(
      createAreaRisk(
        Math.min(100, Math.max(0, position.x)),
        Math.min(100, Math.max(0, position.y)),
      ),
    );
  }, []);

  const selectCity = useCallback((city: MapCityNodeData) => {
    setSelectedCity(city);
    setRegionalMapping(null);
  }, []);

  const syncComparisonView = useCallback((view: SyncedMapView) => {
    setSyncedView(view);
    setLastMapView(view);
  }, []);

  const searchRegion = useCallback((query: string): SearchResult => {
    const normalizedQuery = query.trim().toLowerCase();
    const matchedCity = cityNodes.find(
      (city) => city.name.toLowerCase() === normalizedQuery,
    );

    if (matchedCity) {
      setSelectedCity(matchedCity);
      setRegionalMapping(null);
      setFocusedCityName(matchedCity.name);
      setFocusRequestId((currentId) => currentId + 1);
      return "known";
    }

    const fallbackQuery = query.trim() || "Unmapped urban cell";
    const center = syncedView?.center ?? lastMapView?.center ?? [31, 30];
    const mapping = createRegionalMapping(fallbackQuery, center);

    setRegionalMapping(mapping);
    setSelectedCity(createRegionalCity(mapping));
    setFocusedCityName("");

    return "regional";
  }, [lastMapView, syncedView]);

  return (
    <main className="relative min-h-screen overflow-x-hidden bg-black text-white">
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[radial-gradient(circle_at_25%_18%,rgba(56,189,248,0.22),transparent_32%),radial-gradient(circle_at_78%_74%,rgba(168,85,247,0.18),transparent_34%),linear-gradient(180deg,#020617_0%,#030712_50%,#000_100%)]"
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.055)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.055)_1px,transparent_1px)] [background-size:64px_64px] opacity-25"
      />

      <section className="relative z-10 flex min-h-screen flex-col gap-4 p-4 lg:grid lg:grid-cols-[280px_1fr_360px] lg:grid-rows-[1fr_auto] lg:p-6">
        <motion.header
          initial={{ opacity: 0, y: -14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="rounded-lg border border-white/10 bg-black/45 p-4 backdrop-blur-2xl lg:col-start-1 lg:row-span-2 lg:row-start-1"
        >
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-white/55 transition hover:text-white"
          >
            <ArrowLeft size={16} strokeWidth={1.8} />
            Landing
          </Link>

          <div className="mt-6 flex items-center gap-3">
            <div className="rounded-lg border border-cyan-100/20 bg-cyan-100/10 p-3 text-cyan-100">
              <Layers size={20} strokeWidth={1.8} />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-cyan-100/45">
                Future Cities AI
              </p>
              <h1 className="mt-1 text-2xl font-semibold">Map Prototype</h1>
            </div>
          </div>

          <div className="mt-7 space-y-3">
            {layerNames.map((layerName) => (
              <LayerToggle
                key={layerName}
                label={layerName}
                enabled={layers[layerName]}
                onToggle={() => toggleLayer(layerName)}
              />
            ))}
          </div>

          <div className="mt-6 rounded-lg border border-white/10 bg-white/[0.045] p-4">
            <p className="text-xs uppercase tracking-[0.26em] text-white/35">
              Active overlays
            </p>
            <p className="mt-3 text-sm leading-6 text-white/60">
              {activeLayers.length > 0
                ? activeLayers.join(" / ")
                : "No layers active"}
            </p>
          </div>
        </motion.header>

        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.75, ease: [0.22, 1, 0.36, 1] }}
          className="relative min-h-[520px] overflow-hidden rounded-lg border border-white/10 bg-slate-950/55 shadow-[0_30px_110px_rgba(0,0,0,0.5)] backdrop-blur-xl lg:col-start-2 lg:row-span-2 lg:h-[calc(100vh-3rem)] lg:min-h-0"
        >
          <div className="absolute bottom-5 left-5 z-30 rounded-lg border border-white/10 bg-black/45 px-4 py-3 backdrop-blur-2xl">
            <p className="text-sm text-white/75">Live Mapbox viewport</p>
            <p className="mt-1 text-xs text-white/40">
              Dark map / dummy intelligence layer
            </p>
          </div>

          <SearchScenarioBar
            mode={scenarioMode}
            warming={manualWarming}
            predictedWarming={predictedWarming}
            selectedYear={selectedYear}
            comparisonMode={comparisonMode}
            scientificView={scientificView}
            onModeChange={setScenarioMode}
            onWarmingChange={setManualWarming}
            onComparisonModeChange={setComparisonMode}
            onScientificViewChange={setScientificView}
            onSearch={searchRegion}
          />

          {comparisonMode ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid h-full grid-cols-1 gap-2 pt-40 md:grid-cols-2 md:pt-32 xl:pt-28"
            >
              <div className="relative min-h-[360px] overflow-hidden border-t border-white/10 md:border-r md:border-t-0">
                <div className="absolute left-3 top-48 z-40 rounded-full border border-cyan-100/25 bg-black/70 px-3 py-1.5 text-xs font-medium uppercase tracking-[0.22em] text-cyan-50 backdrop-blur-xl md:top-44 xl:top-40">
                  Scenario A
                </div>
                <div className="absolute left-3 right-3 top-3 z-30">
                  <ComparisonScenarioControls
                    label="Scenario A"
                    scenario={scenarioA}
                    years={years}
                    layerNames={layerNames}
                    onChange={setScenarioA}
                  />
                </div>
                <MapboxView
                  mapId="scenario-a"
                  cities={cityNodes}
                  selectedCityName={selectedCity.name}
                  focusedCityName={focusedCityName}
                  focusRequestId={focusRequestId}
                  areaRisk={areaRisk}
                  regionalMapping={regionalMapping}
                  syncedView={syncedView}
                  onViewChange={syncComparisonView}
                  onSelectCity={selectCity}
                  onInspectArea={inspectArea}
                />
              </div>
              <div className="relative min-h-[360px] overflow-hidden border-t border-white/10 md:border-t-0">
                <div className="absolute left-3 top-48 z-40 rounded-full border border-fuchsia-100/25 bg-black/70 px-3 py-1.5 text-xs font-medium uppercase tracking-[0.22em] text-fuchsia-50 backdrop-blur-xl md:top-44 xl:top-40">
                  Scenario B
                </div>
                <div className="absolute left-3 right-3 top-3 z-30">
                  <ComparisonScenarioControls
                    label="Scenario B"
                    scenario={scenarioB}
                    years={years}
                    layerNames={layerNames}
                    onChange={setScenarioB}
                  />
                </div>
                <MapboxView
                  mapId="scenario-b"
                  cities={cityNodes}
                  selectedCityName={selectedCity.name}
                  focusedCityName={focusedCityName}
                  focusRequestId={focusRequestId}
                  areaRisk={areaRisk}
                  regionalMapping={regionalMapping}
                  syncedView={syncedView}
                  onViewChange={syncComparisonView}
                  onSelectCity={selectCity}
                  onInspectArea={inspectArea}
                />
              </div>
            </motion.div>
          ) : (
            <MapboxView
              cities={cityNodes}
              selectedCityName={selectedCity.name}
              focusedCityName={focusedCityName}
              focusRequestId={focusRequestId}
              areaRisk={areaRisk}
              regionalMapping={regionalMapping}
              onViewChange={setLastMapView}
              onSelectCity={selectCity}
              onInspectArea={inspectArea}
            />
          )}

          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-x-0 bottom-0 h-36 bg-gradient-to-t from-black/70 to-transparent"
          />
        </motion.div>

        <div className="lg:col-start-3 lg:row-start-1">
          <IntelligencePanel
            city={panelCity}
            year={panelYear}
            areaRisk={areaRisk}
            scenarioMode={scenarioMode}
            warming={panelWarming}
            outdoorComfort={panelOutdoorComfort}
            comparisonMode={comparisonMode}
            scientificView={scientificView}
            inspectedScenario={inspectedScenario}
            onInspectedScenarioChange={setInspectedScenario}
            comparisonMetrics={comparisonMetrics}
            regionalMapping={regionalMapping}
          />
        </div>

        <motion.div
          initial={{ opacity: 0, y: 18 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.1 }}
          className="rounded-lg border border-white/10 bg-black/50 p-4 backdrop-blur-2xl lg:col-start-3 lg:row-start-2"
        >
          <div className="flex items-center justify-between gap-4">
            <p className="text-xs uppercase tracking-[0.3em] text-white/40">
              Timeline
            </p>
            <p className="text-lg font-semibold text-white">{selectedYear}</p>
          </div>

          <div className="mt-5 grid grid-cols-4 gap-2">
            {years.map((year) => (
              <button
                key={year}
                type="button"
                onClick={() => setSelectedYear(year)}
                className={`rounded-lg border px-3 py-2 text-sm transition ${
                  selectedYear === year
                    ? "border-cyan-100/50 bg-cyan-100/15 text-white shadow-[0_0_26px_rgba(103,232,249,0.2)]"
                    : "border-white/10 bg-white/[0.04] text-white/50 hover:text-white"
                }`}
              >
                {year}
              </button>
            ))}
          </div>

          <input
            aria-label="Projection year"
            type="range"
            min={0}
            max={years.length - 1}
            step={1}
            value={years.indexOf(selectedYear)}
            onChange={(event) =>
              setSelectedYear(years[Number(event.currentTarget.value)])
            }
            className="mt-5 h-2 w-full accent-cyan-200"
          />
        </motion.div>
      </section>
    </main>
  );
}
