'use client';

import { FileText, CheckCircle2, Eye, Gift } from 'lucide-react';

const steps = [
  {
    number: 1,
    title: 'Describe',
    description: 'Tell us what you need—brand identity, landing page, app feature, or any digital outcome.',
    icon: FileText,
  },
  {
    number: 2,
    title: 'Confirm',
    description: 'Our AI specs out the work. You review the plan, deliverables, acceptance criteria, and price.',
    icon: CheckCircle2,
  },
  {
    number: 3,
    title: 'Watch',
    description: 'Verified talent executes in parallel. You see live progress, milestones, and can chat at every step.',
    icon: Eye,
  },
  {
    number: 4,
    title: 'Receive',
    description: 'AI-verified deliverables arrive on time. You accept, and the outcome is yours—all rights included.',
    icon: Gift,
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="py-20 sm:py-32 bg-card/50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">How it works</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Four simple steps from idea to delivered outcome. No freelancer hand-offs, no quality surprises.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div key={step.number} className="relative">
                {/* Connector line */}
                {idx < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-12 left-[60%] w-[calc(100%+1rem)] h-0.5 bg-border" />
                )}

                <div className="bg-background border border-border rounded-lg p-6 relative z-10">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center">
                      <Icon className="w-6 h-6 text-primary" />
                    </div>
                    <span className="text-2xl font-bold text-primary">{step.number}</span>
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{step.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{step.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
