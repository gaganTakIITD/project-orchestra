'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

const faqs = [
  {
    question: 'How does the unlimited design requests work?',
    answer: 'You can submit as many design tasks as you need each month. There\'s no per-task billing or waiting list. Our designers prioritize your requests based on complexity and timeline.',
  },
  {
    question: 'What if I don\'t like the design?',
    answer: 'We offer unlimited revisions until you\'re completely satisfied. Your designer will work with you iteratively to ensure the final product exceeds your expectations.',
  },
  {
    question: 'Can I pause or cancel my subscription?',
    answer: 'Yes, absolutely. You can pause your subscription at any time, and there are no long-term contracts. You can resume or cancel whenever you need to.',
  },
  {
    question: 'How does UMANO integrate with my tools?',
    answer: 'We integrate with Slack, Jira, Notion, Figma, Linear, and more. Your designer can receive tasks directly through your preferred platforms and collaborate seamlessly.',
  },
  {
    question: 'What if I need more design capacity?',
    answer: 'We offer flexible scaling. You can upgrade to have multiple dedicated designers or increase your monthly task capacity based on your growing needs.',
  },
  {
    question: 'How long does onboarding take?',
    answer: 'Onboarding typically takes 3-5 days. We\'ll assign a dedicated designer, understand your brand, and get them fully integrated into your workflow.',
  },
];

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState(0);

  return (
    <section className="w-full py-20 md:py-32 bg-background">
      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="mb-16 text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Frequently asked questions
          </h2>
          <p className="text-lg text-muted-foreground">
            Have other questions? Reach out to our team and we&apos;ll be happy to help.
          </p>
        </div>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="border border-border rounded-lg overflow-hidden hover:border-primary transition-colors"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? -1 : index)}
                className="w-full px-6 py-4 flex items-center justify-between bg-card hover:bg-muted transition-colors text-left"
              >
                <span className="font-semibold text-foreground">{faq.question}</span>
                <ChevronDown
                  className={`w-5 h-5 text-muted-foreground transition-transform flex-shrink-0 ${
                    openIndex === index ? 'transform rotate-180' : ''
                  }`}
                />
              </button>

              {openIndex === index && (
                <div className="px-6 py-4 bg-muted/50 border-t border-border">
                  <p className="text-muted-foreground leading-relaxed">{faq.answer}</p>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Support CTA */}
        <div className="mt-12 p-8 rounded-2xl bg-muted text-center">
          <h3 className="text-xl font-bold mb-2">Still have questions?</h3>
          <p className="text-muted-foreground mb-4">
            Our team is here to help. Get in touch and we&apos;ll answer any questions you have.
          </p>
          <button className="px-6 py-2 bg-primary text-primary-foreground rounded-full font-medium hover:opacity-90 transition-opacity">
            Contact us
          </button>
        </div>
      </div>
    </section>
  );
}
