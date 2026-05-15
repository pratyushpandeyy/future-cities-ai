"use client";

import { motion } from "framer-motion";
import type { MouseEvent } from "react";

export interface MapCityNodeData {
  name: string;
  region: string;
  longitude: number;
  latitude: number;
  x: number;
  y: number;
  livabilityScore: number;
  heatRisk: string;
  floodRisk: string;
  greenCover: string;
  futureSummary: string;
  sportsCultureImpact: string;
  accent: string;
}

interface MapCityNodeProps {
  city: MapCityNodeData;
  isSelected: boolean;
  onSelect: (city: MapCityNodeData) => void;
}

export default function MapCityNode({
  city,
  isSelected,
  onSelect,
}: MapCityNodeProps) {
  function handleSelect(event: MouseEvent<HTMLButtonElement>) {
    event.stopPropagation();
    onSelect(city);
  }

  return (
    <motion.button
      type="button"
      initial={{ opacity: 0, scale: 0.6 }}
      animate={{ opacity: 1, scale: 1 }}
      whileHover={{ scale: 1.12 }}
      whileTap={{ scale: 0.94 }}
      transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
      onClick={handleSelect}
      className="absolute z-20 text-left"
      style={{
        left: `calc(${city.x}% - 0.5rem)`,
        top: `calc(${city.y}% - 0.5rem)`,
      }}
      aria-label={`Open intelligence for ${city.name}`}
    >
      <span
        className={`absolute left-1/2 top-1/2 h-16 w-16 -translate-x-1/2 -translate-y-1/2 rounded-full blur-xl ${city.accent} ${
          isSelected ? "opacity-90" : "opacity-45"
        }`}
      />
      <motion.span
        aria-hidden="true"
        animate={{ scale: [1, 1.7, 1], opacity: [0.38, 0, 0.38] }}
        transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut" }}
        className="absolute left-1/2 top-1/2 h-9 w-9 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-200/45"
      />
      <span
        className={`relative block h-4 w-4 rounded-full border shadow-[0_0_26px_rgba(103,232,249,0.95)] ${
          isSelected
            ? "border-white bg-white"
            : "border-cyan-100/90 bg-cyan-200"
        }`}
      />
      <span
        className={`absolute left-6 top-1/2 hidden -translate-y-1/2 whitespace-nowrap rounded-lg border border-white/10 bg-black/55 px-3 py-2 text-xs font-medium text-white/80 shadow-2xl backdrop-blur-xl md:block ${
          isSelected ? "opacity-100" : "opacity-70"
        }`}
      >
        {city.name}
        <span className="ml-2 text-white/35">{city.livabilityScore}</span>
      </span>
    </motion.button>
  );
}
