const trustPoints = [
  {
    label: "01",
    title: "Campus-verified talent",
    description: "Every worker is verified as a student or recent alumni of IIT Delhi. Real credentials, real skills—not resume inflation.",
  },
  {
    label: "02",
    title: "AI-verified quality",
    description: "Gemini vision and reasoning models check every milestone against your acceptance criteria before it ships to you.",
  },
  {
    label: "03",
    title: "Outcome guarantee",
    description: "We rework or reimburse if your outcome doesn't meet spec. No fine print. Your result is guaranteed.",
  },
];

export default function TrustBand() {
  return (
    <section className="bg-card border-b border-border">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">

        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">Built on trust</h2>
          <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
            Three non-negotiable pillars behind every outcome we deliver.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 border border-border divide-y md:divide-y-0 md:divide-x divide-border">
          {trustPoints.map((point) => (
            <div key={point.label} className="p-8 flex flex-col gap-4">
              <span className="text-3xl font-bold font-mono text-primary">{point.label}</span>
              <h3 className="text-base font-semibold">{point.title}</h3>
              <p className="text-sm text-muted-foreground leading-relaxed">{point.description}</p>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
