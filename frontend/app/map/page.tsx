"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Layers, Pause, Play, SkipBack, SkipForward, X } from "lucide-react";
import type { AreaRiskData } from "@/components/AreaRiskInspector";
import ComparisonScenarioControls, {
  type ComparisonScenarioConfig,
} from "@/components/ComparisonScenarioControls";
import IntelligencePanel, { type PanelTab } from "@/components/IntelligencePanel";
import LayerToggle from "@/components/LayerToggle";
import MapboxView, { type SyncedMapView } from "@/components/MapboxView";
import type { MapCityNodeData } from "@/components/MapCityNode";
import type { RegionalMappingData } from "@/components/regionalTypes";
import SearchScenarioBar, {
  type ScenarioMode,
  type SearchResult,
} from "@/components/SearchScenarioBar";
import {
  generateClimateOverlays,
  type Season,
} from "@/lib/climateOverlaySimulation";
import {
  compareScenarios,
  getLocalAreaRisk,
  getOutdoorComfort,
  getScenarioScore,
  searchLocation,
} from "@/lib/api/mockClient";
import {
  climateLayerNames,
  knownCityNodes,
  predictedWarmingByYear,
  scenarioYears,
} from "@/lib/api/mockData";
import {
  simulateLocalUrbanCell,
  type LocalUrbanCellData,
} from "@/lib/localCellSimulation";

const cityNodes = knownCityNodes;
const layerNames = climateLayerNames;
const years = scenarioYears;

type LayerState = Record<(typeof layerNames)[number], boolean>;
type InspectedScenario = "A" | "B";

function createLayerPreset(enabledLayers: (typeof layerNames)[number][]) {
  return layerNames.reduce<LayerState>(
    (layers, layerName) => ({
      ...layers,
      [layerName]: enabledLayers.includes(layerName),
    }),
    {} as LayerState,
  );
}

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
  season: "Summer",
  overlays: { ...initialLayers },
};

const scenarioBInitial: ComparisonScenarioConfig = {
  year: 2050,
  warming: 2.7,
  season: "Summer",
  overlays: {
    ...initialLayers,
    "Green Cover": true,
    "Livability Stress": true,
    "Culture/Sports Lens": true,
  },
};

interface DemoStep {
  title: string;
  cityName: string;
  description: string;
  comparisonMode: boolean;
  targetTab: PanelTab;
  inspectedScenario?: InspectedScenario;
  year: number;
  warming: number;
  season: Season;
  layers: LayerState;
  scenarioA?: ComparisonScenarioConfig;
  scenarioB?: ComparisonScenarioConfig;
}

const demoSteps: DemoStep[] = [
  {
    title: "Mumbai heat risk 2030",
    cityName: "Mumbai",
    description:
      "Coastal density and limited cooling cover push heat exposure higher across the mapped Maharashtra corridor.",
    comparisonMode: false,
    targetTab: "Overview",
    year: 2030,
    warming: 1.7,
    season: "Summer",
    layers: createLayerPreset(["Heat Risk"]),
  },
  {
    title: "Istanbul comparison 2030 vs 2050",
    cityName: "Istanbul",
    description:
      "The split view contrasts a near-term Bosphorus climate profile with a hotter mid-century Marmara scenario.",
    comparisonMode: true,
    targetTab: "Comparison",
    inspectedScenario: "B",
    year: 2030,
    warming: 1.7,
    season: "Summer",
    layers: createLayerPreset(["Heat Risk", "Livability Stress"]),
    scenarioA: {
      year: 2030,
      warming: 1.7,
      season: "Summer",
      overlays: createLayerPreset(["Heat Risk"]),
    },
    scenarioB: {
      year: 2050,
      warming: 2.7,
      season: "Summer",
      overlays: createLayerPreset(["Heat Risk", "Livability Stress"]),
    },
  },
  {
    title: "Bangalore monsoon flood risk",
    cityName: "Bangalore",
    description:
      "Monsoon mode shifts attention to lake systems, flood exposure, and commute reliability around dense growth zones.",
    comparisonMode: false,
    targetTab: "Impact",
    year: 2040,
    warming: 2.1,
    season: "Monsoon",
    layers: createLayerPreset(["Flood Risk", "Water Stress"]),
  },
  {
    title: "Manchester outdoor comfort",
    cityName: "Manchester",
    description:
      "Outdoor comfort mode highlights cooler streets, green corridors, and culture districts under a softer warming path.",
    comparisonMode: false,
    targetTab: "Regional Mapping",
    year: 2050,
    warming: 2.7,
    season: "Winter",
    layers: createLayerPreset(["Outdoor Comfort", "Green Cover"]),
  },
];

export default function MapPage() {
  const [selectedCity, setSelectedCity] = useState<MapCityNodeData>(
    cityNodes[0],
  );
  const [selectedYear, setSelectedYear] = useState(2030);
  const [layers, setLayers] = useState<LayerState>(initialLayers);
  const [areaRisk, setAreaRisk] = useState<AreaRiskData | null>(null);
  const [scenarioMode, setScenarioMode] = useState<ScenarioMode>("predicted");
  const [manualWarming, setManualWarming] = useState(2.1);
  const [selectedSeason, setSelectedSeason] = useState<Season>("Summer");
  const [climateOverlayEnabled, setClimateOverlayEnabled] = useState(false);
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
  const [localUrbanCell, setLocalUrbanCell] =
    useState<LocalUrbanCellData | null>(null);
  const [inspectedScenario, setInspectedScenario] =
    useState<InspectedScenario>("B");
  const [activePanelTab, setActivePanelTab] = useState<PanelTab>("Overview");
  const [demoActive, setDemoActive] = useState(false);
  const [demoIndex, setDemoIndex] = useState(0);
  const [demoPaused, setDemoPaused] = useState(false);

  const activeLayers = layerNames.filter((layerName) => layers[layerName]);
  const currentDemoStep = demoActive ? demoSteps[demoIndex] : null;
  const predictedWarming = predictedWarmingByYear[selectedYear];
  const activeWarming =
    scenarioMode === "predicted" ? predictedWarming : manualWarming;
  const scenarioScore = getScenarioScore({
    city: selectedCity,
    warming: activeWarming,
    localUrbanCell,
  });
  const scenarioCity = scenarioScore.city;
  const outdoorComfort = scenarioScore.outdoorComfort;
  const inspectedScenarioConfig =
    inspectedScenario === "A" ? scenarioA : scenarioB;
  const inspectedScenarioScore = getScenarioScore({
    city: selectedCity,
    warming: inspectedScenarioConfig.warming,
    localUrbanCell,
  });
  const panelCity = comparisonMode ? inspectedScenarioScore.city : scenarioCity;
  const panelYear = comparisonMode ? inspectedScenarioConfig.year : selectedYear;
  const panelWarming = comparisonMode
    ? inspectedScenarioConfig.warming
    : activeWarming;
  const panelOutdoorComfort = comparisonMode
    ? inspectedScenarioScore.outdoorComfort
    : outdoorComfort;
  const panelActiveOverlays = comparisonMode
    ? layerNames.filter((layerName) => inspectedScenarioConfig.overlays[layerName])
    : activeLayers;
  const comparisonMetrics = compareScenarios({
    city: selectedCity,
    scenarioA,
    scenarioB,
    localUrbanCell,
  });
  const scenarioAScore = getScenarioScore({
    city: selectedCity,
    warming: scenarioA.warming,
    localUrbanCell,
  });
  const scenarioBScore = getScenarioScore({
    city: selectedCity,
    warming: scenarioB.warming,
    localUrbanCell,
  });
  const scenarioASnapshot = {
    label: "Scenario A",
    year: scenarioA.year,
    warming: scenarioA.warming,
    heatRisk: scenarioAScore.city.heatRisk,
    floodRisk: scenarioAScore.city.floodRisk,
    greenCover: scenarioAScore.city.greenCover,
    livabilityScore: scenarioAScore.city.livabilityScore,
    outdoorComfort: scenarioAScore.outdoorComfort,
  };
  const scenarioBSnapshot = {
    label: "Scenario B",
    year: scenarioB.year,
    warming: scenarioB.warming,
    heatRisk: scenarioBScore.city.heatRisk,
    floodRisk: scenarioBScore.city.floodRisk,
    greenCover: scenarioBScore.city.greenCover,
    livabilityScore: scenarioBScore.city.livabilityScore,
    outdoorComfort: scenarioBScore.outdoorComfort,
  };
  const singleClimateOverlays = useMemo(
    () =>
      climateOverlayEnabled
        ? generateClimateOverlays({
            year: selectedYear,
            warming: activeWarming,
            season: selectedSeason,
            enabledLayers: layers,
            localUrbanCell,
          })
        : [],
    [
      activeWarming,
      climateOverlayEnabled,
      layers,
      localUrbanCell,
      selectedSeason,
      selectedYear,
    ],
  );
  const scenarioAClimateOverlays = useMemo(
    () =>
      climateOverlayEnabled
        ? generateClimateOverlays({
            year: scenarioA.year,
            warming: scenarioA.warming,
            season: scenarioA.season,
            enabledLayers: scenarioA.overlays,
            localUrbanCell,
          })
        : [],
    [climateOverlayEnabled, localUrbanCell, scenarioA],
  );
  const scenarioBClimateOverlays = useMemo(
    () =>
      climateOverlayEnabled
        ? generateClimateOverlays({
            year: scenarioB.year,
            warming: scenarioB.warming,
            season: scenarioB.season,
            enabledLayers: scenarioB.overlays,
            localUrbanCell,
          })
        : [],
    [climateOverlayEnabled, localUrbanCell, scenarioB],
  );

  useEffect(() => {
    if (!comparisonMode && activePanelTab === "Comparison") {
      setActivePanelTab("Overview");
    }
  }, [activePanelTab, comparisonMode]);

  useEffect(() => {
    if (!currentDemoStep) {
      return;
    }

    const demoCity =
      cityNodes.find((city) => city.name === currentDemoStep.cityName) ??
      cityNodes[0];
    const demoSearch = searchLocation({
      query: demoCity.name,
      fallbackCenter: [demoCity.longitude, demoCity.latitude],
    });

    setSelectedCity(demoSearch.city);
    setRegionalMapping(demoSearch.regionalMapping);
    setFocusedCityName(demoCity.name);
    setFocusRequestId((currentId) => currentId + 1);
    setClimateOverlayEnabled(true);
    setLayers(currentDemoStep.layers);
    setSelectedYear(currentDemoStep.year);
    setManualWarming(currentDemoStep.warming);
    setScenarioMode("manual");
    setSelectedSeason(currentDemoStep.season);
    setComparisonMode(currentDemoStep.comparisonMode);
    setActivePanelTab(currentDemoStep.targetTab);
    setInspectedScenario(currentDemoStep.inspectedScenario ?? "B");
    setAreaRisk(null);
    setLocalUrbanCell(null);

    if (currentDemoStep.scenarioA) {
      setScenarioA(currentDemoStep.scenarioA);
    }

    if (currentDemoStep.scenarioB) {
      setScenarioB(currentDemoStep.scenarioB);
    }
  }, [currentDemoStep]);

  useEffect(() => {
    if (!demoActive || demoPaused || demoIndex >= demoSteps.length - 1) {
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setDemoIndex((currentIndex) =>
        Math.min(currentIndex + 1, demoSteps.length - 1),
      );
    }, 6500);

    return () => window.clearTimeout(timeoutId);
  }, [demoActive, demoIndex, demoPaused]);

  function toggleLayer(layerName: keyof LayerState) {
    setLayers((currentLayers) => ({
      ...currentLayers,
      [layerName]: !currentLayers[layerName],
    }));
  }

  function updateComparisonMode(enabled: boolean) {
    setComparisonMode(enabled);

    if (!enabled) {
      setActivePanelTab("Overview");
    }
  }

  function startDemoTour() {
    setDemoIndex(0);
    setDemoPaused(false);
    setDemoActive(true);
  }

  function exitDemoTour() {
    setDemoActive(false);
    setDemoPaused(false);
    setActivePanelTab("Overview");
  }

  function showNextDemoStep() {
    setDemoIndex((currentIndex) =>
      Math.min(currentIndex + 1, demoSteps.length - 1),
    );
  }

  function showPreviousDemoStep() {
    setDemoIndex((currentIndex) => Math.max(currentIndex - 1, 0));
  }

  const inspectArea = useCallback((position: {
    x: number;
    y: number;
    latitude: number;
    longitude: number;
  }) => {
    setAreaRisk(
      getLocalAreaRisk(
        Math.min(100, Math.max(0, position.x)),
        Math.min(100, Math.max(0, position.y)),
      ),
    );
    setLocalUrbanCell(
      simulateLocalUrbanCell(position.latitude, position.longitude),
    );
  }, []);

  const selectCity = useCallback((city: MapCityNodeData) => {
    const result = searchLocation({
      query: city.name,
      fallbackCenter: [city.longitude, city.latitude],
    });

    setSelectedCity(result.city);
    setRegionalMapping(result.regionalMapping);
  }, []);

  const syncComparisonView = useCallback((view: SyncedMapView) => {
    setSyncedView(view);
    setLastMapView(view);
  }, []);

  const searchRegion = useCallback((query: string): SearchResult => {
    const center = syncedView?.center ?? lastMapView?.center ?? [31, 30];
    const result = searchLocation({
      query,
      fallbackCenter: center,
    });

    setRegionalMapping(result.regionalMapping);
    setSelectedCity(result.city);
    setFocusedCityName(result.kind === "known" ? result.city.name : "");
    setFocusRequestId((currentId) => currentId + 1);

    return result.kind;
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
            <LayerToggle
              label="Climate Overlay"
              enabled={climateOverlayEnabled}
              onToggle={() =>
                setClimateOverlayEnabled((currentValue) => !currentValue)
              }
            />
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
              {climateOverlayEnabled
                ? !regionalMapping
                  ? "Search a place to view regional climate overlay."
                  : activeLayers.length > 0
                    ? activeLayers.join(" / ")
                    : "Region overlay on / no layers active"
                : "Climate overlay off"}
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
            season={selectedSeason}
            comparisonMode={comparisonMode}
            scientificView={scientificView}
            onModeChange={setScenarioMode}
            onWarmingChange={setManualWarming}
            onSeasonChange={setSelectedSeason}
            onComparisonModeChange={updateComparisonMode}
            onScientificViewChange={setScientificView}
            onDemoTourStart={startDemoTour}
            onSearch={searchRegion}
          />

          {currentDemoStep ? (
            <motion.div
              key={currentDemoStep.title}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 16 }}
              className="absolute bottom-20 left-1/2 z-50 w-[min(520px,calc(100%-2rem))] -translate-x-1/2 rounded-lg border border-cyan-100/20 bg-black/72 p-4 shadow-[0_24px_80px_rgba(0,0,0,0.55)] backdrop-blur-2xl"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs font-medium uppercase tracking-[0.26em] text-cyan-100/60">
                    Demo Tour {demoIndex + 1}/{demoSteps.length}
                  </p>
                  <h3 className="mt-2 text-lg font-semibold text-white">
                    {currentDemoStep.title}
                  </h3>
                </div>
                <button
                  type="button"
                  onClick={exitDemoTour}
                  className="rounded-full border border-white/10 bg-white/[0.04] p-2 text-white/55 transition hover:text-white"
                  aria-label="Exit demo tour"
                >
                  <X size={15} strokeWidth={1.8} />
                </button>
              </div>
              <p className="mt-3 text-sm leading-6 text-white/60">
                {currentDemoStep.description}
              </p>
              <div className="mt-4 flex items-center justify-between gap-3">
                <button
                  type="button"
                  onClick={showPreviousDemoStep}
                  disabled={demoIndex === 0}
                  className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 text-xs font-medium uppercase tracking-[0.16em] text-white/60 transition hover:text-white disabled:cursor-not-allowed disabled:opacity-45"
                >
                  <SkipBack size={14} strokeWidth={1.8} />
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => setDemoPaused((currentValue) => !currentValue)}
                  className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.05] px-3 py-2 text-xs font-medium uppercase tracking-[0.16em] text-white/60 transition hover:text-white"
                >
                  {demoPaused ? (
                    <Play size={14} strokeWidth={1.8} />
                  ) : (
                    <Pause size={14} strokeWidth={1.8} />
                  )}
                  {demoPaused ? "Resume" : "Pause"}
                </button>
                <button
                  type="button"
                  onClick={showNextDemoStep}
                  disabled={demoIndex >= demoSteps.length - 1}
                  className="inline-flex items-center gap-2 rounded-full border border-cyan-100/25 bg-cyan-100/10 px-3 py-2 text-xs font-medium uppercase tracking-[0.16em] text-cyan-50 transition hover:bg-cyan-100/15 disabled:cursor-not-allowed disabled:opacity-45"
                >
                  Next
                  <SkipForward size={14} strokeWidth={1.8} />
                </button>
              </div>
            </motion.div>
          ) : null}

          {comparisonMode ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="grid h-full grid-cols-1 gap-2 pt-48 md:grid-cols-2 md:pt-40 xl:pt-36"
            >
              <div className="relative min-h-[360px] overflow-hidden border-t border-white/10 md:border-r md:border-t-0">
                <div className="absolute left-3 top-56 z-40 rounded-full border border-cyan-100/25 bg-black/70 px-3 py-1.5 text-xs font-medium uppercase tracking-[0.22em] text-cyan-50 backdrop-blur-xl md:top-52 xl:top-48">
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
                  localUrbanCell={localUrbanCell}
                  climateOverlayEnabled={climateOverlayEnabled}
                  climateOverlays={scenarioAClimateOverlays}
                  syncedView={syncedView}
                  onViewChange={syncComparisonView}
                  onSelectCity={selectCity}
                  onInspectArea={inspectArea}
                />
              </div>
              <div className="relative min-h-[360px] overflow-hidden border-t border-white/10 md:border-t-0">
                <div className="absolute left-3 top-56 z-40 rounded-full border border-fuchsia-100/25 bg-black/70 px-3 py-1.5 text-xs font-medium uppercase tracking-[0.22em] text-fuchsia-50 backdrop-blur-xl md:top-52 xl:top-48">
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
                  localUrbanCell={localUrbanCell}
                  climateOverlayEnabled={climateOverlayEnabled}
                  climateOverlays={scenarioBClimateOverlays}
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
              localUrbanCell={localUrbanCell}
              climateOverlayEnabled={climateOverlayEnabled}
              climateOverlays={singleClimateOverlays}
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
            scenarioA={scenarioASnapshot}
            scenarioB={scenarioBSnapshot}
            regionalMapping={regionalMapping}
            localUrbanCell={localUrbanCell}
            activeOverlays={[...panelActiveOverlays]}
            activeTab={activePanelTab}
            onActiveTabChange={setActivePanelTab}
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
