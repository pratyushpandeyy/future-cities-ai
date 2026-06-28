"use client";

import type { FormEvent } from "react";
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { Search, SlidersHorizontal, Sparkles } from "lucide-react";
import type { Season } from "@/lib/climateOverlaySimulation";
import {
  getLocationSuggestions,
  type LocationSuggestion,
} from "@/lib/api/mockClient";

export type ScenarioMode = "predicted" | "manual";
export type SearchResult = "known" | "regional";

interface SearchScenarioBarProps {
  mode: ScenarioMode;
  warming: number;
  predictedWarming: number;
  selectedYear: number;
  season: Season;
  comparisonMode: boolean;
  scientificView: boolean;
  onModeChange: (mode: ScenarioMode) => void;
  onWarmingChange: (warming: number) => void;
  onSeasonChange: (season: Season) => void;
  onComparisonModeChange: (enabled: boolean) => void;
  onScientificViewChange: (enabled: boolean) => void;
  onDemoTourStart: () => void;
  onSearch: (query: string, parentLocation?: string) => Promise<SearchResult>;
}

export default function SearchScenarioBar({
  mode,
  warming,
  predictedWarming,
  selectedYear,
  season,
  comparisonMode,
  scientificView,
  onModeChange,
  onWarmingChange,
  onSeasonChange,
  onComparisonModeChange,
  onScientificViewChange,
  onDemoTourStart,
  onSearch,
}: SearchScenarioBarProps) {
  const [query, setQuery] = useState("");
  const [parentLocation, setParentLocation] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<LocationSuggestion[]>([]);
  const [suggestionsOpen, setSuggestionsOpen] = useState(false);
  const [suggestionsLoading, setSuggestionsLoading] = useState(false);
  const suggestionRequestId = useRef(0);
  const suppressNextSuggestions = useRef(false);
  const activeWarming = mode === "predicted" ? predictedWarming : warming;

  useEffect(() => {
    const trimmedQuery = query.trim();
    const requestId = suggestionRequestId.current + 1;
    suggestionRequestId.current = requestId;

    if (suppressNextSuggestions.current) {
      suppressNextSuggestions.current = false;
      setSuggestionsLoading(false);
      return;
    }

    if (trimmedQuery.length < 2) {
      setSuggestions([]);
      setSuggestionsLoading(false);
      return;
    }

    setSuggestionsLoading(true);

    const timeoutId = window.setTimeout(async () => {
      try {
        const nextSuggestions = await getLocationSuggestions(
          trimmedQuery,
          parentLocation,
        );

        if (suggestionRequestId.current === requestId) {
          setSuggestions(nextSuggestions);
          setSuggestionsOpen(nextSuggestions.length > 0);
        }
      } catch {
        if (suggestionRequestId.current === requestId) {
          setSuggestions([]);
        }
      } finally {
        if (suggestionRequestId.current === requestId) {
          setSuggestionsLoading(false);
        }
      }
    }, 280);

    return () => window.clearTimeout(timeoutId);
  }, [parentLocation, query]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setMessage("Searching...");

    try {
      const result = await onSearch(query, parentLocation);
      setSuggestionsOpen(false);
      setMessage(
        result === "known" ? null : "Region extrapolation mode activated",
      );
    } catch {
      setMessage("Backend search unavailable. Try again in a moment.");
    }
  }

  async function handleSuggestionSelect(suggestion: LocationSuggestion) {
    suppressNextSuggestions.current = true;
    setQuery(suggestion.locationName);
    setParentLocation(suggestion.hierarchyLabel ?? suggestion.region);
    setSuggestionsOpen(false);
    setMessage("Searching...");

    try {
      const result = await onSearch(
        suggestion.locationName,
        suggestion.hierarchyLabel ?? suggestion.region,
      );
      setMessage(
        result === "known" ? null : "Region extrapolation mode activated",
      );
    } catch {
      setMessage("Backend search unavailable. Try again in a moment.");
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="absolute left-4 right-4 top-4 z-40 rounded-lg border border-white/10 bg-black/60 p-3 shadow-[0_22px_70px_rgba(0,0,0,0.42)] backdrop-blur-2xl md:left-5 md:right-5"
    >
      <div className="grid gap-3 xl:grid-cols-[minmax(260px,1fr)_auto_minmax(260px,360px)] xl:items-center">
        <form onSubmit={handleSubmit} className="space-y-2">
          <div className="relative">
            <Search
              aria-hidden="true"
              size={17}
              strokeWidth={1.8}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-white/40"
            />
            <input
              value={query}
              onChange={(event) => {
                setQuery(event.currentTarget.value);
                setSuggestionsOpen(true);
              }}
              onFocus={() => setSuggestionsOpen(suggestions.length > 0)}
              onKeyDown={(event) => {
                if (event.key === "Escape") {
                  setSuggestionsOpen(false);
                }
              }}
              placeholder="Place or neighborhood"
              className="h-11 w-full rounded-lg border border-white/10 bg-white/[0.055] pl-10 pr-4 text-sm text-white outline-none transition placeholder:text-white/35 focus:border-cyan-200/45 focus:bg-white/[0.075]"
            />
            {suggestionsOpen || suggestionsLoading ? (
              <div className="absolute left-0 right-0 top-[calc(100%+0.35rem)] z-50 overflow-hidden rounded-lg border border-cyan-100/15 bg-[#08111b]/95 shadow-[0_18px_55px_rgba(0,0,0,0.45)] backdrop-blur-xl">
                {suggestionsLoading ? (
                  <div className="px-4 py-3 text-xs uppercase tracking-[0.16em] text-cyan-100/60">
                    Searching places...
                  </div>
                ) : null}
                {!suggestionsLoading && suggestions.length === 0 ? (
                  <div className="px-4 py-3 text-xs text-white/45">
                    Keep typing to resolve a place.
                  </div>
                ) : null}
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion.id}
                    type="button"
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => handleSuggestionSelect(suggestion)}
                    className="grid w-full grid-cols-[1fr_auto] gap-3 border-t border-white/10 px-4 py-3 text-left transition first:border-t-0 hover:bg-cyan-100/10"
                  >
                    <span className="min-w-0">
                      <span className="block truncate text-sm font-semibold text-white">
                        {suggestion.label}
                      </span>
                      <span className="mt-1 block truncate text-xs text-white/45">
                        {suggestion.hierarchyLabel ??
                          [suggestion.city, suggestion.region, suggestion.country]
                            .filter(Boolean)
                            .join(" / ")}
                      </span>
                    </span>
                    <span className="self-center rounded-full border border-white/10 bg-white/[0.05] px-2 py-1 text-[10px] uppercase tracking-[0.14em] text-cyan-100/70">
                      {suggestion.placeType ?? suggestion.geocoderProvider ?? "place"}
                    </span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          <input
            value={parentLocation}
            onChange={(event) => setParentLocation(event.currentTarget.value)}
            placeholder="City, state, or country context"
            className="h-9 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 text-xs text-white outline-none transition placeholder:text-white/30 focus:border-cyan-200/35 focus:bg-white/[0.065]"
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
          <button
            type="button"
            onClick={onDemoTourStart}
            className="inline-flex items-center gap-2 rounded-full border border-cyan-100/30 bg-cyan-100/10 px-3 py-1.5 text-xs font-medium uppercase tracking-[0.18em] text-cyan-50 shadow-[0_0_24px_rgba(34,211,238,0.12)] transition hover:border-cyan-100/50 hover:bg-cyan-100/15"
          >
            <Sparkles size={13} strokeWidth={1.8} />
            Demo Tour
          </button>
        </div>
        <div className="flex rounded-full border border-white/10 bg-white/[0.035] p-1">
          {(["Spring", "Summer", "Monsoon", "Winter"] as const).map(
            (seasonOption) => (
              <button
                key={seasonOption}
                type="button"
                onClick={() => onSeasonChange(seasonOption)}
                className={`rounded-full px-2.5 py-1 text-[11px] font-medium uppercase tracking-[0.14em] transition ${
                  season === seasonOption
                    ? "bg-cyan-100/15 text-cyan-50"
                    : "text-white/40 hover:text-white"
                }`}
              >
                {seasonOption}
              </button>
            ),
          )}
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
