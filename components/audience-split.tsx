'use client';

import Link from 'next/link';
import { ArrowRight, Lightbulb, TrendingUp } from 'lucide-react';

export default function AudienceSplit() {
  return (
    <section className="py-20 sm:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-8">
          {/* For Clients */}
          <div className="group">
            <div className="bg-card border border-border rounded-lg p-8 h-full flex flex-col hover:border-primary transition">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-6">
                <Lightbulb className="w-6 h-6 text-primary" />
              </div>

              <h3 className="text-2xl font-bold mb-3">For clients</h3>
              <p className="text-muted-foreground mb-6 flex-grow">
                Stop hiring freelancers for every project. Describe what you need and let our AI general contractor orchestrate a verified team to deliver it end-to-end—on time, on budget, quality guaranteed.
              </p>

              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm">No project management—we handle every detail</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm">Live progress tracking from brief to delivery</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm">Fixed price with no surprises</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm">Quality gates verified by AI</span>
                </li>
              </ul>

              <Link
                href="/start"
                className="inline-flex items-center gap-2 text-primary font-semibold hover:gap-3 transition"
              >
                Start your outcome
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>

          {/* For Talent */}
          <div className="group">
            <div className="bg-card border border-border rounded-lg p-8 h-full flex flex-col hover:border-primary transition">
              <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-6">
                <TrendingUp className="w-6 h-6 text-primary" />
              </div>

              <h3 className="text-2xl font-bold mb-3">For talent</h3>
              <p className="text-muted-foreground mb-6 flex-grow">
                Are you a designer or developer at IIT Delhi? Join our verified community. Get matched to real outcomes, work with quality clients, and build your portfolio while earning competitive payouts—all without the hustle of a freelance marketplace.
              </p>

              <ul className="space-y-3 mb-8">
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm">Pre-verified outcomes—no bad clients</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm">Fair matching based on your skills</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm">Clear specs and criteria upfront</span>
                </li>
                <li className="flex items-start gap-3">
                  <div className="w-1.5 h-1.5 bg-primary rounded-full mt-2 flex-shrink-0" />
                  <span className="text-sm">Competitive payouts on every delivery</span>
                </li>
              </ul>

              <Link
                href="/join"
                className="inline-flex items-center gap-2 text-primary font-semibold hover:gap-3 transition"
              >
                Apply to join
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
