"use client";

import { motion } from "framer-motion";
import { Activity, Droplets, Flame, Leaf, Sparkles } from "lucide-react";
import type { AreaRiskData } from "@/components/AreaRiskInspector";
import type { MapCityNodeData } from "@/components/MapCityNode";

interface IntelligencePanelProps {
  city: MapCityNodeData;
  year: number;
  areaRisk: AreaRiskData | null;
}

export default function IntelligencePanel({
  city,
  year,
  areaRisk,
}: IntelligencePanelProps) {
  const metrics = [
    { label: "Heat risk", value: city.heatRisk, icon: Flame },
    { label: "Flood risk", value: city.floodRisk, icon: Droplets },
    { label: "Green cover", value: city.greenCover, icon: Leaf },
  ];

  return (
    <motion.aside
      key={city.name}
      initial={{ opacity: 0, x: 28 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      className="relative overflow-hidden rounded-lg border border-white/10 bg-black/50 p-5 shadow-[0_24px_80px_rgba(0,0,0,0.48)] backdrop-blur-2xl"
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
              {city.region} projection / {year}
            </p>
          </div>
          <div className="rounded-full border border-cyan-100/20 bg-cyan-100/10 p-3 text-cyan-100">
            <Activity size={20} strokeWidth={1.8} />
          </div>
        </div>

        <div className="mt-8 rounded-lg border border-white/10 bg-white/[0.055] p-4">
          <p className="text-sm text-white/45">Livability score</p>
          <div className="mt-3 flex items-end justify-between">
            <span className="text-6xl font-semibold leading-none text-white">
              {city.livabilityScore}
            </span>
            <span className="mb-2 text-sm text-cyan-100/70">AI estimate</span>
          </div>
          <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-cyan-200 shadow-[0_0_18px_rgba(103,232,249,0.8)]"
              style={{ width: `${city.livabilityScore}%` }}
            />
          </div>
        </div>

        <div className="mt-4 grid gap-3">
          {metrics.map((metric) => {
            const Icon = metric.icon;

            return (
              <div
                key={metric.label}
                className="flex items-center justify-between rounded-lg border border-white/10 bg-black/25 px-3 py-3"
              >
                <div className="flex items-center gap-3 text-white/55">
                  <Icon size={16} strokeWidth={1.8} />
                  <span className="text-sm">{metric.label}</span>
                </div>
                <span className="text-sm font-medium text-white/85">
                  {metric.value}
                </span>
              </div>
            );
          })}
        </div>

        <div className="mt-5 space-y-4">
          {areaRisk ? (
            <motion.section
              key={`${areaRisk.x}-${areaRisk.y}`}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="rounded-lg border border-fuchsia-200/20 bg-fuchsia-200/[0.055] p-4 shadow-[0_0_30px_rgba(217,70,239,0.12)]"
            >
              <p className="text-xs font-medium uppercase tracking-[0.26em] text-fuchsia-100/65">
                Local Area Risk
              </p>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-white/40">Local heat index</p>
                  <p className="mt-1 text-lg font-semibold text-white">
                    {areaRisk.localHeatIndex}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-white/40">Flood exposure</p>
                  <p className="mt-1 text-lg font-semibold text-white">
                    {areaRisk.floodExposure}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-white/40">Green cover proxy</p>
                  <p className="mt-1 text-lg font-semibold text-white">
                    {areaRisk.greenCoverProxy}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-white/40">Walkability comfort</p>
                  <p className="mt-1 text-lg font-semibold text-white">
                    {areaRisk.walkabilityComfort}
                  </p>
                </div>
              </div>
              <div className="mt-4 rounded-lg border border-white/10 bg-black/25 px-3 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm text-white/55">Overall local risk</p>
                  <p className="text-sm font-semibold text-fuchsia-100">
                    {areaRisk.overallLocalRisk}
                  </p>
                </div>
                <p className="mt-3 text-sm leading-6 text-white/55">
                  {areaRisk.explanation}
                </p>
              </div>
            </motion.section>
          ) : null}

          <section>
            <div className="mb-2 flex items-center gap-2 text-sm font-medium text-white/80">
              <Sparkles size={15} strokeWidth={1.8} />
              Future summary
            </div>
            <p className="text-sm leading-6 text-white/55">
              {city.futureSummary}
            </p>
          </section>

          <section>
            <p className="mb-2 text-sm font-medium text-white/80">
              Sports/culture impact
            </p>
            <p className="text-sm leading-6 text-white/55">
              {city.sportsCultureImpact}
            </p>
          </section>
        </div>
      </div>
    </motion.aside>
  );
}
