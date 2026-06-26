"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
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
  type RegionBoundaryFeatureCollection,
  type Season,
} from "@/lib/climateOverlaySimulation";
import {
  compareScenarios,
  getAIExplanation,
  getClimateCellDetail,
  getClimateTimeline,
  getCompositeRisk,
  getRecommendations,
  queryClimateAdvisor,
  type AIExplanation,
  type AdvisorResult,
  type ClimateSurfaceMetadata,
  type ClimateDataEvidence,
  type ClimateCellDetail,
  type ClimateInteractionResult,
  type ClimateTimelineResult,
  type RecommendationPreferences,
  type RecommendationResult,
  type WarmingPathway,
  getLocalAreaRisk,
  getRegionBoundary,
  getScenarioScore,
  listSavedScenarios,
  deleteSavedScenario,
  saveScenario,
  searchLocation,
  type ComparisonMetrics,
  type SavedScenario,
  type ScenarioScoreResult,
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
const playbackYearRange = { start: 2025, end: 2100 };
const playbackSpeeds = [0.5, 1, 2, 4] as const;

type LayerState = Record<(typeof layerNames)[number], boolean>;
type InspectedScenario = "A" | "B";
type PlaybackSpeed = (typeof playbackSpeeds)[number];
type LoadingState = {
  searching: boolean;
  scenario: boolean;
  explanation: boolean;
};

const initialComparisonMetrics: ComparisonMetrics = {
  heatIncrease: 0,
  livabilityDecline: 0,
  outdoorComfortChange: 0,
  scientificMetric: "Wet bulb anomaly +0.0C",
  humanTranslation:
    "Scenario comparison will update after the backend response is received.",
};

const initialAIExplanation: AIExplanation = {
  humanSummary:
    "Human impact translation will update after the backend explanation service responds.",
  commuteImpact: "Commute exposure will update with the selected scenario.",
  outdoorActivityImpact:
    "Outdoor activity impacts will update with the selected scenario.",
  nighttimeRecovery: "Nighttime recovery guidance will update with the scenario.",
  vulnerableGroupsNote:
    "Vulnerability guidance will update once climate facts are loaded.",
  confidenceNote:
    "Explanation confidence will update after backend validation.",
  explanationSource: "template",
};

function createInitialScenarioScore(city: MapCityNodeData): ScenarioScoreResult {
  return {
    city,
    outdoorComfort: "Moderate",
    wetBulbAnomaly: 0,
    climateRegionType: "continental",
    scoreBreakdown: {
      heatScore: 0,
      floodScore: 0,
      outdoorComfortScore: 0,
      airQualityScore: 0,
      greenCoverStressScore: 0,
      waterStressScore: 0,
      livabilityStressScore: 0,
      warmingPressure: 0,
      yearPressure: 0,
      seasonModifier: "Summer",
      timeOfDayModifier: "Afternoon",
    },
    dominantRiskDriver: "warming pressure",
    rasterSample: null,
    dataEvidence: null,
    summary: city.futureSummary,
  };
}

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
  const [overlayOpacity, setOverlayOpacity] = useState(0.88);
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
  const [loadingState, setLoadingState] = useState<LoadingState>({
    searching: false,
    scenario: false,
    explanation: false,
  });
  const [apiError, setApiError] = useState<string | null>(null);
  const [scenarioScore, setScenarioScore] = useState<ScenarioScoreResult>(
    createInitialScenarioScore(cityNodes[0]),
  );
  const [inspectedScenarioScore, setInspectedScenarioScore] =
    useState<ScenarioScoreResult>(createInitialScenarioScore(cityNodes[0]));
  const [scenarioAScore, setScenarioAScore] = useState<ScenarioScoreResult>(
    createInitialScenarioScore(cityNodes[0]),
  );
  const [scenarioBScore, setScenarioBScore] = useState<ScenarioScoreResult>(
    createInitialScenarioScore(cityNodes[0]),
  );
  const [comparisonMetrics, setComparisonMetrics] = useState<ComparisonMetrics>(
    initialComparisonMetrics,
  );
  const [regionBoundary, setRegionBoundary] =
    useState<RegionBoundaryFeatureCollection | null>(null);
  const [climateSurfaceMetadata, setClimateSurfaceMetadata] =
    useState<ClimateSurfaceMetadata | null>(null);
  const [selectedClimateCell, setSelectedClimateCell] =
    useState<ClimateCellDetail | null>(null);
  const [aiExplanation, setAiExplanation] =
    useState<AIExplanation>(initialAIExplanation);
  const [climateInteraction, setClimateInteraction] =
    useState<ClimateInteractionResult | null>(null);
  const [recommendationResult, setRecommendationResult] =
    useState<RecommendationResult | null>(null);
  const [recommendationLoading, setRecommendationLoading] = useState(false);
  const [advisorResult, setAdvisorResult] = useState<AdvisorResult | null>(null);
  const [advisorLoading, setAdvisorLoading] = useState(false);
  const [savedScenarios, setSavedScenarios] = useState<SavedScenario[]>([]);
  const [savingScenario, setSavingScenario] = useState(false);
  const [timelinePlaybackEnabled, setTimelinePlaybackEnabled] = useState(false);
  const [timelinePlaying, setTimelinePlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState<PlaybackSpeed>(1);
  const [warmingPathway, setWarmingPathway] =
    useState<WarmingPathway>("moderate");
  const [timelineData, setTimelineData] =
    useState<ClimateTimelineResult | null>(null);
  const timelineCacheRef = useRef<Map<string, ClimateTimelineResult>>(new Map());

  const activeLayers = layerNames.filter((layerName) => layers[layerName]);
  const currentDemoStep = demoActive ? demoSteps[demoIndex] : null;
  const predictedWarming = predictedWarmingByYear[selectedYear] ?? manualWarming;
  const activeWarming =
    scenarioMode === "predicted" ? predictedWarming : manualWarming;
  const activePlaybackLayer = activeLayers[0] ?? "Heat Risk";
  const currentTimelineSnapshot =
    timelineData?.snapshots.find((snapshot) => snapshot.year === selectedYear) ??
    null;
  const scenarioCity = scenarioScore.city;
  const outdoorComfort = scenarioScore.outdoorComfort;
  const inspectedScenarioConfig =
    inspectedScenario === "A" ? scenarioA : scenarioB;
  const panelCity = comparisonMode ? inspectedScenarioScore.city : scenarioCity;
  const panelYear = comparisonMode ? inspectedScenarioConfig.year : selectedYear;
  const panelWarming = comparisonMode
    ? inspectedScenarioConfig.warming
    : activeWarming;
  const panelOutdoorComfort = comparisonMode
    ? inspectedScenarioScore.outdoorComfort
    : outdoorComfort;
  const panelScoreBreakdown = comparisonMode
    ? inspectedScenarioScore.scoreBreakdown
    : scenarioScore.scoreBreakdown;
  const panelClimateRegionType = comparisonMode
    ? inspectedScenarioScore.climateRegionType
    : scenarioScore.climateRegionType;
  const panelDominantRiskDriver = comparisonMode
    ? inspectedScenarioScore.dominantRiskDriver
    : scenarioScore.dominantRiskDriver;
  const panelRasterSample = comparisonMode
    ? inspectedScenarioScore.rasterSample
    : scenarioScore.rasterSample;
  const panelDataEvidence: ClimateDataEvidence | null = comparisonMode
    ? inspectedScenarioScore.dataEvidence
    : scenarioScore.dataEvidence;
  const panelActiveOverlays = comparisonMode
    ? layerNames.filter((layerName) => inspectedScenarioConfig.overlays[layerName])
    : activeLayers;
  const panelActiveOverlayKey = panelActiveOverlays.join("|");
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
          }).map((overlay) => ({
            ...overlay,
            opacity: overlay.opacity * overlayOpacity,
          }))
        : [],
    [
      activeWarming,
      climateOverlayEnabled,
      layers,
      localUrbanCell,
      overlayOpacity,
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
          }).map((overlay) => ({
            ...overlay,
            opacity: overlay.opacity * overlayOpacity,
          }))
        : [],
    [climateOverlayEnabled, localUrbanCell, overlayOpacity, scenarioA],
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
          }).map((overlay) => ({
            ...overlay,
            opacity: overlay.opacity * overlayOpacity,
          }))
        : [],
    [climateOverlayEnabled, localUrbanCell, overlayOpacity, scenarioB],
  );

  useEffect(() => {
    let cancelled = false;

    setLoadingState((current) => ({
      ...current,
      scenario: true,
      explanation: true,
    }));
    setApiError(null);

    Promise.all([
      getScenarioScore({
        city: selectedCity,
        year: selectedYear,
        warming: activeWarming,
        season: selectedSeason,
        overlayTypes: activeLayers,
        localUrbanCell,
      }),
      getScenarioScore({
        city: selectedCity,
        year: inspectedScenarioConfig.year,
        warming: inspectedScenarioConfig.warming,
        season: inspectedScenarioConfig.season,
        overlayTypes: layerNames.filter(
          (layerName) => inspectedScenarioConfig.overlays[layerName],
        ),
        localUrbanCell,
      }),
      getScenarioScore({
        city: selectedCity,
        year: scenarioA.year,
        warming: scenarioA.warming,
        season: scenarioA.season,
        overlayTypes: layerNames.filter((layerName) => scenarioA.overlays[layerName]),
        localUrbanCell,
      }),
      getScenarioScore({
        city: selectedCity,
        year: scenarioB.year,
        warming: scenarioB.warming,
        season: scenarioB.season,
        overlayTypes: layerNames.filter((layerName) => scenarioB.overlays[layerName]),
        localUrbanCell,
      }),
      compareScenarios({
        city: selectedCity,
        scenarioA,
        scenarioB,
        localUrbanCell,
      }),
    ])
      .then(
        ([
          nextScenarioScore,
          nextInspectedScore,
          nextScenarioAScore,
          nextScenarioBScore,
          nextComparisonMetrics,
        ]) => {
          if (cancelled) {
            return;
          }

          setScenarioScore(nextScenarioScore);
          setInspectedScenarioScore(nextInspectedScore);
          setScenarioAScore(nextScenarioAScore);
          setScenarioBScore(nextScenarioBScore);
          setComparisonMetrics(nextComparisonMetrics);
        },
      )
      .catch(() => {
        if (!cancelled) {
          setApiError(
            "Backend data is temporarily unavailable. Showing the latest loaded scenario.",
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingState((current) => ({
            ...current,
            scenario: false,
            explanation: false,
          }));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    activeWarming,
    inspectedScenarioConfig.season,
    inspectedScenarioConfig.overlays,
    inspectedScenarioConfig.warming,
    inspectedScenarioConfig.year,
    layers,
    localUrbanCell,
    scenarioA,
    scenarioB,
    selectedCity,
    selectedSeason,
    selectedYear,
  ]);

  useEffect(() => {
    let cancelled = false;

    if (!regionalMapping) {
      setRegionBoundary(null);
      return;
    }

    getRegionBoundary(regionalMapping)
      .then((boundary) => {
        if (!cancelled) {
          setRegionBoundary(boundary);
          const boundarySource =
            boundary.features[0]?.properties?.boundarySource ??
            regionalMapping.boundarySource;
          const boundaryName = boundary.features[0]?.properties?.boundaryName;
          const boundaryMatchReason =
            boundary.features[0]?.properties?.boundaryMatchReason;
          const dbBoundaryId = boundary.features[0]?.properties?.dbBoundaryId;
          const boundaryClimateRegionType =
            boundary.features[0]?.properties?.boundaryClimateRegionType;

          setRegionalMapping((currentMapping) => {
            if (!currentMapping) {
              return null;
            }

            const unchanged =
              currentMapping.boundarySource === boundarySource &&
              currentMapping.boundaryName === boundaryName &&
              currentMapping.boundaryMatchReason === boundaryMatchReason &&
              currentMapping.dbBoundaryId === dbBoundaryId &&
              currentMapping.boundaryClimateRegionType === boundaryClimateRegionType;

            return unchanged
              ? currentMapping
              : {
                  ...currentMapping,
                  boundarySource,
                  boundaryName,
                  boundaryMatchReason,
                  dbBoundaryId,
                  boundaryClimateRegionType,
                };
          });
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRegionBoundary(null);
          setApiError(
            "Regional boundary could not be loaded from the backend.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, [regionalMapping]);

  useEffect(() => {
    if (!comparisonMode && activePanelTab === "Comparison") {
      setActivePanelTab("Overview");
    }
  }, [activePanelTab, comparisonMode]);

  useEffect(() => {
    let cancelled = false;

    listSavedScenarios()
      .then((scenarios) => {
        if (!cancelled) {
          setSavedScenarios(scenarios);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setSavedScenarios([]);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    setSelectedClimateCell(null);
  }, [climateOverlayEnabled, regionalMapping]);

  useEffect(() => {
    let cancelled = false;
    let timeoutId = 0;

    if (!timelinePlaybackEnabled) {
      return;
    }

    const cacheKey = [
      selectedCity.name,
      warmingPathway,
      activePlaybackLayer,
      selectedSeason,
      playbackYearRange.start,
      playbackYearRange.end,
    ].join("|");
    const cachedTimeline = timelineCacheRef.current.get(cacheKey);

    if (cachedTimeline) {
      setTimelineData(cachedTimeline);
      return;
    }

    setLoadingState((current) => ({ ...current, scenario: true }));
    setTimelineData(null);
    setApiError(null);

    timeoutId = window.setTimeout(() => {
      getClimateTimeline({
        location: selectedCity.name,
        startYear: playbackYearRange.start,
        endYear: playbackYearRange.end,
        warmingPathway,
        layerType: activePlaybackLayer,
        season: selectedSeason,
      })
        .then((timeline) => {
          if (cancelled) {
            return;
          }

          timelineCacheRef.current.set(cacheKey, timeline);

          if (timelineCacheRef.current.size > 8) {
            const oldestKey = timelineCacheRef.current.keys().next().value;

            if (oldestKey) {
              timelineCacheRef.current.delete(oldestKey);
            }
          }

          setTimelineData(timeline);
        })
        .catch(() => {
          if (!cancelled) {
            setTimelineData(null);
            setApiError("Climate timeline could not be loaded from the backend.");
          }
        })
        .finally(() => {
          if (!cancelled) {
            setLoadingState((current) => ({ ...current, scenario: false }));
          }
        });
    }, 280);

    return () => {
      cancelled = true;
      window.clearTimeout(timeoutId);
    };
  }, [
    activePlaybackLayer,
    selectedCity.name,
    selectedSeason,
    timelinePlaybackEnabled,
    warmingPathway,
  ]);

  useEffect(() => {
    if (!timelinePlaybackEnabled || !currentTimelineSnapshot) {
      return;
    }

    setScenarioMode("manual");
    setManualWarming(currentTimelineSnapshot.warmingLevel);
  }, [currentTimelineSnapshot, timelinePlaybackEnabled]);

  useEffect(() => {
    if (!timelinePlaybackEnabled || !timelinePlaying) {
      return;
    }

    const intervalId = window.setInterval(() => {
      setSelectedYear((currentYear) =>
        currentYear >= playbackYearRange.end
          ? playbackYearRange.start
          : currentYear + 1,
      );
    }, Math.max(650, 2200 / playbackSpeed));

    return () => window.clearInterval(intervalId);
  }, [playbackSpeed, timelinePlaybackEnabled, timelinePlaying]);

  useEffect(() => {
    let cancelled = false;

    getCompositeRisk({
      city: panelCity,
      year: panelYear,
      warming: panelWarming,
      season: panelScoreBreakdown.seasonModifier as Season,
      timeOfDay: panelScoreBreakdown.timeOfDayModifier,
      activeLayers: [...panelActiveOverlays],
      selectedGridCell: selectedClimateCell,
    })
      .then((interaction) => {
        if (!cancelled) {
          setClimateInteraction(interaction);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setClimateInteraction(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    panelActiveOverlayKey,
    panelCity,
    panelScoreBreakdown.seasonModifier,
    panelScoreBreakdown.timeOfDayModifier,
    panelWarming,
    panelYear,
    selectedClimateCell,
  ]);

  useEffect(() => {
    let cancelled = false;

    if (
      timelinePlaybackEnabled &&
      timelinePlaying &&
      currentTimelineSnapshot
    ) {
      setAiExplanation({
        humanSummary: `${currentTimelineSnapshot.year} playback frame: ${currentTimelineSnapshot.dominantRiskDriver} is the leading signal while livability is ${currentTimelineSnapshot.livabilityScore}/100 under the ${warmingPathway} pathway.`,
        commuteImpact:
          "Commute exposure is being previewed from the yearly climate timeline.",
        outdoorActivityImpact: `${currentTimelineSnapshot.outdoorComfort} outdoor comfort is projected for this playback year.`,
        nighttimeRecovery:
          "Nighttime recovery updates after playback pauses or the year is stepped manually.",
        vulnerableGroupsNote:
          "Sensitivity guidance is summarized during playback to keep the timeline responsive.",
        confidenceNote:
          "Timeline playback uses cached yearly backend snapshots and the deterministic climate engine.",
        explanationSource: "timeline",
      });
      setLoadingState((current) => ({ ...current, explanation: false }));
      return;
    }

    setLoadingState((current) => ({ ...current, explanation: true }));

    getAIExplanation({
      city: panelCity,
      year: panelYear,
      warming: panelWarming,
      season: panelScoreBreakdown.seasonModifier as Season,
      timeOfDay: panelScoreBreakdown.timeOfDayModifier,
      outdoorComfort: panelOutdoorComfort,
      climateRegionType: panelClimateRegionType,
      dominantRiskDriver: panelDominantRiskDriver,
      selectedGridCell: selectedClimateCell,
      interactionSummary: climateInteraction,
    })
      .then((explanation) => {
        if (!cancelled) {
          setAiExplanation(explanation);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setAiExplanation({
            ...initialAIExplanation,
            humanSummary:
              "Explanation service is temporarily unavailable. Computed scores remain visible.",
          });
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoadingState((current) => ({ ...current, explanation: false }));
        }
      });

    return () => {
      cancelled = true;
    };
  }, [
    panelCity,
    panelClimateRegionType,
    panelDominantRiskDriver,
    panelOutdoorComfort,
    panelScoreBreakdown.seasonModifier,
    panelScoreBreakdown.timeOfDayModifier,
    panelWarming,
    panelYear,
    climateInteraction,
    currentTimelineSnapshot,
    selectedClimateCell,
    timelinePlaybackEnabled,
    timelinePlaying,
    warmingPathway,
  ]);

  useEffect(() => {
    let cancelled = false;

    if (!currentDemoStep) {
      return;
    }

    async function applyDemoStep() {
      const demoCity =
        cityNodes.find((city) => city.name === currentDemoStep?.cityName) ??
        cityNodes[0];

      setLoadingState((current) => ({ ...current, searching: true }));
      setApiError(null);

      try {
        const demoSearch = await searchLocation({
          query: demoCity.name,
          fallbackCenter: [demoCity.longitude, demoCity.latitude],
        });

        if (cancelled || !currentDemoStep) {
          return;
        }

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
      } catch {
        if (!cancelled) {
          setApiError("Demo tour could not load backend search data.");
        }
      } finally {
        if (!cancelled) {
          setLoadingState((current) => ({ ...current, searching: false }));
        }
      }
    }

    void applyDemoStep();

    return () => {
      cancelled = true;
    };
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

    if (enabled) {
      setTimelinePlaybackEnabled(false);
      setTimelinePlaying(false);
    } else {
      setActivePanelTab("Overview");
    }
  }

  function toggleTimelinePlaybackMode() {
    setTimelinePlaybackEnabled((currentValue) => {
      const nextValue = !currentValue;

      if (nextValue) {
        setComparisonMode(false);
        setScenarioMode("manual");
        setClimateOverlayEnabled(true);
        setSelectedYear((currentYear) =>
          Math.min(
            playbackYearRange.end,
            Math.max(playbackYearRange.start, currentYear),
          ),
        );
      } else {
        setTimelinePlaying(false);

        if (!years.some((year) => year === selectedYear)) {
          setSelectedYear(2050);
        }
      }

      return nextValue;
    });
  }

  function stepTimeline(delta: number) {
    setTimelinePlaying(false);
    setSelectedYear((currentYear) =>
      Math.min(
        playbackYearRange.end,
        Math.max(playbackYearRange.start, currentYear + delta),
      ),
    );
  }

  function startDemoTour() {
    setTimelinePlaying(false);
    setTimelinePlaybackEnabled(false);
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

  const selectCity = useCallback(async (city: MapCityNodeData) => {
    setLoadingState((current) => ({ ...current, searching: true }));
    setApiError(null);

    try {
      const result = await searchLocation({
        query: city.name,
        fallbackCenter: [city.longitude, city.latitude],
      });

      setSelectedCity(result.city);
      setRegionalMapping(result.regionalMapping);
    } catch {
      setApiError("Search failed. Keeping the current location selected.");
    } finally {
      setLoadingState((current) => ({ ...current, searching: false }));
    }
  }, []);

  const saveCurrentScenario = useCallback(async () => {
    setSavingScenario(true);
    setApiError(null);

    try {
      const savedScenario = await saveScenario({
        name: `${panelCity.name} ${panelYear} +${panelWarming.toFixed(1)}C`,
        city: panelCity,
        year: panelYear,
        warming: panelWarming,
        season: panelScoreBreakdown.seasonModifier as Season,
        timeOfDay: panelScoreBreakdown.timeOfDayModifier,
        activeLayer: panelActiveOverlays[0] ?? "None",
        outdoorComfort: panelOutdoorComfort,
      });

      setSavedScenarios((current) => [
        savedScenario,
        ...current.filter((scenario) => scenario.id !== savedScenario.id),
      ]);
      setActivePanelTab("Saved");
    } catch {
      setApiError(
        "Scenario could not be saved. Check that the database is running.",
      );
    } finally {
      setSavingScenario(false);
    }
  }, [
    panelActiveOverlays,
    panelCity,
    panelOutdoorComfort,
    panelScoreBreakdown.seasonModifier,
    panelScoreBreakdown.timeOfDayModifier,
    panelWarming,
    panelYear,
  ]);

  const loadSavedScenario = useCallback(async (scenario: SavedScenario) => {
    setLoadingState((current) => ({ ...current, searching: true }));
    setApiError(null);

    try {
      const result = await searchLocation({
        query: scenario.locationName,
        fallbackCenter: [scenario.longitude, scenario.latitude],
      });
      const layerName = layerNames.includes(
        scenario.activeLayer as (typeof layerNames)[number],
      )
        ? (scenario.activeLayer as (typeof layerNames)[number])
        : null;

      setSelectedCity({
        ...result.city,
        livabilityScore: scenario.livabilityScore,
        heatRisk: scenario.heatRisk,
        floodRisk: scenario.floodRisk,
      });
      setRegionalMapping(result.regionalMapping);
      setSelectedYear(scenario.year);
      setManualWarming(scenario.warmingLevel);
      setScenarioMode("manual");
      setSelectedSeason(scenario.season);
      setLayers(layerName ? createLayerPreset([layerName]) : createLayerPreset([]));
      setClimateOverlayEnabled(layerName !== null);
      setComparisonMode(false);
      setTimelinePlaybackEnabled(false);
      setTimelinePlaying(false);
      setFocusedCityName(result.city.name);
      setFocusRequestId((currentId) => currentId + 1);
      setActivePanelTab("Overview");
    } catch {
      setApiError("Saved scenario could not be reloaded.");
    } finally {
      setLoadingState((current) => ({ ...current, searching: false }));
    }
  }, []);

  const removeSavedScenario = useCallback(async (scenarioId: number) => {
    setApiError(null);

    try {
      await deleteSavedScenario(scenarioId);
      setSavedScenarios((current) =>
        current.filter((scenario) => scenario.id !== scenarioId),
      );
    } catch {
      setApiError("Saved scenario could not be deleted.");
    }
  }, []);

  const runRecommendationAdvisor = useCallback(
    async (preferences: RecommendationPreferences) => {
      setRecommendationLoading(true);
      setApiError(null);

      try {
        const result = await getRecommendations({
          city: selectedCity,
          preferences,
        });

        setRecommendationResult(result);
      } catch {
        setApiError("Recommendation advisor could not load future suitability data.");
      } finally {
        setRecommendationLoading(false);
      }
    },
    [selectedCity],
  );

  const runClimateAdvisor = useCallback(
    async (queryText: string, selectedPreferences: string[]) => {
      setAdvisorLoading(true);
      setApiError(null);

      try {
        const result = await queryClimateAdvisor({
          queryText,
          selectedPreferences,
          currentScenarioState: {
            location: selectedCity.name,
            year: selectedYear,
            warming: activeWarming,
            season: selectedSeason,
          },
        });

        setAdvisorResult(result);
      } catch {
        setApiError("Climate Advisor could not parse or score that query.");
      } finally {
        setAdvisorLoading(false);
      }
    },
    [activeWarming, selectedCity.name, selectedSeason, selectedYear],
  );

  const applyAdvisorToMap = useCallback(async (result: AdvisorResult) => {
    setLoadingState((current) => ({ ...current, searching: true }));
    setApiError(null);

    try {
      const searchResult = await searchLocation({
        query: result.extractedInputs.primaryLocation,
        fallbackCenter: [selectedCity.longitude, selectedCity.latitude],
      });

      setSelectedCity(searchResult.city);
      setRegionalMapping(searchResult.regionalMapping);
      setFocusedCityName(searchResult.city.name);
      setFocusRequestId((currentId) => currentId + 1);
      setSelectedYear(result.extractedInputs.targetYear);
      setManualWarming(result.extractedInputs.warmingLevel);
      setScenarioMode("manual");
      setSelectedSeason(result.extractedInputs.season);
      setLayers(createLayerPreset(["Heat Risk"]));
      setClimateOverlayEnabled(true);
      setActivePanelTab("Overview");
    } catch {
      setApiError("Advisor result could not be applied to the map.");
    } finally {
      setLoadingState((current) => ({ ...current, searching: false }));
    }
  }, [selectedCity.latitude, selectedCity.longitude]);

  const addAdvisorComparisonLocation = useCallback(
    async (locationName: string) => {
      setLoadingState((current) => ({ ...current, searching: true }));
      setApiError(null);

      try {
        const result = await searchLocation({
          query: locationName,
          fallbackCenter: [selectedCity.longitude, selectedCity.latitude],
        });

        setSelectedCity(result.city);
        setRegionalMapping(result.regionalMapping);
        setSelectedYear(advisorResult?.extractedInputs.targetYear ?? selectedYear);
        setManualWarming(advisorResult?.extractedInputs.warmingLevel ?? activeWarming);
        setScenarioMode("manual");
        setSelectedSeason(advisorResult?.extractedInputs.season ?? selectedSeason);
        setComparisonMode(true);
        setActivePanelTab("Comparison");
        setFocusedCityName(result.city.name);
        setFocusRequestId((currentId) => currentId + 1);
      } catch {
        setApiError("Comparison location could not be loaded.");
      } finally {
        setLoadingState((current) => ({ ...current, searching: false }));
      }
    },
    [
      activeWarming,
      advisorResult,
      selectedCity.latitude,
      selectedCity.longitude,
      selectedSeason,
      selectedYear,
    ],
  );

  const syncComparisonView = useCallback((view: SyncedMapView) => {
    setSyncedView(view);
    setLastMapView(view);
  }, []);

  const inspectClimateCell = useCallback(
    async (
      cell: { gridCellId: string; layerType: string },
      scenario: {
        year: number;
        warming: number;
        season: Season;
      },
    ) => {
      setLoadingState((current) => ({ ...current, explanation: true }));
      setApiError(null);

      try {
        const detail = await getClimateCellDetail({
          gridCellId: cell.gridCellId,
          layerType: cell.layerType,
          year: scenario.year,
          warming: scenario.warming,
          season: scenario.season,
        });

        setSelectedClimateCell(detail);
        setActivePanelTab("Technical");
      } catch {
        setApiError("Climate cell detail could not be loaded.");
      } finally {
        setLoadingState((current) => ({ ...current, explanation: false }));
      }
    },
    [],
  );

  const searchRegion = useCallback(async (query: string): Promise<SearchResult> => {
    const center = syncedView?.center ?? lastMapView?.center ?? [31, 30];

    setLoadingState((current) => ({ ...current, searching: true }));
    setApiError(null);

    try {
      const result = await searchLocation({
        query,
        fallbackCenter: center,
      });

      setRegionalMapping(result.regionalMapping);
      setSelectedCity(result.city);
      setFocusedCityName(result.kind === "known" ? result.city.name : "");
      setFocusRequestId((currentId) => currentId + 1);

      return result.kind;
    } catch {
      setApiError("Search failed. Check that the FastAPI backend is running.");
      return "regional";
    } finally {
      setLoadingState((current) => ({ ...current, searching: false }));
    }
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

          <div className="mt-3 rounded-lg border border-white/10 bg-white/[0.045] p-4">
            <div className="flex items-center justify-between gap-4">
              <p className="text-xs uppercase tracking-[0.26em] text-white/35">
                Overlay opacity
              </p>
              <p className="text-sm font-medium text-cyan-50">
                {Math.round(overlayOpacity * 100)}%
              </p>
            </div>
            <input
              aria-label="Climate overlay opacity"
              type="range"
              min={45}
              max={100}
              value={Math.round(overlayOpacity * 100)}
              onChange={(event) =>
                setOverlayOpacity(Number(event.currentTarget.value) / 100)
              }
              className="mt-4 h-2 w-full accent-cyan-200"
            />
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

          {(loadingState.searching ||
            loadingState.scenario ||
            loadingState.explanation ||
            apiError) ? (
            <div className="absolute right-6 top-40 z-50 rounded-lg border border-white/10 bg-black/65 px-4 py-3 text-xs text-white/60 shadow-[0_18px_50px_rgba(0,0,0,0.35)] backdrop-blur-2xl">
              {loadingState.searching ? <p>Searching...</p> : null}
              {loadingState.scenario ? <p>Loading scenario...</p> : null}
              {loadingState.explanation ? (
                <p>Generating explanation...</p>
              ) : null}
              {apiError ? <p className="text-amber-100/80">{apiError}</p> : null}
            </div>
          ) : null}

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
                  regionBoundary={regionBoundary}
                  localUrbanCell={localUrbanCell}
                  climateOverlayEnabled={climateOverlayEnabled}
                  climateOverlays={scenarioAClimateOverlays}
                  syncedView={syncedView}
                  onViewChange={syncComparisonView}
                  onClimateSurfaceMetadata={setClimateSurfaceMetadata}
                  onClimateCellSelect={(cell) =>
                    inspectClimateCell(cell, {
                      year: scenarioA.year,
                      warming: scenarioA.warming,
                      season: scenarioA.season,
                    })
                  }
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
                  regionBoundary={regionBoundary}
                  localUrbanCell={localUrbanCell}
                  climateOverlayEnabled={climateOverlayEnabled}
                  climateOverlays={scenarioBClimateOverlays}
                  syncedView={syncedView}
                  onViewChange={syncComparisonView}
                  onClimateSurfaceMetadata={setClimateSurfaceMetadata}
                  onClimateCellSelect={(cell) =>
                    inspectClimateCell(cell, {
                      year: scenarioB.year,
                      warming: scenarioB.warming,
                      season: scenarioB.season,
                    })
                  }
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
              regionBoundary={regionBoundary}
              localUrbanCell={localUrbanCell}
              climateOverlayEnabled={climateOverlayEnabled}
              climateOverlays={singleClimateOverlays}
              onViewChange={setLastMapView}
              onClimateSurfaceMetadata={setClimateSurfaceMetadata}
              onClimateCellSelect={(cell) =>
                inspectClimateCell(cell, {
                  year: selectedYear,
                  warming: activeWarming,
                  season: selectedSeason,
                })
              }
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
            climateRegionType={panelClimateRegionType}
            scoreBreakdown={panelScoreBreakdown}
            dominantRiskDriver={panelDominantRiskDriver}
            rasterSample={panelRasterSample}
            dataEvidence={panelDataEvidence}
            climateSurfaceMetadata={climateSurfaceMetadata}
            climateCellDetail={selectedClimateCell}
            climateInteraction={climateInteraction}
            aiExplanation={aiExplanation}
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
            onSaveScenario={saveCurrentScenario}
            savedScenarios={savedScenarios}
            onLoadSavedScenario={loadSavedScenario}
            onDeleteSavedScenario={removeSavedScenario}
            savingScenario={savingScenario}
            recommendationResult={recommendationResult}
            recommendationLoading={recommendationLoading}
            onRunRecommendation={runRecommendationAdvisor}
            advisorResult={advisorResult}
            advisorLoading={advisorLoading}
            onRunAdvisorQuery={runClimateAdvisor}
            onApplyAdvisorResult={applyAdvisorToMap}
            onAddAdvisorComparisonLocation={addAdvisorComparisonLocation}
            timelinePlaybackEnabled={timelinePlaybackEnabled}
            timelinePlaying={timelinePlaying}
            warmingPathway={warmingPathway}
            timelineSnapshot={currentTimelineSnapshot}
            timelineData={timelineData}
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
            <button
              type="button"
              onClick={toggleTimelinePlaybackMode}
              className={`rounded-full border px-3 py-1.5 text-[11px] font-medium uppercase tracking-[0.16em] transition ${
                timelinePlaybackEnabled
                  ? "border-cyan-100/40 bg-cyan-100/15 text-cyan-50"
                  : "border-white/10 bg-white/[0.04] text-white/45 hover:text-white"
              }`}
            >
              Evolution {timelinePlaybackEnabled ? "On" : "Off"}
            </button>
          </div>

          {timelinePlaybackEnabled ? (
            <>
              <div className="mt-4 flex items-end justify-between gap-4">
                <div>
                  <p className="text-3xl font-semibold leading-none text-white">
                    {selectedYear}
                  </p>
                  <p className="mt-1 text-xs text-cyan-100/55">
                    +{activeWarming.toFixed(1)}C / {warmingPathway}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => stepTimeline(-1)}
                    className="rounded-full border border-white/10 bg-white/[0.045] p-2 text-white/55 transition hover:text-white"
                    aria-label="Step timeline backward"
                  >
                    <SkipBack size={15} strokeWidth={1.8} />
                  </button>
                  <button
                    type="button"
                    onClick={() =>
                      setTimelinePlaying((currentValue) => !currentValue)
                    }
                    className="rounded-full border border-cyan-100/30 bg-cyan-100/12 p-2.5 text-cyan-50 transition hover:bg-cyan-100/18"
                    aria-label={timelinePlaying ? "Pause timeline" : "Play timeline"}
                  >
                    {timelinePlaying ? (
                      <Pause size={16} strokeWidth={1.8} />
                    ) : (
                      <Play size={16} strokeWidth={1.8} />
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => stepTimeline(1)}
                    className="rounded-full border border-white/10 bg-white/[0.045] p-2 text-white/55 transition hover:text-white"
                    aria-label="Step timeline forward"
                  >
                    <SkipForward size={15} strokeWidth={1.8} />
                  </button>
                </div>
              </div>

              <input
                aria-label="Climate evolution year"
                type="range"
                min={playbackYearRange.start}
                max={playbackYearRange.end}
                step={1}
                value={selectedYear}
                onChange={(event) => {
                  setTimelinePlaying(false);
                  setSelectedYear(Number(event.currentTarget.value));
                }}
                className="mt-5 h-2 w-full accent-cyan-200"
              />

              <div className="mt-4 grid grid-cols-3 gap-2">
                {(["optimistic", "moderate", "severe"] as const).map((pathway) => (
                  <button
                    key={pathway}
                    type="button"
                    onClick={() => setWarmingPathway(pathway)}
                    className={`rounded-lg border px-2 py-2 text-[11px] font-medium uppercase tracking-[0.12em] transition ${
                      warmingPathway === pathway
                        ? "border-cyan-100/40 bg-cyan-100/15 text-cyan-50"
                        : "border-white/10 bg-white/[0.035] text-white/42 hover:text-white"
                    }`}
                  >
                    {pathway}
                  </button>
                ))}
              </div>

              <div className="mt-3 flex items-center justify-between gap-3">
                <p className="text-xs uppercase tracking-[0.2em] text-white/35">
                  Speed
                </p>
                <div className="flex gap-1 rounded-full border border-white/10 bg-white/[0.035] p-1">
                  {playbackSpeeds.map((speed) => (
                    <button
                      key={speed}
                      type="button"
                      onClick={() => setPlaybackSpeed(speed)}
                      className={`rounded-full px-2.5 py-1 text-xs transition ${
                        playbackSpeed === speed
                          ? "bg-cyan-100/15 text-cyan-50"
                          : "text-white/42 hover:text-white"
                      }`}
                    >
                      {speed}x
                    </button>
                  ))}
                </div>
              </div>

              {timelineData ? (
                <p className="mt-3 text-xs leading-5 text-white/45">
                  {timelineData.climateEvolutionSummary}
                </p>
              ) : null}
            </>
          ) : (
            <>
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
                value={Math.max(0, years.indexOf(selectedYear))}
                onChange={(event) =>
                  setSelectedYear(years[Number(event.currentTarget.value)])
                }
                className="mt-5 h-2 w-full accent-cyan-200"
              />
            </>
          )}
        </motion.div>
      </section>
    </main>
  );
}
