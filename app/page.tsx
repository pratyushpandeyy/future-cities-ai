"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import type { Variants } from "framer-motion";
import CityCard, { type CityCardData } from "@/components/CityCard";

const cities: CityCardData[] = [
  {
    name: "Mumbai",
    livabilityScore: 82,
    heatRisk: "High",
    floodRisk: "Elevated",
    greenCover: "14%",
    culturalImpactNote:
      "Coastal resilience and transit density shape a fast-moving creative economy.",
    accent: "bg-cyan-400/20",
  },
  {
    name: "Bangalore",
    livabilityScore: 88,
    heatRisk: "Medium",
    floodRisk: "Moderate",
    greenCover: "22%",
    culturalImpactNote:
      "Innovation corridors expand around lakes, gardens, and mixed-use tech districts.",
    accent: "bg-emerald-400/20",
  },
  {
    name: "Madrid",
    livabilityScore: 91,
    heatRisk: "Rising",
    floodRisk: "Low",
    greenCover: "31%",
    culturalImpactNote:
      "Public plazas and shaded mobility routes support a warmer civic rhythm.",
    accent: "bg-rose-400/20",
  },
  {
    name: "Istanbul",
    livabilityScore: 79,
    heatRisk: "Medium",
    floodRisk: "Variable",
    greenCover: "18%",
    culturalImpactNote:
      "Historic layers meet adaptive waterfront planning across two continents.",
    accent: "bg-amber-300/20",
  },
  {
    name: "Manchester",
    livabilityScore: 86,
    heatRisk: "Low",
    floodRisk: "Moderate",
    greenCover: "27%",
    culturalImpactNote:
      "Regenerated industrial zones evolve into music, media, and green mobility hubs.",
    accent: "bg-sky-300/20",
  },
];

const previewContainer: Variants = {
  hidden: {},
  visible: {
    transition: {
      staggerChildren: 0.14,
      delayChildren: 0.12,
    },
  },
};

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-black text-white">
      {/* Animated Background Glow */}
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.4, 0.7, 0.4],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute w-[600px] h-[600px] bg-blue-500/20 blur-3xl rounded-full top-[-200px] left-[-200px]"
      />

      <motion.div
        animate={{
          scale: [1, 1.1, 1],
          opacity: [0.3, 0.6, 0.3],
        }}
        transition={{
          duration: 10,
          repeat: Infinity,
          ease: "easeInOut",
        }}
        className="absolute w-[500px] h-[500px] bg-purple-500/20 blur-3xl rounded-full bottom-[-200px] right-[-200px]"
      />

      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.07)_1px,transparent_1px)] [background-size:42px_42px] opacity-20"
      />

      {/* Main Content */}
      <section className="relative z-10 flex min-h-screen items-center justify-center px-6 py-24 text-center">
        <div>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1 }}
            className="mb-6 text-sm uppercase tracking-[0.3em] text-gray-400"
          >
            Future Cities AI
          </motion.p>

          <motion.h1
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2 }}
            className="mb-6 text-5xl font-bold leading-tight sm:text-6xl md:text-8xl"
          >
            Explore the Future
            <br />
            of Urban Life
          </motion.h1>

          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1.5 }}
            className="mx-auto mb-10 max-w-2xl text-lg text-gray-400"
          >
            AI-powered geospatial intelligence for future livability, climate
            risk, and evolving urban culture.
          </motion.p>

          <motion.div
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.96 }}
          >
            <Link
              href="/map"
              className="inline-flex rounded-full bg-white px-8 py-4 font-semibold text-black"
            >
              Enter the Map
            </Link>
          </motion.div>

          {/* Floating City Labels */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.8 }}
            className="mt-16 flex flex-wrap justify-center gap-4 text-sm text-gray-500"
          >
            {["Mumbai", "Madrid", "Istanbul", "Manchester", "Bangalore"].map(
              (city) => (
                <motion.span
                  key={city}
                  whileHover={{
                    scale: 1.15,
                    color: "#ffffff",
                  }}
                  className="cursor-pointer transition-colors"
                >
                  {city}
                </motion.span>
              ),
            )}
          </motion.div>
        </div>
      </section>

      {/* City Intelligence Preview */}
      <section className="relative z-10 px-6 pb-24 md:pb-32">
        <div className="mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 28 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.35 }}
            transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
            className="mx-auto max-w-3xl text-center"
          >
            <p className="text-xs font-medium uppercase tracking-[0.34em] text-cyan-200/60">
              City Intelligence Preview
            </p>
            <h2 className="mt-5 text-4xl font-semibold tracking-normal text-white md:text-6xl">
              Simulated signals for tomorrow&apos;s urban decisions
            </h2>
            <p className="mx-auto mt-5 max-w-2xl text-base leading-8 text-white/48 md:text-lg">
              A lightweight preview of AI-scored livability, climate pressure,
              green infrastructure, and cultural momentum across global cities.
            </p>
          </motion.div>

          <motion.div
            variants={previewContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, amount: 0.18 }}
            className="mt-14 grid gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5"
          >
            {cities.map((city) => (
              <CityCard key={city.name} city={city} />
            ))}
          </motion.div>
        </div>
      </section>
    </main>
  );
}
