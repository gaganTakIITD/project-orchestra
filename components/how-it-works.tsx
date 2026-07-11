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
    <section id="how" className="border-b-4 border-foreground bg-background" ref={ref}>
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-16 lg:py-24">

        <motion.div 
          className="mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight mb-4 text-foreground">
            How it works
          </h2>
          <div className="w-16 h-2 bg-accent mb-8" aria-hidden="true" />
          <p className="text-base text-foreground max-w-lg leading-relaxed font-mono">
            Four steps from brief to delivery. No hand-off chaos, no quality surprises.
          </p>
        </motion.div>

        <motion.div 
          className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-0 border-2 border-foreground divide-x-2 divide-y-2 divide-foreground"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={staggerContainer}
        >
          {steps.map((step, idx) => (
            <motion.div 
              key={step.number} 
              className={`p-8 lg:p-10 flex flex-col justify-start gap-6 ${
                idx % 2 === 0 ? 'bg-background' : 'bg-muted'
              }`}
              variants={staggerItem}
              whileHover={{ y: -4 }}
            >
              <motion.span 
                className="text-6xl lg:text-7xl font-bold text-primary font-mono leading-none"
                whileHover={{ scale: 1.05 }}
              >
                {step.number}
              </motion.span>
              <div>
                <h3 className="text-lg lg:text-xl font-bold mb-3 text-foreground uppercase tracking-wide">
                  {step.title}
                </h3>
                <p className="text-sm lg:text-base text-foreground leading-relaxed font-mono opacity-90">
                  {step.description}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>

      </div>
    </section>
  );
}
