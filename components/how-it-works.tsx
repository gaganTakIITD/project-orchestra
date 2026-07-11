const steps = [
  {
    number: "01",
    title: "Describe",
    description: "Tell us what you need—brand identity, landing page, app feature, or any digital outcome. Plain English is fine.",
  },
  {
    number: "02",
    title: "Confirm",
    description: "Our AI specs out the work. You review the plan, deliverables, acceptance criteria, and fixed price before a single task starts.",
  },
  {
    number: "03",
    title: "Watch",
    description: "Verified IIT Delhi talent executes in parallel. Live milestone tracking and a scoped chat panel—full visibility, zero meetings.",
  },
  {
    number: "04",
    title: "Receive",
    description: "AI-verified deliverables arrive on time. You accept, and the outcome is yours—100% rights included.",
  },
];

export default function HowItWorks() {
  return (
    <section id="how" className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">

        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4 mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">How it works</h2>
          <p className="text-sm text-muted-foreground max-w-sm leading-relaxed">
            Four steps from brief to delivery. No hand-off chaos, no quality surprises.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 border border-border divide-y sm:divide-y-0 sm:divide-x divide-border">
          {steps.map((step) => (
            <div key={step.number} className="p-8 flex flex-col gap-5">
              <span className="text-5xl font-bold text-primary font-mono leading-none">{step.number}</span>
              <div>
                <h3 className="text-base font-semibold mb-2">{step.title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{step.description}</p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
}
