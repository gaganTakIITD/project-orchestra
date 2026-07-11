"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";

export default function Hero() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  // ASCII decoration pattern
  const AsciiPattern = () => (
    <div className="text-muted-foreground font-mono text-xs leading-tight select-none" aria-hidden="true">
      <div>{'> > > > > > > >'.split(' ').map((c, i) => <span key={i}>{c} </span>)}</div>
      <div className="mt-2">{'> > > > > >'.split(' ').map((c, i) => <span key={i}>{c} </span>)}</div>
      <div className="mt-2">{'> > > > > > > > >'.split(' ').map((c, i) => <span key={i}>{c} </span>)}</div>
      <div className="mt-4">{'> > > >'.split(' ').map((c, i) => <span key={i}>{c} </span>)}</div>
      <div className="mt-2">{'> > > > > > > >'.split(' ').map((c, i) => <span key={i}>{c} </span>)}</div>
    </div>
  );

  return (
    <section className="bg-background min-h-screen" ref={ref}>
      <div className="max-w-7xl mx-auto px-8 lg:px-12 py-24 lg:py-40">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-24 items-center">
          {/* Left: Content */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -30 }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          >
            <h1 className="font-serif text-6xl sm:text-7xl lg:text-8xl font-bold text-foreground leading-tight mb-8">
              Describe your outcome.
            </h1>
            <p className="text-lg text-muted-foreground max-w-lg leading-relaxed mb-12">
              We orchestrate the entire execution—planning, staffing, verification, and delivery. Backed by AI and verified talent.
            </p>

            {/* CTA Button - rounded dark teal */}
            <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.98 }} className="mb-16">
              <Link
                href="/start"
                className="inline-block px-8 py-3 bg-secondary text-secondary-foreground rounded-full font-semibold text-sm hover:opacity-85 transition-opacity duration-300"
              >
                Begin Project
              </Link>
            </motion.div>

            {/* Trust indicators */}
            <div className="space-y-3 text-sm">
              <p className="text-xs text-muted-foreground uppercase tracking-widest font-semibold mb-4">Backed by verified talent</p>
              <div className="flex items-center gap-3">
                <span className="w-1 h-1 bg-primary rounded-full" aria-hidden="true" />
                <span className="text-foreground">IIT Delhi campus-verified specialists</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-1 h-1 bg-primary rounded-full" aria-hidden="true" />
                <span className="text-foreground">AI-powered quality gates at every checkpoint</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-1 h-1 bg-primary rounded-full" aria-hidden="true" />
                <span className="text-foreground">Fixed pricing, firm deadlines</span>
              </div>
            </div>
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
