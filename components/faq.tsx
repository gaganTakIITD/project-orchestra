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
    <section id="faq" className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">

        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Frequently asked</h2>
          <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
            Everything you need to know about how Orchestra works.
          </p>
        </div>

        <div className="max-w-3xl border border-border divide-y divide-border">
          {faqs.map((faq, idx) => (
            <div key={idx}>
              <button
                onClick={() => setOpenIdx(openIdx === idx ? null : idx)}
                className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-card transition-colors"
                aria-expanded={openIdx === idx}
              >
                <span className="font-semibold text-sm pr-4">{faq.question}</span>
                <ChevronDown
                  className={`w-4 h-4 text-muted-foreground flex-shrink-0 transition-transform duration-200 ${
                    openIdx === idx ? "rotate-180" : ""
                  }`}
                  aria-hidden="true"
                />
              </button>

              {openIdx === idx && (
                <div className="px-6 pb-5 border-t border-border bg-card">
                  <p className="text-sm text-muted-foreground leading-relaxed pt-4">
                    {faq.answer}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="mt-10 border border-border p-8 max-w-3xl">
          <p className="text-sm text-muted-foreground mb-2">Still have questions?</p>
          <a
            href="mailto:hello@orchestrapro.com"
            className="text-sm font-semibold text-primary hover:underline"
          >
            hello@orchestrapro.com
          </a>
        </div>

      </div>
    </section>
  );
}
