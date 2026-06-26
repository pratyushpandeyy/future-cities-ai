"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  Bookmark,
  BriefcaseBusiness,
  Clock3,
  Droplets,
  Flame,
  Leaf,
  Network,
  ShieldCheck,
  type LucideIcon,
  Moon,
  Route,
  SlidersHorizontal,
  Sparkles,
  Trash2,
} from "lucide-react";
import type { AreaRiskData } from "@/components/AreaRiskInspector";
import type { MapCityNodeData } from "@/components/MapCityNode";
import type { RegionalMappingData } from "@/components/regionalTypes";
import type { ScenarioMode } from "@/components/SearchScenarioBar";
import type {
  AIExplanation,
  AdvisorResult,
  ClimateDataEvidence,
  ClimateCellDetail,
  ClimateInteractionResult,
  ClimateSurfaceMetadata,
  ClimateTimelineResult,
  ClimateTimelineSnapshot,
  RasterSample,
  RecommendationPreferences,
  RecommendationResult,
  SavedScenario,
  ScoreBreakdown,
  WarmingPathway,
} from "@/lib/api/mockClient";
import type { LocalUrbanCellData } from "@/lib/localCellSimulation";

interface ComparisonMetrics {
  heatIncrease: number;
  livabilityDecline: number;
  outdoorComfortChange: number;
  scientificMetric: string;
  humanTranslation: string;
}

interface ScenarioSnapshot {
  label: string;
  year: number;
  warming: number;
  heatRisk: string;
  floodRisk: string;
  greenCover: string;
  livabilityScore: number;
  outdoorComfort: string;
}

interface IntelligencePanelProps {
  city: MapCityNodeData;
  year: number;
  areaRisk: AreaRiskData | null;
  scenarioMode: ScenarioMode;
  warming: number;
  outdoorComfort: string;
  climateRegionType: string;
  scoreBreakdown: ScoreBreakdown;
  dominantRiskDriver: string;
  rasterSample: RasterSample | null;
  dataEvidence: ClimateDataEvidence | null;
  climateSurfaceMetadata: ClimateSurfaceMetadata | null;
  climateCellDetail: ClimateCellDetail | null;
  climateInteraction: ClimateInteractionResult | null;
  aiExplanation: AIExplanation;
  comparisonMode: boolean;
  scientificView: boolean;
  inspectedScenario: "A" | "B";
  onInspectedScenarioChange: (scenario: "A" | "B") => void;
  comparisonMetrics: ComparisonMetrics;
  scenarioA: ScenarioSnapshot;
  scenarioB: ScenarioSnapshot;
  regionalMapping: RegionalMappingData | null;
  localUrbanCell: LocalUrbanCellData | null;
  activeOverlays: string[];
  activeTab: PanelTab;
  onActiveTabChange: (tab: PanelTab) => void;
  onSaveScenario: () => void;
  savedScenarios: SavedScenario[];
  onLoadSavedScenario: (scenario: SavedScenario) => void;
  onDeleteSavedScenario: (scenarioId: number) => void;
  savingScenario: boolean;
  recommendationResult: RecommendationResult | null;
  recommendationLoading: boolean;
  onRunRecommendation: (preferences: RecommendationPreferences) => void;
  advisorResult: AdvisorResult | null;
  advisorLoading: boolean;
  onRunAdvisorQuery: (queryText: string, selectedPreferences: string[]) => void;
  onApplyAdvisorResult: (result: AdvisorResult) => void;
  onAddAdvisorComparisonLocation: (locationName: string) => void;
  timelinePlaybackEnabled: boolean;
  timelinePlaying: boolean;
  warmingPathway: WarmingPathway;
  timelineSnapshot: ClimateTimelineSnapshot | null;
  timelineData: ClimateTimelineResult | null;
}

export type PanelTab =
  | "Overview"
  | "Impact"
  | "Regional Mapping"
  | "System Interactions"
  | "Future Advisor"
  | "Climate Advisor"
  | "Comparison"
  | "Saved"
  | "Technical";

const tabs: PanelTab[] = [
  "Overview",
  "Impact",
  "Regional Mapping",
  "System Interactions",
  "Climate Advisor",
  "Future Advisor",
  "Comparison",
  "Saved",
  "Technical",
];

const advisorPreferenceChips = [
  "Asthma / respiratory sensitivity",
  "Heat sensitive",
  "Elderly family",
  "Outdoor lifestyle",
  "Walking commute",
  "Remote work",
  "Flood risk avoidant",
  "Prefer cooler cities",
  "Prefer coastal cities",
  "Budget sensitive",
];

function DataRow({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="flex items-center justify-between gap-4 rounded-lg border border-white/10 bg-black/25 px-3 py-2.5">
      <p className="text-xs text-white/40">{label}</p>
      <p className="text-right text-sm font-medium text-white/80">{value}</p>
    </div>
  );
}

function formatBoundarySource(value: RegionalMappingData["boundarySource"]) {
  if (value === "database") {
    return "database";
  }

  if (value === "real_geojson") {
    return "real GeoJSON";
  }

  if (value === "simulated_fallback") {
    return "simulated fallback";
  }

  return "simulated";
}

function formatClimateRegion(value: string) {
  return value.replace(/_/g, " ");
}

function MetricRow({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
}) {
  return (
    <div className="flex items-center justify-between rounded-lg border border-white/10 bg-black/25 px-3 py-3">
      <div className="flex items-center gap-3 text-white/55">
        <Icon size={16} strokeWidth={1.8} />
        <span className="text-sm">{label}</span>
      </div>
      <span className="text-sm font-medium text-white/85">{value}</span>
    </div>
  );
}

function ImpactNote({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: LucideIcon;
}) {
  return (
    <section className="rounded-lg border border-white/10 bg-black/25 p-3">
      <div className="flex items-center gap-2 text-sm font-medium text-white/75">
        <Icon size={15} strokeWidth={1.8} />
        {label}
      </div>
      <p className="mt-2 text-sm leading-6 text-white/55">{value}</p>
    </section>
  );
}

function ScenarioCard({ snapshot }: { snapshot: ScenarioSnapshot }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.045] p-3">
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-cyan-100/60">
          {snapshot.label}
        </p>
        <p className="text-xs text-white/45">
          {snapshot.year} / +{snapshot.warming.toFixed(1)}C
        </p>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <DataRow label="Livability" value={snapshot.livabilityScore} />
        <DataRow label="Heat" value={snapshot.heatRisk} />
        <DataRow label="Flood" value={snapshot.floodRisk} />
        <DataRow label="Comfort" value={snapshot.outdoorComfort} />
      </div>
    </div>
  );
}

function PreferenceSlider({
  label,
  value,
  min = 0,
  max = 100,
  step = 1,
  onChange,
}: {
  label: string;
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
}) {
  return (
    <label className="block rounded-lg border border-white/10 bg-black/25 px-3 py-2.5">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs text-white/42">{label}</span>
        <span className="text-sm font-medium text-white/75">{value}</span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.currentTarget.value))}
        className="mt-3 h-2 w-full accent-cyan-200"
      />
    </label>
  );
}

function PreferenceChoice({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="rounded-lg border border-white/10 bg-black/25 p-3">
      <p className="text-xs text-white/42">{label}</p>
      <div className="mt-3 grid grid-cols-3 gap-1">
        {options.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => onChange(option)}
            className={`rounded-md px-2 py-2 text-[11px] font-medium uppercase tracking-[0.12em] transition ${
              value === option
                ? "bg-cyan-100/15 text-cyan-50"
                : "bg-white/[0.035] text-white/42 hover:text-white"
            }`}
          >
            {option}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function IntelligencePanel({
  city,
  year,
  areaRisk,
  scenarioMode,
  warming,
  outdoorComfort,
  climateRegionType,
  scoreBreakdown,
  dominantRiskDriver,
  rasterSample,
  dataEvidence,
  climateSurfaceMetadata,
  climateCellDetail,
  climateInteraction,
  aiExplanation,
  comparisonMode,
  scientificView,
  inspectedScenario,
  onInspectedScenarioChange,
  comparisonMetrics,
  scenarioA,
  scenarioB,
  regionalMapping,
  localUrbanCell,
  activeOverlays,
  activeTab,
  onActiveTabChange,
  onSaveScenario,
  savedScenarios,
  onLoadSavedScenario,
  onDeleteSavedScenario,
  savingScenario,
  recommendationResult,
  recommendationLoading,
  onRunRecommendation,
  advisorResult,
  advisorLoading,
  onRunAdvisorQuery,
  onApplyAdvisorResult,
  onAddAdvisorComparisonLocation,
  timelinePlaybackEnabled,
  timelinePlaying,
  warmingPathway,
  timelineSnapshot,
  timelineData,
}: IntelligencePanelProps) {
  const [recommendationPreferences, setRecommendationPreferences] =
    useState<RecommendationPreferences>({
      targetYear: 2050,
      warmingTolerance: 2.4,
      heatSensitivity: 62,
      respiratorySensitivity: 42,
      floodRiskTolerance: 45,
      outdoorLifestylePreference: 68,
      urbanVsQuieterPreference: "balanced",
      coastalPreference: "neutral",
      familyElderlySensitivity: 48,
      remoteWorkFlexibility: 58,
    });
  const [advisorQuery, setAdvisorQuery] = useState(
    "I live in Whitefield and have asthma. How bad will summers get by 2050 if warming reaches +2.7C? Should I consider Pune or Manchester instead?",
  );
  const [advisorPreferences, setAdvisorPreferences] = useState<string[]>([
    "Asthma / respiratory sensitivity",
  ]);
  const visibleTabs = comparisonMode
    ? tabs
    : tabs.filter((tab) => tab !== "Comparison");
  const metrics = [
    { label: "Heat risk", value: city.heatRisk, icon: Flame },
    { label: "Flood risk", value: city.floodRisk, icon: Droplets },
    { label: "Green cover", value: city.greenCover, icon: Leaf },
    { label: "Outdoor comfort", value: outdoorComfort, icon: Activity },
  ];

  useEffect(() => {
    if (!comparisonMode && activeTab === "Comparison") {
      onActiveTabChange("Overview");
    }
  }, [activeTab, comparisonMode, onActiveTabChange]);

  return (
    <motion.aside
      key={city.name}
      initial={{ opacity: 0, x: 28 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="relative overflow-hidden rounded-lg border border-white/10 bg-black/50 p-4 shadow-[0_24px_80px_rgba(0,0,0,0.48)] backdrop-blur-2xl"
    >
      <div
        aria-hidden="true"
        className={`absolute -right-24 -top-24 h-56 w-56 rounded-full blur-3xl ${city.accent}`}
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[linear-gradient(145deg,rgba(255,255,255,0.12),transparent_46%,rgba(103,232,249,0.08))]"
      />

      <div className="relative">
        <p className="text-xs font-medium uppercase tracking-[0.3em] text-cyan-100/55">
          Intelligence Panel
        </p>

        <div className="mt-4 flex items-start justify-between gap-4">
          <div>
            <h2 className="text-3xl font-semibold text-white">{city.name}</h2>
            <p className="mt-1 text-sm text-white/45">
              {city.region} / {year} / +{warming.toFixed(1)}C
            </p>
          </div>
          <div className="rounded-full border border-cyan-100/20 bg-cyan-100/10 p-3 text-cyan-100">
            <Activity size={20} strokeWidth={1.8} />
          </div>
        </div>

        {comparisonMode ? (
          <div className="mt-4 rounded-lg border border-white/10 bg-white/[0.045] p-1">
            <div className="grid grid-cols-2 gap-1">
              {(["A", "B"] as const).map((scenario) => (
                <button
                  key={scenario}
                  type="button"
                  onClick={() => onInspectedScenarioChange(scenario)}
                  className={`rounded-md px-3 py-2 text-xs font-medium uppercase tracking-[0.18em] transition ${
                    inspectedScenario === scenario
                      ? "bg-cyan-100/15 text-cyan-50 shadow-[0_0_22px_rgba(103,232,249,0.14)]"
                      : "text-white/45 hover:text-white"
                  }`}
                >
                  Inspect Scenario {scenario}
                </button>
              ))}
            </div>
          </div>
        ) : null}

        <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
          {visibleTabs.map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => onActiveTabChange(tab)}
              className={`shrink-0 rounded-full border px-3 py-1.5 text-[11px] font-medium uppercase tracking-[0.16em] transition ${
                activeTab === tab
                  ? "border-cyan-100/40 bg-cyan-100/15 text-cyan-50 shadow-[0_0_22px_rgba(103,232,249,0.14)]"
                  : "border-white/10 bg-white/[0.035] text-white/42 hover:text-white"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="mt-4 min-h-[520px] space-y-4"
        >
          {activeTab === "Overview" ? (
            <>
              <div className="rounded-lg border border-white/10 bg-white/[0.055] p-4">
                <p className="text-sm text-white/45">Livability score</p>
                <div className="mt-3 flex items-end justify-between">
                  <span className="text-6xl font-semibold leading-none text-white">
                    {city.livabilityScore}
                  </span>
                  <span className="mb-2 text-sm text-cyan-100/70">
                    AI estimate
                  </span>
                </div>
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                  <div
                    className="h-full rounded-full bg-cyan-200 shadow-[0_0_18px_rgba(103,232,249,0.8)]"
                    style={{ width: `${city.livabilityScore}%` }}
                  />
                </div>
              </div>
              <div className="grid gap-3">
                {metrics.map((metric) => (
                  <MetricRow
                    key={metric.label}
                    label={metric.label}
                    value={metric.value}
                    icon={metric.icon}
                  />
                ))}
              </div>
              <div className="rounded-lg border border-cyan-100/15 bg-cyan-100/[0.045] p-4">
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-cyan-100/60">
                  Selected scenario
                </p>
                <p className="mt-3 text-sm leading-6 text-white/55">
                  {scenarioMode === "predicted" ? "Predicted mode" : "Manual scenario"} /{" "}
                  {year} / +{warming.toFixed(1)}C
                </p>
                <button
                  type="button"
                  onClick={onSaveScenario}
                  disabled={savingScenario}
                  className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-lg border border-cyan-100/20 bg-cyan-100/10 px-3 py-2.5 text-xs font-medium uppercase tracking-[0.18em] text-cyan-50 transition hover:bg-cyan-100/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <Bookmark size={14} strokeWidth={1.8} />
                  {savingScenario ? "Saving..." : "Save Scenario"}
                </button>
              </div>
              <details className="group rounded-lg border border-white/10 bg-black/25 p-4">
                <summary className="cursor-pointer list-none text-sm font-medium text-white/80">
                  Why this score?
                </summary>
                <p className="mt-3 text-sm leading-6 text-white/55">
                  {dominantRiskDriver} is the dominant driver in a{" "}
                  {formatClimateRegion(climateRegionType)} climate profile.
                  Warming, {scoreBreakdown.seasonModifier.toLowerCase()} season,
                  and {scoreBreakdown.timeOfDayModifier.toLowerCase()} conditions
                  produce the current livability estimate.
                </p>
                <div className="mt-3 grid grid-cols-2 gap-2">
                  <DataRow label="Heat" value={scoreBreakdown.heatScore} />
                  <DataRow label="Flood" value={scoreBreakdown.floodScore} />
                  <DataRow label="Comfort" value={scoreBreakdown.outdoorComfortScore} />
                  <DataRow label="Air" value={scoreBreakdown.airQualityScore} />
                </div>
              </details>
            </>
          ) : null}

          {activeTab === "Impact" ? (
            <>
              <section className="rounded-lg border border-white/10 bg-white/[0.045] p-4">
                <div className="mb-3 flex items-center gap-2 text-sm font-medium text-white/80">
                  <Sparkles size={15} strokeWidth={1.8} />
                  Human Impact Translation
                </div>
                {scientificView ? (
                  <div className="mb-3 rounded-lg border border-white/10 bg-black/25 p-3">
                    <p className="text-xs text-white/40">Scientific</p>
                    <p className="mt-1 text-sm font-medium text-white">
                      {comparisonMetrics.scientificMetric}
                    </p>
                  </div>
                ) : null}
                <p className="text-sm leading-6 text-white/58">
                  {aiExplanation.humanSummary}
                  {climateCellDetail ? (
                    <>
                      {" "}
                      Selected grid cell {climateCellDetail.gridCellId} shows a{" "}
                      {climateCellDetail.normalizedScore}/100{" "}
                      {formatClimateRegion(climateCellDetail.layerType)} signal,
                      driven by {climateCellDetail.dominantRiskFactor}.
                    </>
                  ) : null}
                </p>
                <p className="mt-3 rounded-full border border-cyan-100/15 bg-cyan-100/[0.06] px-3 py-1.5 text-[11px] uppercase tracking-[0.16em] text-cyan-50/55">
                  Explanation source: {aiExplanation.explanationSource}
                </p>
              </section>
              <div className="grid gap-3">
                <ImpactNote
                  label="Commute impact"
                  value={aiExplanation.commuteImpact}
                  icon={Route}
                />
                <ImpactNote
                  label="Outdoor work impact"
                  value={aiExplanation.outdoorActivityImpact}
                  icon={BriefcaseBusiness}
                />
                <ImpactNote
                  label="Nighttime recovery"
                  value={aiExplanation.nighttimeRecovery}
                  icon={Moon}
                />
                <ImpactNote
                  label="Vulnerable groups"
                  value={aiExplanation.vulnerableGroupsNote}
                  icon={Clock3}
                />
              </div>
              <section>
                <p className="mb-2 text-sm font-medium text-white/80">Confidence note</p>
                <p className="text-sm leading-6 text-white/55">
                  {aiExplanation.confidenceNote}
                </p>
              </section>
              {timelinePlaybackEnabled && timelineData ? (
                <section className="rounded-lg border border-cyan-100/15 bg-cyan-100/[0.045] p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.24em] text-cyan-100/60">
                    Climate Evolution Summary
                  </p>
                  <p className="mt-3 text-sm leading-6 text-white/58">
                    {timelineData.climateEvolutionSummary}
                  </p>
                  {timelineSnapshot ? (
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      <DataRow label="Playback year" value={timelineSnapshot.year} />
                      <DataRow
                        label="Dominant risk"
                        value={timelineSnapshot.dominantRiskDriver}
                      />
                      <DataRow label="Heat score" value={timelineSnapshot.heatScore} />
                      <DataRow
                        label="Livability"
                        value={timelineSnapshot.livabilityScore}
                      />
                    </div>
                  ) : null}
                </section>
              ) : null}
              <section>
                <p className="mb-2 text-sm font-medium text-white/80">
                  Sports/culture note
                </p>
                <p className="text-sm leading-6 text-white/55">
                  {city.sportsCultureImpact}
                </p>
              </section>
            </>
          ) : null}

          {activeTab === "Regional Mapping" ? (
            regionalMapping ? (
              <section className="rounded-lg border border-fuchsia-200/20 bg-fuchsia-200/[0.055] p-4 shadow-[0_0_34px_rgba(217,70,239,0.12)]">
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-fuchsia-100/65">
                  Regional Mapping
                </p>
                <p className="mt-3 rounded-lg border border-cyan-100/15 bg-cyan-100/[0.045] px-3 py-2 text-sm text-cyan-50/75">
                  Mapped region:{" "}
                  <span className="font-medium text-white">
                    {regionalMapping.mappedRegion}
                  </span>
                </p>
                {regionalMapping.hierarchyLabel ? (
                  <p className="mt-3 rounded-lg border border-white/10 bg-black/25 px-3 py-2 text-sm leading-6 text-white/60">
                    {regionalMapping.hierarchyLabel}
                  </p>
                ) : null}
                <div className="mt-4 grid gap-3">
                  <DataRow label="Input location" value={regionalMapping.inputLocation} />
                  {regionalMapping.locality ? (
                    <DataRow label="Locality" value={regionalMapping.locality} />
                  ) : null}
                  {regionalMapping.district ? (
                    <DataRow label="District" value={regionalMapping.district} />
                  ) : null}
                  {regionalMapping.city ? (
                    <DataRow label="City" value={regionalMapping.city} />
                  ) : null}
                  {regionalMapping.country ? (
                    <DataRow label="Country" value={regionalMapping.country} />
                  ) : null}
                  <DataRow label="Mapped region" value={regionalMapping.mappedRegion} />
                  <DataRow label="Climate zone" value={regionalMapping.climateZone} />
                  <DataRow label="Confidence" value={regionalMapping.confidence} />
                  {regionalMapping.placeType ? (
                    <DataRow label="Place type" value={regionalMapping.placeType} />
                  ) : null}
                  <DataRow label="Nearest grid cell" value={regionalMapping.nearestGridCell} />
                  <DataRow
                    label="Boundary source"
                    value={formatBoundarySource(regionalMapping.boundarySource)}
                  />
                  {regionalMapping.boundaryName ? (
                    <DataRow label="Boundary name" value={regionalMapping.boundaryName} />
                  ) : null}
                  {regionalMapping.boundaryMatchReason ? (
                    <DataRow
                      label="Match reason"
                      value={regionalMapping.boundaryMatchReason}
                    />
                  ) : null}
                  {regionalMapping.dbBoundaryId ? (
                    <DataRow label="DB boundary ID" value={regionalMapping.dbBoundaryId} />
                  ) : null}
                  {regionalMapping.boundaryClimateRegionType ? (
                    <DataRow
                      label="Boundary climate"
                      value={formatClimateRegion(regionalMapping.boundaryClimateRegionType)}
                    />
                  ) : null}
                </div>
                <p className="mt-4 text-sm leading-6 text-white/55">
                  This prototype maps places to a regional climate cell. Future
                  versions will use geocoding, administrative boundaries, and
                  climate-grid datasets.
                </p>
              </section>
            ) : (
              <section className="rounded-lg border border-white/10 bg-white/[0.045] p-4">
                <p className="text-sm leading-6 text-white/55">
                  Search or select a city to view simulated regional mapping.
                </p>
              </section>
            )
          ) : null}

          {activeTab === "System Interactions" ? (
            climateInteraction ? (
              <>
                <section className="rounded-lg border border-cyan-100/15 bg-cyan-100/[0.045] p-4 shadow-[0_0_34px_rgba(103,232,249,0.1)]">
                  <div className="flex items-center gap-2 text-sm font-medium text-white/80">
                    <Network size={15} strokeWidth={1.8} />
                    Multi-layer Climate System
                  </div>
                  <div className="mt-4 grid grid-cols-2 gap-2">
                    <DataRow
                      label="Composite risk"
                      value={climateInteraction.compositeRiskScore}
                    />
                    <DataRow
                      label="Resilience"
                      value={climateInteraction.resilienceScore}
                    />
                    <DataRow
                      label="Infrastructure"
                      value={climateInteraction.infrastructurePressure}
                    />
                    <DataRow
                      label="Human exposure"
                      value={climateInteraction.humanExposureScore}
                    />
                  </div>
                  <p className="mt-4 text-sm leading-6 text-white/58">
                    {climateInteraction.dominantInteractionChain}
                  </p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    {climateInteraction.visualIndicators.map((indicator) => (
                      <span
                        key={indicator}
                        className="rounded-full border border-cyan-100/20 bg-cyan-100/[0.07] px-3 py-1.5 text-[11px] uppercase tracking-[0.16em] text-cyan-50/70"
                      >
                        {indicator}
                      </span>
                    ))}
                  </div>
                </section>

                <section className="rounded-lg border border-red-200/15 bg-red-200/[0.045] p-4">
                  <p className="text-xs font-medium uppercase tracking-[0.24em] text-red-100/60">
                    Cascading Risks
                  </p>
                  <div className="mt-3 space-y-2">
                    {climateInteraction.cascadingRisks.map((risk) => (
                      <p
                        key={risk}
                        className="rounded-lg border border-white/10 bg-black/25 px-3 py-2 text-sm leading-5 text-white/58"
                      >
                        {risk}
                      </p>
                    ))}
                  </div>
                </section>

                <section className="rounded-lg border border-emerald-200/15 bg-emerald-200/[0.045] p-4">
                  <div className="flex items-center gap-2 text-sm font-medium text-white/80">
                    <ShieldCheck size={15} strokeWidth={1.8} />
                    Urban Resilience
                  </div>
                  <p className="mt-3 text-sm leading-6 text-white/55">
                    Stabilizing factors and adaptation levers for this regional
                    system.
                  </p>
                  <div className="mt-3 space-y-2">
                    {climateInteraction.mitigationFactors.map((factor) => (
                      <p
                        key={factor}
                        className="rounded-lg border border-white/10 bg-black/25 px-3 py-2 text-sm leading-5 text-white/58"
                      >
                        {factor}
                      </p>
                    ))}
                  </div>
                </section>
              </>
            ) : (
              <section className="rounded-lg border border-white/10 bg-white/[0.045] p-4">
                <p className="text-sm leading-6 text-white/55">
                  System interaction modeling will appear after the current
                  scenario scores load.
                </p>
              </section>
            )
          ) : null}

          {activeTab === "Climate Advisor" ? (
            <>
              <section className="rounded-lg border border-cyan-100/15 bg-cyan-100/[0.045] p-4">
                <div className="flex items-center gap-2 text-sm font-medium text-white/80">
                  <Sparkles size={15} strokeWidth={1.8} />
                  Natural Language Climate Advisor
                </div>
                <textarea
                  value={advisorQuery}
                  onChange={(event) => setAdvisorQuery(event.currentTarget.value)}
                  placeholder="Ask about your future climate risk, relocation options, or how your city changes by 2050..."
                  className="mt-4 min-h-28 w-full resize-none rounded-lg border border-white/10 bg-black/35 px-3 py-3 text-sm leading-6 text-white/75 outline-none placeholder:text-white/30 focus:border-cyan-100/35"
                />
                <div className="mt-3 flex flex-wrap gap-2">
                  {advisorPreferenceChips.map((chip) => {
                    const enabled = advisorPreferences.includes(chip);

                    return (
                      <button
                        key={chip}
                        type="button"
                        onClick={() =>
                          setAdvisorPreferences((current) =>
                            enabled
                              ? current.filter((value) => value !== chip)
                              : [...current, chip],
                          )
                        }
                        className={`rounded-full border px-3 py-1.5 text-[11px] font-medium uppercase tracking-[0.12em] transition ${
                          enabled
                            ? "border-cyan-100/35 bg-cyan-100/15 text-cyan-50"
                            : "border-white/10 bg-white/[0.035] text-white/42 hover:text-white"
                        }`}
                      >
                        {chip}
                      </button>
                    );
                  })}
                </div>
                <button
                  type="button"
                  onClick={() => onRunAdvisorQuery(advisorQuery, advisorPreferences)}
                  disabled={advisorLoading || advisorQuery.trim().length === 0}
                  className="mt-4 inline-flex w-full items-center justify-center rounded-lg border border-cyan-100/20 bg-cyan-100/10 px-3 py-2.5 text-xs font-medium uppercase tracking-[0.18em] text-cyan-50 transition hover:bg-cyan-100/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {advisorLoading ? "Reading Query..." : "Ask Climate Advisor"}
                </button>
              </section>

              {advisorResult ? (
                <>
                  <section className="rounded-lg border border-white/10 bg-white/[0.045] p-4">
                    <p className="text-xs font-medium uppercase tracking-[0.24em] text-white/45">
                      Interpreted Query
                    </p>
                    <p className="mt-3 text-sm leading-6 text-white/58">
                      {advisorResult.interpretedQuery}
                    </p>
                    <div className="mt-3 grid grid-cols-2 gap-2">
                      <DataRow
                        label="Location"
                        value={advisorResult.extractedInputs.primaryLocation}
                      />
                      <DataRow
                        label="Year"
                        value={advisorResult.extractedInputs.targetYear}
                      />
                      <DataRow
                        label="Warming"
                        value={`+${advisorResult.extractedInputs.warmingLevel.toFixed(1)}C`}
                      />
                      <DataRow
                        label="Season"
                        value={advisorResult.extractedInputs.season}
                      />
                      <DataRow
                        label="Risk tolerance"
                        value={advisorResult.extractedInputs.riskTolerance}
                      />
                      <DataRow
                        label="Relocation"
                        value={
                          advisorResult.extractedInputs.relocationIntent
                            ? "Requested"
                            : "Not requested"
                        }
                      />
                    </div>
                    <div className="mt-3 space-y-2">
                      <p className="rounded-lg border border-white/10 bg-black/25 px-3 py-2 text-sm leading-5 text-white/58">
                        Health constraints:{" "}
                        {advisorResult.extractedInputs.healthConstraints.length > 0
                          ? advisorResult.extractedInputs.healthConstraints.join(" / ")
                          : "None detected"}
                      </p>
                      <p className="rounded-lg border border-white/10 bg-black/25 px-3 py-2 text-sm leading-5 text-white/58">
                        Lifestyle constraints:{" "}
                        {advisorResult.extractedInputs.lifestyleConstraints.length > 0
                          ? advisorResult.extractedInputs.lifestyleConstraints.join(
                              " / ",
                            )
                          : "None detected"}
                      </p>
                    </div>
                  </section>

                  <section className="rounded-lg border border-emerald-200/15 bg-emerald-200/[0.045] p-4">
                    <p className="text-xs font-medium uppercase tracking-[0.24em] text-emerald-100/60">
                      Recommendation Summary
                    </p>
                    <p className="mt-3 text-sm leading-6 text-white/58">
                      {advisorResult.recommendationSummary}
                    </p>
                    <p className="mt-3 text-sm leading-6 text-white/58">
                      {advisorResult.humanExplanation.humanSummary}
                    </p>
                  </section>

                  <section className="rounded-lg border border-red-200/15 bg-red-200/[0.045] p-4">
                    <p className="text-xs font-medium uppercase tracking-[0.24em] text-red-100/60">
                      Key Risks
                    </p>
                    <div className="mt-3 space-y-2">
                      {advisorResult.keyRisks.map((risk) => (
                        <p
                          key={risk}
                          className="rounded-lg border border-white/10 bg-black/25 px-3 py-2 text-sm leading-5 text-white/58"
                        >
                          {risk}
                        </p>
                      ))}
                    </div>
                  </section>

                  <section className="rounded-lg border border-cyan-100/15 bg-cyan-100/[0.045] p-4">
                    <p className="text-xs font-medium uppercase tracking-[0.24em] text-cyan-100/60">
                      Suggested Comparisons
                    </p>
                    <div className="mt-3 space-y-2">
                      {advisorResult.suggestedComparisonLocations.map((location) => (
                        <button
                          key={location.locationName}
                          type="button"
                          onClick={() =>
                            onAddAdvisorComparisonLocation(location.locationName)
                          }
                          className="flex w-full items-center justify-between rounded-lg border border-white/10 bg-black/25 px-3 py-2 text-left text-sm text-white/65 transition hover:border-cyan-100/25 hover:text-white"
                        >
                          <span>{location.regionName}</span>
                          <span className="text-cyan-50/70">
                            {location.suitabilityScore}
                          </span>
                        </button>
                      ))}
                    </div>
                    <button
                      type="button"
                      onClick={() => onApplyAdvisorResult(advisorResult)}
                      className="mt-4 inline-flex w-full items-center justify-center rounded-lg border border-cyan-100/20 bg-cyan-100/10 px-3 py-2.5 text-xs font-medium uppercase tracking-[0.18em] text-cyan-50 transition hover:bg-cyan-100/15"
                    >
                      Apply to Map
                    </button>
                  </section>

                  {advisorResult.fallbackLocations.length > 0 ? (
                    <section className="rounded-lg border border-white/10 bg-white/[0.035] p-4">
                      <p className="text-xs font-medium uppercase tracking-[0.24em] text-white/45">
                        Fallback Regions
                      </p>
                      <div className="mt-3 space-y-2">
                        {advisorResult.fallbackLocations.map((location) => (
                          <p
                            key={location.locationName}
                            className="rounded-lg border border-white/10 bg-black/25 px-3 py-2 text-sm leading-5 text-white/58"
                          >
                            {location.regionName} / suitability{" "}
                            {location.suitabilityScore}
                          </p>
                        ))}
                      </div>
                    </section>
                  ) : null}

                  <section>
                    <p className="text-sm leading-6 text-white/55">
                      {advisorResult.confidenceNote}
                    </p>
                  </section>
                </>
              ) : null}
            </>
          ) : null}

          {activeTab === "Future Advisor" ? (
            <>
              <section className="rounded-lg border border-cyan-100/15 bg-cyan-100/[0.045] p-4">
                <div className="flex items-center gap-2 text-sm font-medium text-white/80">
                  <SlidersHorizontal size={15} strokeWidth={1.8} />
                  Future Relocation Advisor
                </div>
                <p className="mt-3 text-sm leading-6 text-white/55">
                  Personalize future habitability preferences, then compare the
                  current location against resilient candidate regions.
                </p>
                <div className="mt-4 grid gap-3">
                  <PreferenceSlider
                    label="Target year"
                    value={recommendationPreferences.targetYear}
                    min={2030}
                    max={2100}
                    step={5}
                    onChange={(targetYear) =>
                      setRecommendationPreferences((current) => ({
                        ...current,
                        targetYear,
                      }))
                    }
                  />
                  <PreferenceSlider
                    label="Warming tolerance"
                    value={recommendationPreferences.warmingTolerance}
                    min={1}
                    max={4}
                    step={0.1}
                    onChange={(warmingTolerance) =>
                      setRecommendationPreferences((current) => ({
                        ...current,
                        warmingTolerance,
                      }))
                    }
                  />
                  <PreferenceSlider
                    label="Heat sensitivity"
                    value={recommendationPreferences.heatSensitivity}
                    onChange={(heatSensitivity) =>
                      setRecommendationPreferences((current) => ({
                        ...current,
                        heatSensitivity,
                      }))
                    }
                  />
                  <PreferenceSlider
                    label="Respiratory sensitivity"
                    value={recommendationPreferences.respiratorySensitivity}
                    onChange={(respiratorySensitivity) =>
                      setRecommendationPreferences((current) => ({
                        ...current,
                        respiratorySensitivity,
                      }))
                    }
                  />
                  <PreferenceSlider
                    label="Flood risk tolerance"
                    value={recommendationPreferences.floodRiskTolerance}
                    onChange={(floodRiskTolerance) =>
                      setRecommendationPreferences((current) => ({
                        ...current,
                        floodRiskTolerance,
                      }))
                    }
                  />
                  <PreferenceSlider
                    label="Outdoor lifestyle preference"
                    value={recommendationPreferences.outdoorLifestylePreference}
                    onChange={(outdoorLifestylePreference) =>
                      setRecommendationPreferences((current) => ({
                        ...current,
                        outdoorLifestylePreference,
                      }))
                    }
                  />
                  <PreferenceSlider
                    label="Family / elderly sensitivity"
                    value={recommendationPreferences.familyElderlySensitivity}
                    onChange={(familyElderlySensitivity) =>
                      setRecommendationPreferences((current) => ({
                        ...current,
                        familyElderlySensitivity,
                      }))
                    }
                  />
                  <PreferenceSlider
                    label="Remote work flexibility"
                    value={recommendationPreferences.remoteWorkFlexibility}
                    onChange={(remoteWorkFlexibility) =>
                      setRecommendationPreferences((current) => ({
                        ...current,
                        remoteWorkFlexibility,
                      }))
                    }
                  />
                  <PreferenceChoice
                    label="Urban preference"
                    value={recommendationPreferences.urbanVsQuieterPreference}
                    options={["balanced", "urban", "quieter"]}
                    onChange={(urbanVsQuieterPreference) =>
                      setRecommendationPreferences((current) => ({
                        ...current,
                        urbanVsQuieterPreference:
                          urbanVsQuieterPreference as RecommendationPreferences["urbanVsQuieterPreference"],
                      }))
                    }
                  />
                  <PreferenceChoice
                    label="Coastal preference"
                    value={recommendationPreferences.coastalPreference}
                    options={["neutral", "coastal", "inland"]}
                    onChange={(coastalPreference) =>
                      setRecommendationPreferences((current) => ({
                        ...current,
                        coastalPreference:
                          coastalPreference as RecommendationPreferences["coastalPreference"],
                      }))
                    }
                  />
                </div>
                <button
                  type="button"
                  onClick={() => onRunRecommendation(recommendationPreferences)}
                  disabled={recommendationLoading}
                  className="mt-4 inline-flex w-full items-center justify-center rounded-lg border border-cyan-100/20 bg-cyan-100/10 px-3 py-2.5 text-xs font-medium uppercase tracking-[0.18em] text-cyan-50 transition hover:bg-cyan-100/15 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {recommendationLoading ? "Evaluating..." : "Run Advisor"}
                </button>
              </section>

              {recommendationResult ? (
                <>
                  <section className="rounded-lg border border-emerald-200/15 bg-emerald-200/[0.045] p-4">
                    <p className="text-xs font-medium uppercase tracking-[0.24em] text-emerald-100/60">
                      Recommendation Summary
                    </p>
                    <p className="mt-3 text-sm leading-6 text-white/58">
                      {recommendationResult.explanationSummary}
                    </p>
                  </section>

                  <div className="grid gap-3">
                    {recommendationResult.recommendedRegions.map((region) => (
                      <article
                        key={region.regionName}
                        className="rounded-lg border border-white/10 bg-black/25 p-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-medium text-white/85">
                              {region.regionName}
                            </p>
                            <p className="mt-1 text-xs text-white/45">
                              {region.locationName}
                            </p>
                          </div>
                          <span className="rounded-full border border-cyan-100/20 bg-cyan-100/[0.07] px-2 py-1 text-xs text-cyan-50/75">
                            {region.suitabilityScore}
                          </span>
                        </div>
                        <p className="mt-3 text-sm leading-6 text-white/58">
                          {region.explanation}
                        </p>
                        <div className="mt-3 grid grid-cols-2 gap-2">
                          <DataRow label="Resilience" value={region.resilienceScore} />
                          <DataRow
                            label="Trajectory"
                            value={region.expectedLivabilityTrajectory}
                          />
                        </div>
                        <p className="mt-3 text-xs leading-5 text-white/45">
                          Tradeoffs: {region.majorTradeoffs.join(" ")}
                        </p>
                      </article>
                    ))}
                  </div>

                  <section className="rounded-lg border border-fuchsia-200/15 bg-fuchsia-200/[0.045] p-4">
                    <p className="text-xs font-medium uppercase tracking-[0.24em] text-fuchsia-100/60">
                      Current vs Recommended
                    </p>
                    <div className="mt-3 grid gap-3">
                      {recommendationResult.comparisonProjection.map((projection) => (
                        <div
                          key={projection.locationName}
                          className="rounded-lg border border-white/10 bg-black/25 p-3"
                        >
                          <p className="text-sm font-medium text-white/80">
                            {projection.locationName}
                          </p>
                          <div className="mt-3 grid grid-cols-2 gap-2">
                            <DataRow
                              label="Livability"
                              value={projection.livabilityScore}
                            />
                            <DataRow
                              label="Resilience"
                              value={projection.resilienceScore}
                            />
                            <DataRow label="Heat" value={projection.heatRisk} />
                            <DataRow label="Flood" value={projection.floodRisk} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </section>

                  <section className="rounded-lg border border-white/10 bg-white/[0.045] p-4">
                    <p className="text-xs font-medium uppercase tracking-[0.24em] text-white/45">
                      Timeline Narratives
                    </p>
                    <div className="mt-3 space-y-2">
                      {recommendationResult.timelineNarratives.map((narrative) => (
                        <p
                          key={narrative}
                          className="rounded-lg border border-white/10 bg-black/25 px-3 py-2 text-sm leading-5 text-white/58"
                        >
                          {narrative}
                        </p>
                      ))}
                    </div>
                  </section>
                </>
              ) : null}
            </>
          ) : null}

          {comparisonMode && activeTab === "Comparison" ? (
            <>
              <ScenarioCard snapshot={scenarioA} />
              <ScenarioCard snapshot={scenarioB} />
              <section className="rounded-lg border border-fuchsia-200/20 bg-fuchsia-200/[0.055] p-4 shadow-[0_0_34px_rgba(217,70,239,0.12)]">
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-fuchsia-100/65">
                  Comparison Delta
                </p>
                <p className="mt-2 text-xs text-white/45">
                  Scenario B relative to Scenario A.
                </p>
                <div className="mt-4 grid grid-cols-3 gap-2">
                  <DataRow label="Heat" value={`+${comparisonMetrics.heatIncrease}`} />
                  <DataRow label="Live" value={`-${comparisonMetrics.livabilityDecline}`} />
                  <DataRow label="Comfort" value={`-${comparisonMetrics.outdoorComfortChange}`} />
                </div>
                <p className="mt-4 text-sm leading-6 text-white/55">
                  {comparisonMetrics.humanTranslation}
                </p>
              </section>
            </>
          ) : null}

          {activeTab === "Saved" ? (
            <section className="rounded-lg border border-cyan-100/15 bg-cyan-100/[0.045] p-4">
              <div className="flex items-center justify-between gap-3">
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-cyan-100/60">
                  Saved Scenarios
                </p>
                <span className="rounded-full border border-white/10 bg-black/25 px-2 py-1 text-xs text-white/45">
                  {savedScenarios.length}
                </span>
              </div>
              {savedScenarios.length > 0 ? (
                <div className="mt-4 space-y-3">
                  {savedScenarios.map((scenario) => (
                    <article
                      key={scenario.id}
                      className="rounded-lg border border-white/10 bg-black/25 p-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <p className="text-sm font-medium text-white/85">
                            {scenario.name}
                          </p>
                          <p className="mt-1 text-xs leading-5 text-white/45">
                            {scenario.locationName} / {scenario.year} / +
                            {scenario.warmingLevel.toFixed(1)}C /{" "}
                            {scenario.season}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => onDeleteSavedScenario(scenario.id)}
                          className="rounded-full border border-white/10 bg-white/[0.035] p-2 text-white/45 transition hover:border-red-200/30 hover:text-red-100"
                          aria-label={`Delete ${scenario.name}`}
                        >
                          <Trash2 size={14} strokeWidth={1.8} />
                        </button>
                      </div>
                      <div className="mt-3 grid grid-cols-3 gap-2">
                        <DataRow label="Live" value={scenario.livabilityScore} />
                        <DataRow label="Heat" value={scenario.heatRisk} />
                        <DataRow label="Layer" value={scenario.activeLayer} />
                      </div>
                      <button
                        type="button"
                        onClick={() => onLoadSavedScenario(scenario)}
                        className="mt-3 inline-flex w-full items-center justify-center rounded-lg border border-cyan-100/15 bg-cyan-100/[0.07] px-3 py-2 text-xs font-medium uppercase tracking-[0.16em] text-cyan-50/75 transition hover:bg-cyan-100/12 hover:text-cyan-50"
                      >
                        Reload Scenario
                      </button>
                    </article>
                  ))}
                </div>
              ) : (
                <p className="mt-4 text-sm leading-6 text-white/55">
                  Save scenarios from the Overview tab to revisit climate
                  simulations later.
                </p>
              )}
            </section>
          ) : null}

          {activeTab === "Technical" ? (
            <>
              <section className="rounded-lg border border-amber-200/20 bg-amber-200/[0.055] p-4 shadow-[0_0_34px_rgba(251,191,36,0.1)]">
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-amber-100/65">
                  Climate Cell Detail
                </p>
                {climateCellDetail ? (
                  <>
                    <div className="mt-4 grid gap-3">
                      <DataRow
                        label="Grid cell ID"
                        value={climateCellDetail.gridCellId}
                      />
                      <DataRow
                        label="Layer type"
                        value={formatClimateRegion(climateCellDetail.layerType)}
                      />
                      <DataRow
                        label="Raw sampled value"
                        value={climateCellDetail.rawSampledValue.toFixed(3)}
                      />
                      <DataRow
                        label="Normalized score"
                        value={climateCellDetail.normalizedScore}
                      />
                      <DataRow label="Scenario year" value={climateCellDetail.year} />
                      <DataRow
                        label="Warming level"
                        value={`+${climateCellDetail.warmingLevel.toFixed(1)}C`}
                      />
                      <DataRow label="Season" value={climateCellDetail.season} />
                      <DataRow
                        label="Data source"
                        value={climateCellDetail.fallbackSourceUsed}
                      />
                      <DataRow
                        label="Confidence"
                        value={climateCellDetail.confidenceLevel}
                      />
                    </div>
                    <p className="mt-4 text-sm leading-6 text-white/58">
                      {climateCellDetail.scoreExplanation}
                    </p>
                  </>
                ) : (
                  <p className="mt-3 text-sm leading-6 text-white/55">
                    Click a rendered climate surface cell on the map to inspect its
                    sampled value, score, confidence, and fallback source.
                  </p>
                )}
              </section>
              <section className="rounded-lg border border-cyan-100/15 bg-cyan-100/[0.045] p-4">
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-cyan-100/60">
                  Simulation Status
                </p>
                <p className="mt-3 text-sm leading-6 text-white/55">
                  Scores blend backend climate samples, feature engineering, and
                  deterministic model rules. If a source is missing, the backend
                  falls back without breaking the interface.
                </p>
              </section>
              <section className="rounded-lg border border-emerald-200/20 bg-emerald-200/[0.045] p-4 shadow-[0_0_34px_rgba(16,185,129,0.1)]">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-xs font-medium uppercase tracking-[0.24em] text-emerald-100/65">
                      Data Evidence
                    </p>
                    <p className="mt-2 text-sm leading-6 text-white/55">
                      {dataEvidence
                        ? dataEvidence.sourceLabel
                        : "No backend evidence payload loaded yet."}
                    </p>
                  </div>
                  <span className="rounded-full border border-white/10 bg-black/25 px-2.5 py-1 text-xs text-white/55">
                    {dataEvidence?.confidence ?? "Unknown"}
                  </span>
                </div>
                <div className="mt-4 grid gap-3">
                  <DataRow
                    label="Data mode"
                    value={dataEvidence?.dataMode ?? "Not loaded"}
                  />
                  <DataRow
                    label="Variable"
                    value={dataEvidence?.sampledVariable ?? "No sample"}
                  />
                  <DataRow
                    label="Sample"
                    value={
                      dataEvidence?.sampledValue !== null &&
                      dataEvidence?.sampledValue !== undefined
                        ? `${dataEvidence.sampledValue.toFixed(3)} ${
                            dataEvidence.sampledUnit ?? ""
                          }`
                        : "No sample"
                    }
                  />
                  <DataRow
                    label="Model / scenario"
                    value={
                      dataEvidence?.model || dataEvidence?.scenario
                        ? `${dataEvidence.model ?? "model n/a"} / ${
                            dataEvidence.scenario ?? "scenario n/a"
                          }`
                        : "No model metadata"
                    }
                  />
                  <DataRow
                    label="Period / month"
                    value={
                      dataEvidence?.period || dataEvidence?.month
                        ? `${dataEvidence.period ?? "period n/a"} / m${
                            dataEvidence.month ?? "n/a"
                          }`
                        : "No temporal metadata"
                    }
                  />
                  <DataRow
                    label="Cache"
                    value={dataEvidence?.cacheHit ? "cache hit" : "fresh/no cache"}
                  />
                </div>
                {dataEvidence?.warning ? (
                  <p className="mt-4 rounded-lg border border-amber-200/15 bg-amber-200/[0.055] px-3 py-2 text-sm leading-6 text-amber-50/70">
                    {dataEvidence.warning}
                  </p>
                ) : null}
              </section>
              <div className="grid gap-3">
                <DataRow
                  label="Active overlays"
                  value={activeOverlays.length > 0 ? activeOverlays.join(" / ") : "None"}
                />
                <DataRow
                  label="Boundary source"
                  value={
                    regionalMapping
                      ? formatBoundarySource(regionalMapping.boundarySource)
                      : "None selected"
                  }
                />
                <DataRow
                  label="Boundary name"
                  value={regionalMapping?.boundaryName ?? "None selected"}
                />
                <DataRow
                  label="Match reason"
                  value={regionalMapping?.boundaryMatchReason ?? "None selected"}
                />
                <DataRow
                  label="DB boundary ID"
                  value={regionalMapping?.dbBoundaryId ?? "None"}
                />
                <DataRow
                  label="Local cell"
                  value={localUrbanCell?.cellId ?? "No cell selected"}
                />
                <DataRow
                  label="Local risk"
                  value={areaRisk?.overallLocalRisk ?? "No area selected"}
                />
                <DataRow
                  label="Climate region"
                  value={formatClimateRegion(climateRegionType)}
                />
                <DataRow label="Dominant driver" value={dominantRiskDriver} />
                <DataRow
                  label="Livability stress"
                  value={scoreBreakdown.livabilityStressScore}
                />
                <DataRow
                  label="Water stress"
                  value={scoreBreakdown.waterStressScore}
                />
                <DataRow
                  label="Raster source"
                  value={rasterSample?.rasterSource ?? "Formula fallback"}
                />
                <DataRow
                  label="Grid cell ID"
                  value={rasterSample?.gridCellId ?? "No raster sample"}
                />
                <DataRow
                  label="Sampled value"
                  value={
                    rasterSample ? rasterSample.sampledValue.toFixed(3) : "No sample"
                  }
                />
                <DataRow
                  label="Dataset resolution"
                  value={rasterSample?.datasetResolution ?? "No dataset"}
                />
                <DataRow
                  label="Active raster layer"
                  value={climateSurfaceMetadata?.activeRasterLayer ?? "No surface"}
                />
                <DataRow
                  label="Rendered grid"
                  value={
                    climateSurfaceMetadata?.renderedGridResolution ?? "No surface"
                  }
                />
                <DataRow
                  label="Surface cells"
                  value={climateSurfaceMetadata?.sampledCellCount ?? "No surface"}
                />
                <DataRow
                  label="Surface source"
                  value={
                    climateSurfaceMetadata?.climateSurfaceSource ?? "Formula fallback"
                  }
                />
                <DataRow
                  label="Selected grid cell"
                  value={climateCellDetail?.gridCellId ?? "No cell selected"}
                />
                <DataRow
                  label="Fallback mode"
                  value={climateCellDetail?.fallbackSourceUsed ?? "No cell selected"}
                />
                <DataRow
                  label="Timeline playback"
                  value={
                    timelinePlaybackEnabled
                      ? timelinePlaying
                        ? "Playing"
                        : "Paused"
                      : "Off"
                  }
                />
                <DataRow label="Active pathway" value={warmingPathway} />
                <DataRow
                  label="Playback year"
                  value={timelineSnapshot?.year ?? "No timeline snapshot"}
                />
                <DataRow
                  label="Timeline value mode"
                  value={timelineData?.valueMode ?? "Not requested"}
                />
                <DataRow
                  label="Temporal resolution"
                  value={timelineData?.temporalResolution ?? "Not requested"}
                />
                <DataRow
                  label="Interaction model"
                  value={
                    climateInteraction?.activeInteractionModel ??
                    "No interaction result"
                  }
                />
                <DataRow
                  label="Cascade depth"
                  value={climateInteraction?.cascadingChainDepth ?? "No interaction result"}
                />
                <DataRow
                  label="Interaction weights"
                  value={
                    climateInteraction
                      ? Object.keys(climateInteraction.interactionWeights).length
                      : "No interaction result"
                  }
                />
                <DataRow
                  label="Resilience modifiers"
                  value={
                    climateInteraction
                      ? Object.keys(climateInteraction.resilienceModifiers).length
                      : "No interaction result"
                  }
                />
                <DataRow
                  label="Recommendation model"
                  value={
                    recommendationResult?.recommendationModel ??
                    "No advisor result"
                  }
                />
              </div>
              {localUrbanCell ? (
                <section className="rounded-lg border border-white/10 bg-black/25 p-3">
                  <p className="text-xs font-medium uppercase tracking-[0.18em] text-white/45">
                    Local Urban Cell
                  </p>
                  <p className="mt-2 text-sm leading-6 text-white/58">
                    {localUrbanCell.explanation.replace("Why this cell differs: ", "")}
                  </p>
                </section>
              ) : null}
              {climateInteraction ? (
                <section className="rounded-lg border border-white/10 bg-black/25 p-3">
                  <p className="text-xs font-medium uppercase tracking-[0.18em] text-white/45">
                    Interaction Parameters
                  </p>
                  <p className="mt-2 text-sm leading-6 text-white/58">
                    Weights:{" "}
                    {Object.entries(climateInteraction.interactionWeights)
                      .map(([key, value]) => `${formatClimateRegion(key)} ${value}`)
                      .join(" / ")}
                  </p>
                  <p className="mt-2 text-sm leading-6 text-white/58">
                    Resilience modifiers:{" "}
                    {Object.entries(climateInteraction.resilienceModifiers)
                      .map(([key, value]) => `${formatClimateRegion(key)} ${value}`)
                      .join(" / ")}
                  </p>
                </section>
              ) : null}
            </>
          ) : null}
        </motion.div>
      </div>
    </motion.aside>
  );
}
