'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

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

  return (
    <section id="faq" className="py-20 sm:py-32">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">Frequently asked</h2>
          <p className="text-lg text-muted-foreground">
            Everything you need to know about how Orchestra works.
          </p>
        </div>

        <div className="space-y-3">
          {faqs.map((faq, idx) => (
            <div
              key={idx}
              className="border border-border rounded-lg overflow-hidden"
            >
              <button
                onClick={() => setOpenIdx(openIdx === idx ? null : idx)}
                className="w-full px-6 py-4 flex items-center justify-between bg-card hover:bg-muted transition text-left"
              >
                <span className="font-semibold">{faq.question}</span>
                <ChevronDown
                  className={`w-5 h-5 text-muted-foreground transition-transform ${
                    openIdx === idx ? 'rotate-180' : ''
                  }`}
                />
              </button>

              {openIdx === idx && (
                <div className="px-6 py-4 bg-background border-t border-border">
                  <p className="text-muted-foreground leading-relaxed">
                    {faq.answer}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-12 p-6 bg-primary/5 border border-primary/20 rounded-lg text-center">
          <p className="text-muted-foreground mb-3">Still have questions?</p>
          <a
            href="mailto:hello@orchestrapro.com"
            className="text-primary font-medium hover:underline"
          >
            Contact us at hello@orchestrapro.com
          </a>
        </div>
      </div>
    </section>
  );
}
