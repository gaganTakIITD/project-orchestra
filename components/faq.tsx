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
    <section id="faq" className="border-b-4 border-foreground" ref={ref}>
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">

        <motion.div 
          className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-16"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Frequently asked</h2>
          <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
            Everything you need to know about how Orchestra works.
          </p>
        </motion.div>

        <motion.div 
          className="max-w-3xl border-2 border-foreground divide-y-2 divide-foreground"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={staggerContainer}
        >
          {faqs.map((faq, idx) => (
            <motion.div key={idx} variants={staggerItem}>
              <button
                onClick={() => setOpenIdx(openIdx === idx ? null : idx)}
                className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-muted transition-colors"
                aria-expanded={openIdx === idx}
              >
                <span className="font-bold text-sm pr-4 text-foreground">{faq.question}</span>
                <motion.div
                  animate={{ rotate: openIdx === idx ? 180 : 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <ChevronDown
                    className="w-4 h-4 text-foreground flex-shrink-0"
                    aria-hidden="true"
                  />
                </motion.div>
              </button>

              <AnimatePresence>
                {openIdx === idx && (
                  <motion.div
                    className="px-6 pb-5 border-t-2 border-foreground bg-muted"
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: "auto" }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <p className="text-sm text-foreground leading-relaxed pt-4 font-mono">
                      {faq.answer}
                    </p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </motion.div>

        <motion.div 
          className="mt-10 border-2 border-foreground p-8 max-w-3xl"
          initial={{ opacity: 0, y: 20 }}
          animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          whileHover={{ scale: 1.01 }}
        >
          <p className="text-sm text-foreground mb-2 font-bold">Still have questions?</p>
          <motion.a
            href="mailto:hello@orchestrapro.com"
            className="text-sm font-bold text-primary hover:text-accent transition-colors inline-block"
            whileHover={{ x: 4 }}
          >
            hello@orchestrapro.com
          </motion.a>
        </motion.div>

      </div>
    </section>
  );
}
