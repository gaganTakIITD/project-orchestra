"use client";

import { useSkus } from "@/lib/hooks";
import Link from "next/link";
import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { staggerContainer, staggerItem } from "@/lib/animations";

export default function OutcomeCatalog() {
  const { data: skus, isLoading } = useSkus();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section id="outcomes" className="border-b-4 border-foreground" ref={ref}>
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">

        <motion.div 
          className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Our outcomes</h2>
          <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
            Choose from proven outcome packages, or describe your own and we&apos;ll price it.
          </p>
        </motion.div>

        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 border-2 border-foreground divide-y-2 md:divide-y-0 md:divide-x-2 divide-foreground"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={staggerContainer}
        >
          {isLoading
            ? Array.from({ length: 3 }).map((_, idx) => (
                <div key={idx} className="p-8 animate-pulse flex flex-col gap-4">
                  <div className="h-5 bg-muted w-2/3" />
                  <div className="h-4 bg-muted w-full" />
                  <div className="h-4 bg-muted w-5/6" />
                  <div className="h-8 bg-muted w-1/3 mt-4" />
                </div>
              ))
            : skus && skus.length > 0
            ? skus.map((sku) => (
                <motion.div 
                  key={sku.id} 
                  className="p-8 flex flex-col gap-5 hover:bg-muted transition-colors border-r border-foreground last:border-r-0"
                  variants={staggerItem}
                  whileHover={{ y: -4 }}
                >
                  <div>
                    <h3 className="text-base font-bold mb-2 text-foreground">{sku.name}</h3>
                    <p className="text-sm text-foreground leading-relaxed line-clamp-3 font-mono opacity-90">
                      {sku.description}
                    </p>
                  </div>
                  <div className="flex items-baseline gap-3 mt-auto">
                    <span className="text-3xl font-bold text-primary font-mono">
                      ₹{sku.base_price.toLocaleString("en-IN")}
                    </span>
                    <span className="text-xs font-mono tracking-widest uppercase text-foreground opacity-70">
                      ~{sku.typical_days} days
                    </span>
                  </div>
                  <motion.div whileHover={{ scale: 1.04 }} whileTap={{ scale: 0.98 }}>
                    <Link
                      href="/start"
                      className="inline-flex items-center h-9 px-5 border-2 border-primary text-primary text-xs font-mono tracking-widest uppercase hover:bg-primary hover:text-primary-foreground transition-colors self-start font-bold"
                    >
                      Start outcome
                    </Link>
                  </motion.div>
                </motion.div>
              ))
            : (
                <div className="col-span-full p-12 text-center">
                  <p className="text-sm text-foreground font-mono">
                    No outcomes yet. Describe your own at{" "}
                    <Link href="/start" className="text-primary hover:text-accent underline font-bold">
                      /start
                    </Link>.
                  </p>
                </div>
              )}
        </div>

        <div className="mt-10 flex justify-end">
          <Link
            href="/start"
            className="inline-flex items-center h-11 px-8 border border-border text-foreground text-sm font-semibold hover:bg-card transition-colors"
          >
            Describe a custom outcome
          </Link>
        </div>

      </div>
    </section>
  );
}
