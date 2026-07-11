'use client';

import { CheckCircle2, X } from 'lucide-react';

const comparison = [
  { feature: 'Single point of accountability', orchestra: true, freelancer: false },
  { feature: 'AI-driven planning & handoffs', orchestra: true, freelancer: false },
  { feature: 'Quality gates on every milestone', orchestra: true, freelancer: false },
  { feature: 'Live progress tracking', orchestra: true, freelancer: false },
  { feature: 'Fixed price & deadline', orchestra: true, freelancer: false },
  { feature: 'Verified campus talent', orchestra: true, freelancer: false },
  { feature: 'No context-switch delays', orchestra: true, freelancer: false },
  { feature: 'All rights to deliverables included', orchestra: true, freelancer: false },
];

export default function WhyOrchestra() {
  return (
    <section id="why-orchestra" className="py-20 sm:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-4">
            Buy an outcome, not a freelancer
          </h2>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Orchestra is different from hiring freelancers on a marketplace. We orchestrate the work end-to-end.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-4 px-4 font-semibold">Feature</th>
                <th className="text-center py-4 px-4 font-semibold">Orchestra</th>
                <th className="text-center py-4 px-4 font-semibold">Freelancer marketplace</th>
              </tr>
            </thead>
            <tbody>
              {comparison.map((row, idx) => (
                <tr key={idx} className="border-b border-border hover:bg-card/50 transition">
                  <td className="py-4 px-4 font-medium">{row.feature}</td>
                  <td className="py-4 px-4 text-center">
                    {row.orchestra ? (
                      <CheckCircle2 className="w-5 h-5 text-primary mx-auto" />
                    ) : (
                      <X className="w-5 h-5 text-muted-foreground mx-auto" />
                    )}
                  </td>
                  <td className="py-4 px-4 text-center">
                    {row.freelancer ? (
                      <CheckCircle2 className="w-5 h-5 text-primary mx-auto" />
                    ) : (
                      <X className="w-5 h-5 text-muted-foreground mx-auto" />
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
