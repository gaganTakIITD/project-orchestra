"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef, memo } from "react";
import { staggerContainer, staggerItem, springConfig } from "@/lib/animations";
import { steps } from "@/lib/data";

const HowItWorks = memo(function HowItWorks() {
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
            How it works
          </h2>
          <p className="text-lg text-muted-foreground max-w-3xl leading-relaxed">
            Four transparent steps from brief to delivery.
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
              className="bg-secondary rounded-sm p-8 border border-transparent hover:border-primary/20"
              variants={staggerItem}
              whileHover={{ 
                y: -6,
                boxShadow: "0 20px 25px -5px rgba(0, 0, 0, 0.1)",
                transition: springConfig.hover
              }}
              initial={{ boxShadow: "0 1px 3px rgba(0, 0, 0, 0.05)" }}
            >
              <div className="flex items-start gap-4 mb-4">
                <motion.span 
                  className="font-serif text-4xl font-bold text-primary leading-none flex-shrink-0"
                  initial={{ scale: 0.9, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  transition={{ ...springConfig.scrollReveal, delay: 0.1 }}
                  whileHover={{ scale: 1.1 }}
                >
                  {step.number}
                </motion.span>
                <h3 className="text-lg font-bold text-secondary-foreground pt-1">
                  {step.title}
                </h3>
              </div>
              <p className="text-sm text-secondary-foreground/80 leading-relaxed">
                {step.description}
              </p>
            </motion.div>
          ))}
        </motion.div>

      </div>
    </section>
  );
});

HowItWorks.displayName = "HowItWorks";

export default HowItWorks;
