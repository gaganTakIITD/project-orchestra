"use client";

import Link from "next/link";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { springConfig } from "@/lib/animations";
import AsciiPattern from "@/components/ascii-pattern";

export default function Hero() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section className="bg-background border-b border-border" ref={ref}>
      <div className="max-w-7xl mx-auto px-8 lg:px-12 pt-20 lg:pt-28 pb-16 lg:pb-20 min-h-[calc(100vh-4rem)] flex flex-col justify-between">
        {/* Top: headline + ascii graphic */}
        <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-12 lg:gap-16 items-start">
          <motion.h1
            className="font-serif text-[3.25rem] leading-[0.98] sm:text-7xl lg:text-8xl font-semibold tracking-[-0.03em] text-foreground text-balance"
            initial={{ opacity: 0, y: 24 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 24 }}
            transition={springConfig.scrollReveal}
          >
            Describe your outcome. We deliver it.
          </motion.h1>

          <motion.div
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : { opacity: 0 }}
            transition={{ duration: 0.9, ease: "easeOut", delay: 0.15 }}
            className="hidden lg:block"
            aria-hidden="true"
          >
            <AsciiPattern />
          </motion.div>
        </div>

        {/* Bottom: label + intro paragraph + CTA */}
        <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_0.9fr] gap-10 lg:gap-16 items-end mt-16 lg:mt-0">
          <motion.p
            className="text-sm text-muted-foreground max-w-xs leading-relaxed"
            initial={{ opacity: 0, y: 16 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 16 }}
            transition={{ ...springConfig.scrollReveal, delay: 0.2 }}
          >
            Outcome-as-a-Service — an AI general contractor for digital work.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 16 }}
            transition={{ ...springConfig.scrollReveal, delay: 0.3 }}
          >
            <p className="text-2xl lg:text-3xl font-serif font-medium tracking-[-0.02em] leading-snug text-foreground text-pretty mb-8">
              We orchestrate the entire execution — planning, staffing,
              verification, and delivery. Backed by AI and campus-verified
              talent.
            </p>
            <div className="flex flex-wrap items-center gap-x-8 gap-y-4">
              <Link
                href="/start"
                className="inline-flex items-center justify-center h-11 px-6 bg-primary text-primary-foreground rounded-sm text-sm font-semibold hover:opacity-90 transition-opacity duration-300"
              >
                Begin project
              </Link>
              <a
                href="#how"
                className="group inline-flex items-center gap-2 text-sm font-medium text-foreground"
              >
                Discover more
                <span
                  className="inline-flex h-7 w-7 items-center justify-center rounded-full border border-border transition-transform duration-300 group-hover:translate-y-0.5"
                  aria-hidden="true"
                >
                  ↓
                </span>
              </a>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
