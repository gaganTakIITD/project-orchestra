"use client";

import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { springConfig, staggerContainer, staggerItem } from "@/lib/animations";

const trustPoints = [
  {
    label: "01",
    title: "Campus-verified talent",
    description: "Every worker is verified as a student or recent alumni of IIT Delhi. Real credentials, real skills—not resume inflation.",
  },
  {
    label: "02",
    title: "AI-verified quality",
    description: "Gemini vision and reasoning models check every milestone against your acceptance criteria before it ships to you.",
  },
  {
    label: "03",
    title: "Outcome guarantee",
    description: "We rework or reimburse if your outcome doesn't meet spec. No fine print. Your result is guaranteed.",
  },
];

export default function TrustBand() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section className="bg-card border-b border-border" ref={ref}>
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">

        <motion.div 
          className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={springConfig.scrollReveal}
        >
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Built on trust</h2>
          <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
            Three non-negotiable pillars behind every outcome we deliver.
          </p>
        </motion.div>

        <motion.div 
          className="grid grid-cols-1 md:grid-cols-3 border border-border divide-y md:divide-y-0 md:divide-x divide-border"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={staggerContainer}
        >
          {trustPoints.map((point) => (
            <motion.div 
              key={point.label} 
              className="p-8 flex flex-col gap-4 hover:bg-background/50 transition-colors"
              variants={staggerItem}
              whileHover={{ y: -2 }}
            >
              <motion.span 
                className="text-3xl font-bold font-mono text-primary"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={isInView ? { scale: 1, opacity: 1 } : { scale: 0.8, opacity: 0 }}
                transition={{ ...springConfig.scrollReveal, delay: 0.2 }}
              >
                {point.label}
              </motion.span>
              <motion.h3 
                className="text-base font-semibold"
                initial={{ opacity: 0, y: 10 }}
                animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
                transition={{ ...springConfig.scrollReveal, delay: 0.3 }}
              >
                {point.title}
              </motion.h3>
              <motion.p 
                className="text-sm text-muted-foreground leading-relaxed"
                initial={{ opacity: 0, y: 10 }}
                animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
                transition={{ ...springConfig.scrollReveal, delay: 0.4 }}
              >
                {point.description}
              </motion.p>
            </motion.div>
          ))}
        </motion.div>

      </div>
    </section>
  );
}
