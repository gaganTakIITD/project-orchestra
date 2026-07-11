import Link from "next/link";

const clientPoints = [
  "No project management—we handle every detail",
  "Live progress tracking from brief to delivery",
  "Fixed price with no surprises",
  "Quality gates verified by AI before delivery",
];

const talentPoints = [
  "Pre-verified outcomes—no bad-faith clients",
  "Fair skill-based matching on every project",
  "Clear specs and acceptance criteria upfront",
  "Competitive payouts triggered on approval",
];

export default function AudienceSplit() {
  return (
    <section className="border-b border-border">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
        <div className="grid grid-cols-1 lg:grid-cols-2 border border-border divide-y lg:divide-y-0 lg:divide-x divide-border">

          {/* For Clients */}
          <div className="p-8 lg:p-12 flex flex-col gap-6">
            <p className="text-xs font-mono tracking-widest uppercase text-primary">For clients</p>
            <h3 className="text-2xl font-bold tracking-tight">
              Stop managing freelancers.<br />Get the outcome.
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Describe what you need and let our AI general contractor orchestrate a verified team to deliver it end-to-end—on time, on budget, quality guaranteed.
            </p>
            <ul className="flex flex-col gap-3">
              {clientPoints.map((p) => (
                <li key={p} className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-primary flex-shrink-0 mt-1.5" aria-hidden="true" />
                  <span className="text-sm">{p}</span>
                </li>
              ))}
            </ul>
            <Link
              href="/start"
              className="inline-flex items-center h-11 px-8 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity self-start mt-2"
            >
              Start your outcome
            </Link>
          </div>

          {/* For Talent */}
          <div className="p-8 lg:p-12 flex flex-col gap-6">
            <p className="text-xs font-mono tracking-widest uppercase text-primary">For talent</p>
            <h3 className="text-2xl font-bold tracking-tight">
              IIT Delhi builders:<br />get matched to real work.
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Join our verified community. Get matched to real outcomes, work with quality clients, build your portfolio, and earn competitive payouts—without the hustle of a freelance marketplace.
            </p>
            <ul className="flex flex-col gap-3">
              {talentPoints.map((p) => (
                <li key={p} className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-primary flex-shrink-0 mt-1.5" aria-hidden="true" />
                  <span className="text-sm">{p}</span>
                </li>
              ))}
            </ul>
            <Link
              href="/join"
              className="inline-flex items-center h-11 px-8 border border-border text-foreground text-sm font-semibold hover:bg-card transition-colors self-start mt-2"
            >
              Apply to join
            </Link>
          </div>

        </div>
      </div>
    </section>
  );
}
