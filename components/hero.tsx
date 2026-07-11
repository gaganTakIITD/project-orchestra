"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";

export default function Hero() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section className="bg-background" ref={ref}>
      <div className="max-w-6xl mx-auto px-8 lg:px-12 py-32 lg:py-48">
        {/* Main heading with serif elegance */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
          className="mb-24"
        >
          <h1 className="font-serif text-6xl sm:text-7xl lg:text-8xl font-light text-foreground leading-tight mb-8">
            Describe the outcome.
          </h1>
          <p className="font-serif text-2xl sm:text-3xl text-muted-foreground font-light leading-relaxed max-w-3xl">
            We orchestrate the entire execution — planning, staffing, verification, and delivery.
          </p>
        </motion.div>

        {/* CTA and description */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.8, ease: "easeOut", delay: 0.15 }}
          className="space-y-12"
        >
          <div className="flex flex-col gap-6">
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Link
                href="/start"
                className="inline-block px-8 py-4 border border-foreground text-foreground hover:bg-foreground hover:text-background transition-colors duration-300 text-sm font-light tracking-wide"
              >
                Begin
              </Link>
            </motion.div>
            <p className="text-sm text-muted-foreground max-w-xl leading-relaxed">
              Tell us your vision. Our AI analyzes the scope, our network executes with precision, and verification ensures quality at every milestone.
            </p>
          </div>

          {/* Trust indicators */}
          <div className="pt-12 border-t border-border">
            <p className="text-xs text-muted-foreground uppercase tracking-widest font-light mb-8">
              Backed by verified talent
            </p>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="w-1.5 h-1.5 bg-primary rounded-full" aria-hidden="true" />
                <span className="text-sm text-foreground">IIT Delhi campus-verified specialists</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-1.5 h-1.5 bg-primary rounded-full" aria-hidden="true" />
                <span className="text-sm text-foreground">AI-powered quality gates at every checkpoint</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-1.5 h-1.5 bg-primary rounded-full" aria-hidden="true" />
                <span className="text-sm text-foreground">Fixed pricing, firm deadlines</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
