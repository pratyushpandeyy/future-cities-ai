"use client";

import { motion } from "framer-motion";

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-black text-white flex items-center justify-center">

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

      {/* Main Content */}
      <div className="relative z-10 text-center px-6">

        <motion.p
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1 }}
          className="uppercase tracking-[0.3em] text-sm text-gray-400 mb-6"
        >
          Future Cities AI
        </motion.p>

        <motion.h1
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1.2 }}
          className="text-6xl md:text-8xl font-bold leading-tight mb-6"
        >
          Explore the Future
          <br />
          of Urban Life
        </motion.h1>

        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 1.5 }}
          className="text-gray-400 max-w-2xl mx-auto text-lg mb-10"
        >
          AI-powered geospatial intelligence for future livability,
          climate risk, and evolving urban culture.
        </motion.p>

        <motion.button
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.96 }}
          className="px-8 py-4 rounded-full bg-white text-black font-semibold"
        >
          Enter the Map
        </motion.button>

        {/* Floating City Labels */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.8 }}
          className="mt-16 flex flex-wrap gap-4 justify-center text-sm text-gray-500"
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
            )
          )}
        </motion.div>
      </div>
    </main>
  );
}