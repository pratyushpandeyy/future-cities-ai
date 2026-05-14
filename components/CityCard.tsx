"use client";

import { motion } from "framer-motion";
import type { Variants } from "framer-motion";
import { Activity, Droplets, Flame, Leaf } from "lucide-react";

export interface CityCardData {
  name: string;
  livabilityScore: number;
  heatRisk: string;
  floodRisk: string;
  greenCover: string;
  culturalImpactNote: string;
  accent: string;
}

interface CityCardProps {
  city: CityCardData;
}

const cardVariants: Variants = {
  hidden: { opacity: 0, y: 34, scale: 0.96 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] },
  },
};

export default function CityCard({ city }: CityCardProps) {
  const metrics = [
    {
      label: "Heat risk",
      value: city.heatRisk,
      icon: Flame,
    },
    {
      label: "Flood risk",
      value: city.floodRisk,
      icon: Droplets,
    },
    {
      label: "Green cover",
      value: city.greenCover,
      icon: Leaf,
    },
  ];

  return (
    <motion.article
      variants={cardVariants}
      whileHover={{
        y: -8,
        scale: 1.025,
        transition: { duration: 0.25, ease: "easeOut" },
      }}
      className="group relative overflow-hidden rounded-lg border border-white/10 bg-white/[0.055] p-5 shadow-[0_24px_90px_rgba(0,0,0,0.42)] backdrop-blur-2xl"
    >
      <motion.div
        aria-hidden="true"
        animate={{ opacity: [0.28, 0.58, 0.28], scale: [1, 1.08, 1] }}
        transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }}
        className={`absolute -right-16 -top-20 h-44 w-44 rounded-full blur-3xl ${city.accent}`}
      />
      <div
        aria-hidden="true"
        className="absolute inset-0 rounded-lg bg-[linear-gradient(135deg,rgba(255,255,255,0.18),transparent_38%,rgba(255,255,255,0.08))] opacity-60"
      />
      <div
        aria-hidden="true"
        className="absolute inset-px rounded-lg ring-1 ring-white/10 transition duration-300 group-hover:ring-white/25"
      />

      <div className="relative">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-[0.28em] text-white/40">
              City node
            </p>
            <h3 className="mt-3 text-2xl font-semibold tracking-normal text-white">
              {city.name}
            </h3>
          </div>

          <div className="rounded-full border border-white/10 bg-black/25 p-3 text-cyan-100 shadow-[0_0_36px_rgba(103,232,249,0.16)]">
            <Activity size={20} strokeWidth={1.8} />
          </div>
        </div>

        <div className="mt-8 flex items-end justify-between border-b border-white/10 pb-5">
          <div>
            <p className="text-sm text-white/45">Livability score</p>
            <p className="mt-2 text-5xl font-semibold leading-none text-white">
              {city.livabilityScore}
            </p>
          </div>
          <div className="mb-1 h-2 w-24 overflow-hidden rounded-full bg-white/10">
            <div
              className="h-full rounded-full bg-cyan-200 shadow-[0_0_18px_rgba(103,232,249,0.7)]"
              style={{ width: `${city.livabilityScore}%` }}
            />
          </div>
        </div>

        <div className="mt-5 grid gap-3">
          {metrics.map((metric) => {
            const Icon = metric.icon;

            return (
              <div
                key={metric.label}
                className="flex items-center justify-between gap-4 rounded-lg border border-white/10 bg-black/20 px-3 py-3"
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

        <p className="mt-5 min-h-14 text-sm leading-6 text-white/56">
          {city.culturalImpactNote}
        </p>
      </div>
    </motion.article>
  );
}
