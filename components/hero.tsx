"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";

export default function Hero() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section className="bg-background min-h-screen flex flex-col items-center justify-center" ref={ref}>
      <div className="max-w-5xl mx-auto px-8 lg:px-12 text-center">
        {/* Main heading - bold impact */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
          transition={{ duration: 0.9, ease: "easeOut" }}
          className="mb-16"
        >
          <h1 className="font-serif text-7xl sm:text-8xl lg:text-9xl font-bold text-foreground leading-tight mb-8">
            Describe your outcome.
          </h1>
          <div className="w-20 h-1 bg-primary mx-auto mb-12" aria-hidden="true" />
          <p className="text-xl sm:text-2xl text-muted-foreground leading-relaxed max-w-3xl mx-auto">
            We orchestrate the entire execution. Planning, staffing, verification, delivery.
          </p>
        </motion.div>

        {/* CTA - bold button */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.9, ease: "easeOut", delay: 0.2 }}
          className="mb-24"
        >
          <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
            <Link
              href="/start"
              className="inline-block px-10 py-5 bg-primary text-primary-foreground hover:opacity-90 transition-opacity duration-300 text-base font-semibold tracking-wide"
            >
              Begin Project
            </Link>
          </motion.div>
        </motion.div>

        {/* Trust block with color */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.9, ease: "easeOut", delay: 0.35 }}
          className="bg-secondary rounded-lg p-12 max-w-2xl mx-auto"
        >
          <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold mb-8">
            Backed by verified talent
          </p>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <span className="w-2 h-2 bg-accent rounded-full flex-shrink-0 mt-2" aria-hidden="true" />
              <span className="text-sm text-foreground">IIT Delhi campus-verified specialists</span>
            </div>
            <div className="flex items-start gap-4">
              <span className="w-2 h-2 bg-accent rounded-full flex-shrink-0 mt-2" aria-hidden="true" />
              <span className="text-sm text-foreground">AI-powered quality gates at every checkpoint</span>
            </div>
            <div className="flex items-start gap-4">
              <span className="w-2 h-2 bg-accent rounded-full flex-shrink-0 mt-2" aria-hidden="true" />
              <span className="text-sm text-foreground">Fixed pricing, firm deadlines</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
