const rows = [
  "Single point of accountability",
  "AI-driven planning & task handoffs",
  "Quality gates on every milestone",
  "Live progress tracking",
  "Fixed price & firm deadline",
  "Campus-verified IIT Delhi talent",
  "No context-switch delays",
  "100% rights to all deliverables",
];

export default function WhyOrchestra() {
  return (
    <section className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">

        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
            Buy an outcome,<br className="hidden sm:block" /> not a freelancer
          </h2>
          <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
            Orchestrating end-to-end is fundamentally different from a freelancer directory.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-3 pr-8 font-mono text-xs tracking-widest uppercase text-muted-foreground w-full">Feature</th>
                <th className="py-3 px-8 font-mono text-xs tracking-widest uppercase text-foreground whitespace-nowrap">Orchestra</th>
                <th className="py-3 px-8 font-mono text-xs tracking-widest uppercase text-muted-foreground whitespace-nowrap">Freelancer marketplace</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((feature) => (
                <tr key={feature} className="border-b border-border hover:bg-card transition-colors">
                  <td className="py-4 pr-8 font-medium">{feature}</td>
                  <td className="py-4 px-8 text-center">
                    <div className="w-4 h-4 bg-primary mx-auto" aria-label="Yes" />
                  </td>
                  <td className="py-4 px-8 text-center">
                    <div className="w-4 h-px bg-muted-foreground mx-auto" aria-label="No" />
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
