import Link from "next/link";

const trustMarkers = [
  "Campus-verified IIT Delhi talent",
  "AI-verified quality gates",
  "Fixed price, clear deadline",
];

export default function Hero() {
  return (
    <section className="border-b-4 border-foreground">
      <div className="grid grid-cols-1 lg:grid-cols-2">
        {/* Left: Bold red accent block with primary CTA */}
        <div className="bg-primary px-8 lg:px-12 py-20 lg:py-32 flex flex-col justify-between">
          <div>
            <p className="text-xs font-mono tracking-widest uppercase text-primary-foreground opacity-80 mb-6 font-semibold">
              The outcome platform
            </p>
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight leading-tight text-primary-foreground mb-8">
              Tell us the result.
            </h1>
            <p className="text-base lg:text-lg text-primary-foreground opacity-90 max-w-md leading-relaxed mb-12 font-mono">
              Describe your digital outcome. We plan, staff, verify, and ship it. Powered by AI + verified talent.
            </p>
          </div>
          <Link
            href="/start"
            className="inline-flex items-center justify-center h-12 px-8 bg-accent text-accent-foreground text-sm font-bold uppercase tracking-wide hover:opacity-80 transition-opacity w-fit border-2 border-accent-foreground"
          >
            Describe outcome
          </Link>
        </div>

        {/* Right: White block with secondary CTA and trust markers */}
        <div className="bg-background px-8 lg:px-12 py-20 lg:py-32 flex flex-col justify-between border-l-4 border-foreground">
          <div>
            <div className="mb-12">
              <p className="text-xs font-mono tracking-widest uppercase text-foreground font-bold mb-2">
                Or
              </p>
              <Link
                href="/join"
                className="inline-flex items-center justify-center h-12 px-6 border-4 border-foreground text-foreground text-sm font-bold uppercase tracking-wide hover:bg-foreground hover:text-background transition-colors w-fit"
              >
                Join as talent
              </Link>
            </div>

            <div className="border-t-2 border-foreground pt-8">
              <p className="text-xs font-mono tracking-widest uppercase text-foreground font-bold mb-6">
                Why we win
              </p>
              <div className="space-y-4">
                {trustMarkers.map((m) => (
                  <div key={m} className="flex items-start gap-4">
                    <div className="w-3 h-3 bg-accent flex-shrink-0 mt-2" aria-hidden="true" />
                    <span className="text-sm font-mono text-foreground leading-snug">{m}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
