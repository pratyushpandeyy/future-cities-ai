"use client";

import { motion } from "framer-motion";
import type { Season } from "@/lib/climateOverlaySimulation";

export interface ComparisonScenarioConfig {
  year: number;
  warming: number;
  season: Season;
  overlays: Record<string, boolean>;
}

interface ComparisonScenarioControlsProps {
  label: string;
  scenario: ComparisonScenarioConfig;
  years: number[];
  layerNames: readonly string[];
  onChange: (scenario: ComparisonScenarioConfig) => void;
}

export default function ComparisonScenarioControls({
  label,
  scenario,
  years,
  layerNames,
  onChange,
}: ComparisonScenarioControlsProps) {
  function toggleOverlay(layerName: string) {
    onChange({
      ...scenario,
      overlays: {
        ...scenario.overlays,
        [layerName]: !scenario.overlays[layerName],
      },
    });
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="rounded-lg border border-white/10 bg-black/60 p-3 shadow-[0_20px_60px_rgba(0,0,0,0.4)] backdrop-blur-2xl"
    >
      <div className="flex items-center justify-between gap-3">
        <p className="text-xs font-medium uppercase tracking-[0.26em] text-cyan-100/65">
          {label}
        </p>
        <p className="text-sm font-semibold text-white">
          +{scenario.warming.toFixed(1)}C
        </p>
      </div>

      <div className="mt-3 grid grid-cols-4 gap-1.5">
        {years.map((year) => (
          <button
            key={year}
            type="button"
            onClick={() => onChange({ ...scenario, year })}
            className={`rounded-md border px-2 py-1.5 text-xs transition ${
              scenario.year === year
                ? "border-cyan-100/45 bg-cyan-100/15 text-white"
                : "border-white/10 bg-white/[0.045] text-white/50 hover:text-white"
            }`}
          >
            {year}
          </button>
        ))}
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span className="text-xs text-white/35">+1</span>
        <input
          aria-label={`${label} warming level`}
          type="range"
          min={1}
          max={4}
          step={0.1}
          value={scenario.warming}
          onChange={(event) =>
            onChange({
              ...scenario,
              warming: Number(event.currentTarget.value),
            })
          }
          className="w-full accent-cyan-200"
        />
        <span className="text-xs text-white/35">+4</span>
      </div>

      <div className="mt-3 grid grid-cols-4 gap-1.5">
        {(["Spring", "Summer", "Monsoon", "Winter"] as const).map(
          (seasonOption) => (
            <button
              key={seasonOption}
              type="button"
              onClick={() => onChange({ ...scenario, season: seasonOption })}
              className={`rounded-md border px-2 py-1.5 text-[11px] transition ${
                scenario.season === seasonOption
                  ? "border-cyan-100/45 bg-cyan-100/15 text-white"
                  : "border-white/10 bg-white/[0.045] text-white/50 hover:text-white"
              }`}
            >
              {seasonOption}
            </button>
          ),
        )}
      </div>

      <div className="mt-3 flex flex-wrap gap-1.5">
        {layerNames.map((layerName) => (
          <button
            key={layerName}
            type="button"
            onClick={() => toggleOverlay(layerName)}
            className={`rounded-full border px-2.5 py-1 text-[11px] transition ${
              scenario.overlays[layerName]
                ? "border-cyan-100/35 bg-cyan-100/10 text-cyan-50"
                : "border-white/10 bg-white/[0.035] text-white/45 hover:text-white"
            }`}
          >
            {layerName}
          </button>
        ))}
      </div>
    </motion.div>
  );
}
