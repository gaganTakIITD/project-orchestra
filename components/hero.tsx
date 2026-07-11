import Link from "next/link";

const trustMarkers = [
  "Campus-verified IIT Delhi talent",
  "AI-verified quality gates",
  "Fixed price, clear deadline",
];

export default function Hero() {
  return (
    <section className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 pt-20 pb-16 lg:pt-28 lg:pb-24">

        <p className="text-xs font-mono tracking-widest uppercase text-primary mb-8">
          AI-native Outcome-as-a-Service
        </p>

        <h1 className="text-5xl sm:text-6xl lg:text-8xl font-bold tracking-tight leading-none text-balance mb-10">
          Tell us the result.<br />
          <span className="text-primary">We deliver it.</span>
        </h1>

        <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-8">
          <p className="text-lg text-muted-foreground max-w-xl leading-relaxed">
            Describe the digital outcome you need—brand, landing page, or app feature. Our AI general contractor plans, staffs with verified IIT Delhi talent, verifies every handoff, and ships the finished result.
          </p>

          <div className="flex flex-col sm:flex-row gap-3 flex-shrink-0">
            <Link
              href="/start"
              className="inline-flex items-center justify-center h-11 px-8 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              Describe your outcome
            </Link>
            <Link
              href="/join"
              className="inline-flex items-center justify-center h-11 px-8 border border-border text-foreground text-sm font-semibold hover:bg-card transition-colors"
            >
              Join as talent
            </Link>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-border flex flex-wrap gap-x-10 gap-y-4">
          {trustMarkers.map((m) => (
            <div key={m} className="flex items-center gap-3">
              <div className="w-2 h-2 bg-primary flex-shrink-0" aria-hidden="true" />
              <span className="text-xs font-mono tracking-widest uppercase text-muted-foreground">{m}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
