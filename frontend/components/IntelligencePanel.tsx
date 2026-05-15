"use client";

import { useEffect } from "react";
import { motion } from "framer-motion";
import {
  Activity,
  BriefcaseBusiness,
  Clock3,
  Droplets,
  Flame,
  Leaf,
  type LucideIcon,
  Moon,
  Route,
  Sparkles,
} from "lucide-react";
import type { AreaRiskData } from "@/components/AreaRiskInspector";
import type { MapCityNodeData } from "@/components/MapCityNode";
import type { RegionalMappingData } from "@/components/regionalTypes";
import type { ScenarioMode } from "@/components/SearchScenarioBar";
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
}

export type PanelTab =
  | "Overview"
  | "Impact"
  | "Regional Mapping"
  | "Comparison"
  | "Technical";

const tabs: PanelTab[] = [
  "Overview",
  "Impact",
  "Regional Mapping",
  "Comparison",
  "Technical",
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
  if (value === "real_geojson") {
    return "real GeoJSON";
  }

  if (value === "simulated_fallback") {
    return "simulated fallback";
  }

  return "simulated";
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

export default function IntelligencePanel({
  city,
  year,
  areaRisk,
  scenarioMode,
  warming,
  outdoorComfort,
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
}: IntelligencePanelProps) {
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
              </div>
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
                  {comparisonMode
                    ? comparisonMetrics.humanTranslation
                    : city.futureSummary}
                </p>
              </section>
              <div className="grid gap-3">
                <MetricRow
                  label="Commute impact"
                  value="More shade and transfer cooling needed"
                  icon={Route}
                />
                <MetricRow
                  label="Outdoor work impact"
                  value={city.heatRisk === "High" ? "Severe heat scheduling pressure" : "Moderate exposure windows"}
                  icon={BriefcaseBusiness}
                />
                <MetricRow
                  label="Nighttime recovery"
                  value={warming >= 2.5 ? "Weaker overnight cooling" : "Cooling remains variable"}
                  icon={Moon}
                />
                <MetricRow
                  label="Sports/culture impact"
                  value="District activity shifts toward cooler hours"
                  icon={Clock3}
                />
              </div>
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

          {activeTab === "Technical" ? (
            <>
              <section className="rounded-lg border border-cyan-100/15 bg-cyan-100/[0.045] p-4">
                <p className="text-xs font-medium uppercase tracking-[0.24em] text-cyan-100/60">
                  Simulation Status
                </p>
                <p className="mt-3 text-sm leading-6 text-white/55">
                  Scores, regional boundaries, and climate surfaces are currently
                  simulated. Future versions can swap these fixtures for backend
                  GeoJSON, raster overlays, and grid-cell climate datasets.
                </p>
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
                  label="Local cell"
                  value={localUrbanCell?.cellId ?? "No cell selected"}
                />
                <DataRow
                  label="Local risk"
                  value={areaRisk?.overallLocalRisk ?? "No area selected"}
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
            </>
          ) : null}
        </motion.div>
      </div>
    </motion.aside>
  );
}
