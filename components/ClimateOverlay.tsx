"use client";

import type { ClimateOverlayRenderModel } from "@/lib/climateOverlaySimulation";

interface ClimateOverlayProps {
  enabled: boolean;
  overlays: ClimateOverlayRenderModel[];
  regionLabel?: string;
}

export default function ClimateOverlay({
  enabled,
  overlays,
  regionLabel,
}: ClimateOverlayProps) {
  const primaryOverlay = overlays[0];

  return (
    enabled && primaryOverlay ? (
      <div className="pointer-events-none absolute bottom-24 right-4 z-30 w-52 rounded-lg border border-white/10 bg-black/55 p-3 shadow-[0_18px_60px_rgba(0,0,0,0.45)] backdrop-blur-2xl">
        <div className="flex items-center justify-between gap-3">
          <p className="text-xs font-medium uppercase tracking-[0.22em] text-white/55">
            {primaryOverlay.label}
          </p>
          <p className="text-xs text-cyan-100/75">Surface</p>
        </div>
        {regionLabel ? (
          <p className="mt-2 text-xs leading-5 text-white/55">
            Mapped region:{" "}
            <span className="font-medium text-cyan-50/80">{regionLabel}</span>
          </p>
        ) : null}
        <div
          className="mt-3 h-2 rounded-full shadow-[0_0_18px_rgba(103,232,249,0.18)]"
          style={{ background: primaryOverlay.legendGradient }}
        />
        <div className="mt-2 flex items-center justify-between text-[11px] uppercase tracking-[0.18em] text-white/40">
          <span>Low</span>
          <span>Extreme</span>
        </div>
        <p className="mt-3 rounded-full border border-cyan-100/15 bg-cyan-100/[0.06] px-2.5 py-1 text-[11px] uppercase tracking-[0.16em] text-cyan-50/60">
          Region overlay: simulated boundary
        </p>
        <p className="mt-2 text-[11px] leading-4 text-white/35">
          Boundary and climate surface are simulated for this prototype.
        </p>
      </div>
    ) : null
  );
}
