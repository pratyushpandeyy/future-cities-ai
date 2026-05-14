"use client";

import type { FormEvent } from "react";
import { useState } from "react";
import { motion } from "framer-motion";
import { Search, SlidersHorizontal } from "lucide-react";

export type ScenarioMode = "predicted" | "manual";
export type SearchResult = "known" | "regional";

interface SearchScenarioBarProps {
  mode: ScenarioMode;
  warming: number;
  predictedWarming: number;
  selectedYear: number;
  comparisonMode: boolean;
  scientificView: boolean;
  onModeChange: (mode: ScenarioMode) => void;
  onWarmingChange: (warming: number) => void;
  onComparisonModeChange: (enabled: boolean) => void;
  onScientificViewChange: (enabled: boolean) => void;
  onSearch: (query: string) => SearchResult;
}

export default function SearchScenarioBar({
  mode,
  warming,
  predictedWarming,
  selectedYear,
  comparisonMode,
  scientificView,
  onModeChange,
  onWarmingChange,
  onComparisonModeChange,
  onScientificViewChange,
  onSearch,
}: SearchScenarioBarProps) {
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const activeWarming = mode === "predicted" ? predictedWarming : warming;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const result = onSearch(query);
    setMessage(
      result === "known" ? null : "Region extrapolation mode activated",
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="absolute left-4 right-4 top-4 z-40 rounded-lg border border-white/10 bg-black/60 p-3 shadow-[0_22px_70px_rgba(0,0,0,0.42)] backdrop-blur-2xl md:left-5 md:right-5"
    >
      <div className="grid gap-3 xl:grid-cols-[minmax(260px,1fr)_auto_minmax(260px,360px)] xl:items-center">
        <form onSubmit={handleSubmit} className="relative">
          <Search
            aria-hidden="true"
            size={17}
            strokeWidth={1.8}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40"
          />
          <input
            value={query}
            onChange={(event) => setQuery(event.currentTarget.value)}
            placeholder="Search any city, province, or neighborhood"
            className="h-11 w-full rounded-lg border border-white/10 bg-white/[0.055] pl-10 pr-4 text-sm text-white outline-none transition placeholder:text-white/35 focus:border-cyan-200/45 focus:bg-white/[0.075]"
          />
          {message ? (
            <motion.p
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              className="mt-2 text-xs text-amber-100/80"
            >
              {message}
            </motion.p>
          ) : null}
        </form>

        <div className="flex rounded-lg border border-white/10 bg-white/[0.045] p-1">
          {(["predicted", "manual"] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => onModeChange(option)}
              className={`rounded-md px-3 py-2 text-xs font-medium uppercase tracking-[0.18em] transition ${
                mode === option
                  ? "bg-cyan-100/15 text-cyan-100 shadow-[0_0_22px_rgba(103,232,249,0.16)]"
                  : "text-white/45 hover:text-white"
              }`}
            >
              {option === "predicted" ? "Predicted Mode" : "Manual Scenario"}
            </button>
          ))}
        </div>

        <div className="rounded-lg border border-white/10 bg-white/[0.045] p-3">
          <div className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em] text-white/45">
              <SlidersHorizontal size={15} strokeWidth={1.8} />
              Warming
            </div>
            <div className="rounded-full border border-cyan-100/20 bg-cyan-100/10 px-3 py-1 text-xs font-medium text-cyan-100">
              AI projected warming for {selectedYear}: +
              {predictedWarming.toFixed(1)}C
            </div>
          </div>
          <div className="mt-3 flex items-center gap-3">
            <span className="text-xs text-white/35">+1.0C</span>
            <input
              aria-label="Global warming scenario"
              type="range"
              min={1}
              max={4}
              step={0.1}
              value={activeWarming}
              disabled={mode === "predicted"}
              onChange={(event) =>
                onWarmingChange(Number(event.currentTarget.value))
              }
              className="w-full accent-cyan-200 disabled:opacity-45"
            />
            <span className="text-xs text-white/35">+4.0C</span>
            <span className="w-14 text-right text-sm font-semibold text-white">
              +{activeWarming.toFixed(1)}C
            </span>
          </div>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-white/10 pt-3">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onComparisonModeChange(!comparisonMode)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium uppercase tracking-[0.18em] transition ${
              comparisonMode
                ? "border-fuchsia-100/40 bg-fuchsia-100/15 text-fuchsia-50"
                : "border-white/10 bg-white/[0.04] text-white/45 hover:text-white"
            }`}
          >
            Comparison Mode
          </button>
          <button
            type="button"
            onClick={() => onScientificViewChange(!scientificView)}
            className={`rounded-full border px-3 py-1.5 text-xs font-medium uppercase tracking-[0.18em] transition ${
              scientificView
                ? "border-cyan-100/40 bg-cyan-100/15 text-cyan-50"
                : "border-white/10 bg-white/[0.04] text-white/45 hover:text-white"
            }`}
          >
            Scientific View
          </button>
        </div>
        <p className="text-xs text-white/40">
          {comparisonMode
            ? "Split climate comparison active"
            : "Single scenario exploration"}
        </p>
      </div>
    </motion.div>
  );
}
