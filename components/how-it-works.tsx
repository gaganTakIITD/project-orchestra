"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";
import { staggerContainer, staggerItem } from "@/lib/animations";

const steps = [
  {
    number: "01",
    title: "Describe",
    description: "Tell us what you need—brand identity, landing page, app feature, or any digital outcome. Plain English is fine.",
  },
  {
    number: "02",
    title: "Confirm",
    description: "Our AI specs out the work. You review the plan, deliverables, acceptance criteria, and fixed price before a single task starts.",
  },
  {
    number: "03",
    title: "Watch",
    description: "Verified IIT Delhi talent executes in parallel. Live milestone tracking and a scoped chat panel—full visibility, zero meetings.",
  },
  {
    number: "04",
    title: "Receive",
    description: "AI-verified deliverables arrive on time. You accept, and the outcome is yours—100% rights included.",
  },
];

export default function HowItWorks() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section id="how" className="bg-background" ref={ref}>
      <div className="max-w-6xl mx-auto px-8 lg:px-12 py-32 lg:py-48">

        <motion.div 
          className="mb-20"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.9 }}
        >
          <h2 className="font-serif text-6xl sm:text-7xl lg:text-8xl font-bold text-foreground mb-8 leading-tight">
            The Process
          </h2>
          <div className="w-20 h-1 bg-accent mb-8" aria-hidden="true" />
          <p className="text-lg text-muted-foreground max-w-3xl leading-relaxed">
            From brief to delivery. Clear, transparent, outcome-focused at every step.
          </p>
        </motion.div>

        <motion.div 
          className="grid grid-cols-1 md:grid-cols-2 gap-12"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={staggerContainer}
        >
          {steps.map((step) => (
            <motion.div 
              key={step.number} 
              className="bg-secondary rounded-lg p-8 hover:border-accent border border-transparent transition-colors"
              variants={staggerItem}
              whileHover={{ y: -4 }}
            >
              <div className="flex items-start gap-6 mb-6">
                <span className="font-serif text-6xl font-bold text-primary leading-none flex-shrink-0">
                  {step.number}
                </span>
                <h3 className="text-2xl font-bold text-foreground pt-2">
                  {step.title}
                </h3>
              </div>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {step.description}
              </p>
            </motion.div>
          ))}
        </motion.div>

      </div>
    </section>
  );
}
