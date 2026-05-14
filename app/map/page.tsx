"use client";

import Link from "next/link";
import type { MouseEvent } from "react";
import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowLeft, Layers, Radar } from "lucide-react";
import AreaRiskInspector, {
  type AreaRiskData,
} from "@/components/AreaRiskInspector";
import IntelligencePanel from "@/components/IntelligencePanel";
import LayerToggle from "@/components/LayerToggle";
import MapCityNode, { type MapCityNodeData } from "@/components/MapCityNode";

const cityNodes: MapCityNodeData[] = [
  {
    name: "Mumbai",
    region: "Arabian Sea megacity corridor",
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

type LayerState = Record<(typeof layerNames)[number], boolean>;

const initialLayers = layerNames.reduce<LayerState>(
  (layers, layerName, index) => ({
    ...layers,
    [layerName]: index < 3,
  }),
  {} as LayerState,
);

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

export default function MapPage() {
  const [selectedCity, setSelectedCity] = useState<MapCityNodeData>(
    cityNodes[0],
  );
  const [selectedYear, setSelectedYear] = useState(2030);
  const [layers, setLayers] = useState<LayerState>(initialLayers);
  const [areaRisk, setAreaRisk] = useState<AreaRiskData | null>(null);

  const activeLayers = layerNames.filter((layerName) => layers[layerName]);

  function toggleLayer(layerName: keyof LayerState) {
    setLayers((currentLayers) => ({
      ...currentLayers,
      [layerName]: !currentLayers[layerName],
    }));
  }

  function inspectArea(event: MouseEvent<HTMLDivElement>) {
    const bounds = event.currentTarget.getBoundingClientRect();
    const x = ((event.clientX - bounds.left) / bounds.width) * 100;
    const y = ((event.clientY - bounds.top) / bounds.height) * 100;

    setAreaRisk(
      createAreaRisk(
        Math.min(100, Math.max(0, x)),
        Math.min(100, Math.max(0, y)),
      ),
    );
  }

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
          onClick={inspectArea}
          className="relative min-h-[520px] overflow-hidden rounded-lg border border-white/10 bg-slate-950/55 shadow-[0_30px_110px_rgba(0,0,0,0.5)] backdrop-blur-xl lg:col-start-2 lg:row-span-2 lg:min-h-0"
        >
          <div
            aria-hidden="true"
            className="absolute inset-0 bg-[radial-gradient(ellipse_at_65%_55%,rgba(34,211,238,0.16),transparent_26%),radial-gradient(ellipse_at_42%_38%,rgba(244,114,182,0.12),transparent_22%),radial-gradient(ellipse_at_49%_43%,rgba(251,191,36,0.12),transparent_18%)]"
          />
          <div
            aria-hidden="true"
            className="absolute inset-0 opacity-75 [background-image:linear-gradient(120deg,transparent_0_18%,rgba(125,211,252,0.18)_18.4%,transparent_19%,transparent_40%,rgba(255,255,255,0.08)_40.5%,transparent_41%),linear-gradient(25deg,transparent_0_30%,rgba(255,255,255,0.07)_30.4%,transparent_31%,transparent_66%,rgba(125,211,252,0.12)_66.5%,transparent_67%)] [background-size:240px_180px,310px_230px]"
          />
          <div
            aria-hidden="true"
            className="absolute left-[38%] top-[25%] h-[54%] w-[35%] rounded-[48%] border border-cyan-100/10 bg-cyan-100/[0.025] blur-[0.2px]"
          />
          <div
            aria-hidden="true"
            className="absolute left-[58%] top-[42%] h-[34%] w-[25%] rounded-[48%] border border-emerald-100/10 bg-emerald-100/[0.025]"
          />
          <div
            aria-hidden="true"
            className="absolute left-[32%] top-[16%] h-[22%] w-[16%] rounded-[45%] border border-white/10 bg-white/[0.018]"
          />

          <div className="absolute left-5 top-5 z-30 rounded-lg border border-white/10 bg-black/45 px-4 py-3 backdrop-blur-2xl">
            <div className="flex items-center gap-2 text-sm text-white/75">
              <Radar size={16} strokeWidth={1.8} />
              Simulation viewport
            </div>
            <p className="mt-1 text-xs text-white/40">
              Dummy intelligence layer / no Mapbox
            </p>
          </div>

          {cityNodes.map((city) => (
            <MapCityNode
              key={city.name}
              city={city}
              isSelected={selectedCity.name === city.name}
              onSelect={setSelectedCity}
            />
          ))}

          {areaRisk ? <AreaRiskInspector area={areaRisk} /> : null}

          <div
            aria-hidden="true"
            className="absolute inset-x-0 bottom-0 h-36 bg-gradient-to-t from-black/70 to-transparent"
          />
        </motion.div>

        <div className="lg:col-start-3 lg:row-start-1">
          <IntelligencePanel
            city={selectedCity}
            year={selectedYear}
            areaRisk={areaRisk}
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
