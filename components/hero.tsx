"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { slideVariants, staggerContainer, staggerItem } from "@/lib/animations";

const trustMarkers = [
  "Campus-verified IIT Delhi talent",
  "AI-verified quality gates",
  "Fixed price, clear deadline",
];

export default function Hero() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section className="border-b-4 border-foreground" ref={ref}>
      <div className="grid grid-cols-1 lg:grid-cols-2">
        {/* Left: Bold red accent block with primary CTA */}
        <motion.div 
          className="bg-primary px-8 lg:px-12 py-20 lg:py-32 flex flex-col justify-between"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={slideVariants.slideLeft}
        >
          <div>
            <motion.p 
              className="text-xs font-mono tracking-widest uppercase text-primary-foreground opacity-80 mb-6 font-semibold"
              variants={staggerItem}
            >
              The outcome platform
            </motion.p>
            <motion.h1 
              className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-tight text-primary-foreground mb-8"
              variants={staggerItem}
            >
              Tell us the result.
            </motion.h1>
            <motion.p 
              className="text-base lg:text-lg text-primary-foreground opacity-90 max-w-md leading-relaxed mb-12 font-mono"
              variants={staggerItem}
            >
              Describe your digital outcome. We plan, staff, verify, and ship it. Powered by AI + verified talent.
            </motion.p>
          </div>
          <motion.div variants={staggerItem} whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.98 }}>
            <Link
              href="/start"
              className="inline-flex items-center justify-center h-12 px-8 bg-accent text-accent-foreground text-sm font-bold uppercase tracking-wide hover:opacity-80 transition-opacity w-fit border-2 border-accent-foreground"
            >
              Describe outcome
            </Link>
          </motion.div>
        </motion.div>

        {/* Right: White block with secondary CTA and trust markers */}
        <motion.div 
          className="bg-background px-8 lg:px-12 py-20 lg:py-32 flex flex-col justify-between border-l-4 border-foreground"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={slideVariants.slideRight}
        >
          <div>
            <motion.div className="mb-12" variants={staggerItem}>
              <p className="text-xs font-mono tracking-widest uppercase text-foreground font-bold mb-2">
                Or
              </p>
              <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.98 }}>
                <Link
                  href="/join"
                  className="inline-flex items-center justify-center h-12 px-6 border-4 border-foreground text-foreground text-sm font-bold uppercase tracking-wide hover:bg-foreground hover:text-background transition-colors w-fit"
                >
                  Join as talent
                </Link>
              </motion.div>
            </motion.div>

            <motion.div className="border-t-2 border-foreground pt-8" variants={staggerItem}>
              <p className="text-xs font-mono tracking-widest uppercase text-foreground font-bold mb-6">
                Why we win
              </p>
              <motion.div className="space-y-4" variants={staggerContainer}>
                {trustMarkers.map((m) => (
                  <motion.div key={m} className="flex items-start gap-4" variants={staggerItem}>
                    <div className="w-3 h-3 bg-accent flex-shrink-0 mt-2" aria-hidden="true" />
                    <span className="text-sm font-mono text-foreground leading-snug">{m}</span>
                  </motion.div>
                ))}
              </motion.div>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
