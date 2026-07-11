"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { springConfig } from "@/lib/animations";
import AsciiPattern from "@/components/ascii-pattern";

export default function Hero() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section className="bg-background min-h-screen" ref={ref}>
      <div className="max-w-7xl mx-auto px-8 lg:px-12 py-24 lg:py-40">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-24 items-center">
          {/* Left: Content */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -50 }}
            transition={springConfig.scrollReveal}
          >
            <motion.h1 
              className="font-serif text-6xl sm:text-7xl lg:text-8xl font-bold text-foreground leading-tight mb-8"
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ ...springConfig.scrollReveal, delay: 0.1 }}
            >
              Describe your outcome.
            </motion.h1>
            <motion.p 
              className="text-lg text-muted-foreground max-w-lg leading-relaxed mb-12"
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ ...springConfig.scrollReveal, delay: 0.2 }}
            >
              We orchestrate the entire execution—planning, staffing, verification, and delivery. Backed by AI and verified talent.
            </motion.p>

            {/* CTA Button - rounded dark teal */}
            <motion.div 
              whileHover={{ scale: 1.05, boxShadow: "0 10px 30px rgba(0,0,0,0.1)" }}
              whileTap={{ scale: 0.95 }} 
              className="mb-16"
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ ...springConfig.scrollReveal, delay: 0.3 }}
            >
              <Link
                href="/start"
                className="inline-block px-8 py-3 bg-secondary text-secondary-foreground rounded-full font-semibold text-sm hover:opacity-85 transition-opacity duration-300"
              >
                Begin Project
              </Link>
            </motion.div>

            {/* Trust indicators */}
            <motion.div 
              className="space-y-3 text-sm"
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ ...springConfig.scrollReveal, delay: 0.4 }}
            >
              <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold mb-4">Backed by verified talent</p>
              {[
                "IIT Delhi campus-verified specialists",
                "AI-powered quality gates at every checkpoint",
                "Fixed pricing, firm deadlines"
              ].map((text, i) => (
                <motion.div 
                  key={i}
                  className="flex items-center gap-3"
                  initial={{ opacity: 0, x: -10 }}
                  animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -10 }}
                  transition={{ ...springConfig.scrollReveal, delay: 0.5 + i * 0.1 }}
                  whileHover={{ x: 4 }}
                >
                  <span className="w-1 h-1 bg-primary rounded-full flex-shrink-0" aria-hidden="true" />
                  <span className="text-foreground">{text}</span>
                </motion.div>
              ))}
            </motion.div>
          </motion.div>

          {/* Right: ASCII decoration */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: 30 }}
            transition={{ duration: 0.8, ease: "easeOut", delay: 0.1 }}
            className="hidden lg:block"
          >
            <AsciiPattern />
          </motion.div>
        </div>
      </div>
    </section>
  );
}
