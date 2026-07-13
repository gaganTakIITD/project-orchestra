"use client";

import { motion, useInView } from "framer-motion";
import { useRef, memo } from "react";
import { springConfig, staggerContainer, staggerItem } from "@/lib/animations";
import { trustPoints } from "@/lib/data";

const TrustBand = memo(function TrustBand() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section
      className="bg-highlight text-highlight-foreground border-b border-border"
      ref={ref}
    >
      <div className="max-w-7xl mx-auto px-8 lg:px-12 py-24 lg:py-32">
        <motion.h2
          className="font-serif text-5xl sm:text-6xl lg:text-7xl font-semibold tracking-[-0.03em] leading-[0.98] max-w-4xl mb-20 text-balance"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={springConfig.scrollReveal}
        >
          Built on trust, backed by proof.
        </motion.h2>

        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-6 lg:gap-8"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={staggerContainer}
        >
          {trustPoints.map((point) => (
            <motion.div
              key={point.label}
              className="flex flex-col bg-card text-card-foreground p-8"
              variants={staggerItem}
            >
              <h3 className="text-lg font-serif font-medium tracking-[-0.01em] mb-6">
                {point.title}
              </h3>
              <div className="border-t border-border pt-6 mb-8">
                <span className="font-serif text-6xl font-semibold tracking-[-0.03em] leading-none text-foreground">
                  {point.label}
                </span>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed mt-auto">
                {point.description}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
});

TrustBand.displayName = "TrustBand";

export default TrustBand;
