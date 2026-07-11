'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'framer-motion';
import { useRef } from 'react';
import { staggerContainer, staggerItem } from '@/lib/animations';

const faqs = [
  {
    question: "How long does an outcome take?",
    answer:
      "Depends on complexity. Our SKUs range from 7–21 days. Once you confirm the spec, we give you a firm deadline. The orchestrator manages every day.",
  },
  {
    question: "What if I need changes mid-way?",
    answer:
      "You can request amendments anytime. We re-spec, re-price, and get approval before executing changes. Everything stays tracked and transparent.",
  },
  {
    question: "Who owns the final deliverables?",
    answer:
      "You do. 100% rights transfer to you on delivery. No royalties, no strings. The work is yours.",
  },
  {
    question: "What if the result doesn't meet expectations?",
    answer:
      "We rework it or refund you. Our QA gates check every deliverable against your acceptance criteria before it ships. If something doesn't match spec, we fix it.",
  },
  {
    question: "How are workers paid?",
    answer:
      "Fairly, and on time. Payouts are triggered when each task passes QA. We handle all tax compliance and transfers.",
  },
  {
    question: "Why IIT Delhi talent?",
    answer:
      "Our founders and core team are from IIT Delhi. We trust the community. Every worker is campus-verified—no fakes, no resume inflation.",
  },
];

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
          {faqs.map((faq, idx) => (
            <motion.div key={idx} variants={staggerItem}>
              <button
                onClick={() => setOpenIdx(openIdx === idx ? null : idx)}
                className="w-full py-6 flex items-start justify-between text-left hover:text-primary transition-colors"
                aria-expanded={openIdx === idx}
              >
                <span className="text-base font-semibold text-foreground pr-4">{faq.question}</span>
                <motion.div
                  animate={{ rotate: openIdx === idx ? 180 : 0 }}
                  transition={{ duration: 0.3 }}
                  className="flex-shrink-0 mt-0.5"
                >
                  <ChevronDown
                    className="w-4 h-4 text-muted-foreground"
                    aria-hidden="true"
                  />
                </motion.div>
              </button>

              <AnimatePresence>
                {openIdx === idx && (
                  <motion.div
                    className="pb-6"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <p className="text-sm text-muted-foreground leading-relaxed">
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
