'use client';

import { Award, Shield, Zap } from 'lucide-react';

const trustPoints = [
  {
    icon: Award,
    title: "Campus-verified talent",
    description: "Every worker is verified as a student or recent alumni of IIT Delhi. Real credentials, real skills.",
  },
  {
    icon: Shield,
    title: "AI-verified quality",
    description: "Gemini vision and reasoning models verify every milestone against acceptance criteria before delivery.",
  },
  {
    icon: Zap,
    title: "Outcome guarantee",
    description: "We reimburse or rework if your outcome doesn't meet spec. Your satisfaction, guaranteed.",
  },
];

export default function TrustBand() {
  return (
    <section className="py-20 sm:py-32 bg-primary/5 border-y border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">Built on trust</h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            How we ensure quality, accountability, and satisfaction on every outcome.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {trustPoints.map((point, idx) => {
            const Icon = point.icon;
            return (
              <div key={idx} className="text-center">
                <div className="flex justify-center mb-4">
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center">
                    <Icon className="w-8 h-8 text-primary" />
                  </div>
                </div>
                <h3 className="text-lg font-semibold mb-2">{point.title}</h3>
                <p className="text-muted-foreground leading-relaxed">
                  {point.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
