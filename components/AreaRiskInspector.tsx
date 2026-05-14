"use client";

import { motion } from "framer-motion";

export interface AreaRiskData {
  x: number;
  y: number;
  localHeatIndex: number;
  floodExposure: string;
  greenCoverProxy: string;
  walkabilityComfort: string;
  overallLocalRisk: string;
  explanation: string;
}

interface AreaRiskInspectorProps {
  area: AreaRiskData;
}

export default function AreaRiskInspector({ area }: AreaRiskInspectorProps) {
  const tooltipPosition =
    area.x > 72
      ? "right-6 top-1/2 -translate-y-1/2"
      : "left-6 top-1/2 -translate-y-1/2";

  return (
    <motion.div
      key={`${area.x}-${area.y}`}
      initial={{ opacity: 0, scale: 0.7 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
      className="pointer-events-none absolute z-30"
      style={{
        left: `calc(${area.x}% - 0.5rem)`,
        top: `calc(${area.y}% - 0.5rem)`,
      }}
    >
      <motion.span
        aria-hidden="true"
        animate={{ scale: [1, 1.8, 1], opacity: [0.45, 0, 0.45] }}
        transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
        className="absolute left-1/2 top-1/2 h-16 w-16 -translate-x-1/2 -translate-y-1/2 rounded-full border border-fuchsia-200/45"
      />
      <span
        aria-hidden="true"
        className="absolute left-1/2 top-1/2 h-20 w-20 -translate-x-1/2 -translate-y-1/2 rounded-full bg-fuchsia-400/20 blur-2xl"
      />
      <span className="relative block h-4 w-4 rounded-full border border-white bg-fuchsia-200 shadow-[0_0_28px_rgba(240,171,252,0.9)]" />
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.08 }}
        className={`absolute ${tooltipPosition} whitespace-nowrap rounded-lg border border-white/10 bg-black/65 px-3 py-2 text-xs font-medium text-white/85 shadow-2xl backdrop-blur-2xl`}
      >
        Selected urban cell
      </motion.div>
    </motion.div>
  );
}
