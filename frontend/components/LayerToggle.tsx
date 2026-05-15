"use client";

import { motion } from "framer-motion";

interface LayerToggleProps {
  label: string;
  enabled: boolean;
  onToggle: () => void;
}

export default function LayerToggle({
  label,
  enabled,
  onToggle,
}: LayerToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={enabled}
      onClick={onToggle}
      className="flex w-full items-center justify-between gap-4 rounded-lg border border-white/10 bg-white/[0.045] px-3 py-3 text-left text-sm text-white/70 transition hover:border-cyan-200/30 hover:bg-white/[0.07]"
    >
      <span>{label}</span>
      <span
        className={`flex h-5 w-9 items-center rounded-full p-0.5 transition ${
          enabled ? "bg-cyan-300/80" : "bg-white/10"
        }`}
      >
        <motion.span
          layout
          animate={{ x: enabled ? 16 : 0 }}
          className="h-4 w-4 rounded-full bg-white shadow-[0_0_14px_rgba(255,255,255,0.45)]"
          transition={{ type: "spring", stiffness: 420, damping: 30 }}
        />
      </span>
    </button>
  );
}
