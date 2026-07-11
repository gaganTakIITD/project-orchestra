'use client';

import { useState, memo } from 'react';
import { ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef } from 'react';
import { staggerContainer, staggerItem, springConfig } from '@/lib/animations';
import { faqItems } from '@/lib/data';

export default function FAQ() {
  const [openIdx, setOpenIdx] = useState<number | null>(0);
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section id="faq" className="bg-background" ref={ref}>
      <div className="max-w-6xl mx-auto px-8 lg:px-12 py-32 lg:py-48">

        <motion.div 
          className="mb-20"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.9 }}
        >
          <h2 className="font-serif text-6xl sm:text-7xl lg:text-8xl font-bold text-foreground mb-8">Questions</h2>
          <p className="text-lg text-muted-foreground max-w-3xl">
            Everything you need to know about how we work.
          </p>
        </motion.div>

        <motion.div 
          className="max-w-3xl space-y-0 divide-y divide-border"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={staggerContainer}
        >
          {faqItems.map((faq, idx) => (
            <motion.div key={idx} variants={staggerItem}>
              <motion.button
                onClick={() => setOpenIdx(openIdx === idx ? null : idx)}
                className="w-full py-6 flex items-start justify-between text-left hover:text-primary transition-colors group"
                aria-expanded={openIdx === idx}
                whileHover={{ x: 4 }}
                transition={{ type: "spring", stiffness: 200 }}
              >
                <span className="text-base font-semibold text-foreground pr-4 group-hover:text-primary transition-colors">
                  {faq.question}
                </span>
                <motion.div
                  animate={{ rotate: openIdx === idx ? 180 : 0 }}
                  transition={springConfig.accordion}
                  className="flex-shrink-0 mt-0.5"
                >
                  <ChevronDown
                    className="w-4 h-4 text-muted-foreground group-hover:text-primary transition-colors"
                    aria-hidden="true"
                  />
                </motion.div>
              </motion.button>

              <AnimatePresence mode="wait">
                {openIdx === idx && (
                  <motion.div
                    className="pb-6"
                    initial={{ opacity: 0, height: 0, marginBottom: 0 }}
                    animate={{ opacity: 1, height: "auto", marginBottom: 16 }}
                    exit={{ opacity: 0, height: 0, marginBottom: 0 }}
                    transition={springConfig.accordion}
                  >
                    <p className="text-sm text-muted-foreground leading-relaxed pt-2">
                      {faq.answer}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </motion.div>

        <motion.div 
          className="mt-20 pt-12 border-t border-border"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.9, delay: 0.2 }}
        >
          <p className="text-sm text-muted-foreground mb-3">Still have questions?</p>
          <motion.a
            href="mailto:hello@orchestrapro.com"
            className="text-base font-semibold text-primary hover:text-accent transition-colors inline-block"
            whileHover={{ x: 4 }}
          >
            hello@orchestrapro.com
          </motion.a>
        </motion.div>

      </div>
    </section>
  );
}
