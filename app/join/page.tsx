import Link from "next/link";
import Header from "@/components/header";
import Footer from "@/components/footer";

export const metadata = {
  title: "Join as talent — Project Orchestra",
  description:
    "IIT Delhi designers and developers: apply to join our verified talent community and get matched to real digital outcomes.",
};

export default function JoinPage() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          <p className="text-xs font-mono tracking-widest uppercase text-primary mb-8">
            For talent
          </p>

          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-none text-balance mb-6">
            Apply to join Orchestra.
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed mb-10 max-w-xl">
            We verify every member as a student or recent alumni of IIT Delhi. Once live,
            you get matched to scoped outcomes with clear specs, fair pay, and no bad-faith clients.
          </p>

          <div className="flex flex-wrap gap-3 mb-16">
            <Link
              href="/worker/onboarding"
              className="inline-flex items-center justify-center h-11 px-8 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              Start onboarding →
            </Link>
            <Link
              href="/worker"
              className="inline-flex items-center justify-center h-11 px-8 border border-border text-sm font-semibold hover:border-primary transition-colors"
            >
              Open worker inbox
            </Link>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
            <div className="border border-border p-8 flex flex-col gap-6">
              <h2 className="text-base font-semibold">Why join Orchestra</h2>
              {[
                {
                  n: "01",
                  title: "Pre-vetted outcomes only",
                  body: "Every project is scoped and priced before you touch it.",
                },
                {
                  n: "02",
                  title: "Clear specs upfront",
                  body: "You receive a Charter + TaskPacket job card before you start.",
                },
                {
                  n: "03",
                  title: "Payouts on delivery",
                  body: "Payments trigger when work passes the quality gate.",
                },
                {
                  n: "04",
                  title: "Verified portfolio",
                  body: "Completed outcomes become credentials on your Orchestra profile.",
                },
              ].map((item) => (
                <div key={item.n} className="flex gap-5">
                  <span className="text-xl font-bold font-mono text-primary flex-shrink-0 w-8">
                    {item.n}
                  </span>
                  <div>
                    <p className="text-sm font-semibold mb-1">{item.title}</p>
                    <p className="text-sm text-muted-foreground leading-relaxed">{item.body}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="border border-border p-6 h-fit">
              <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-3">
                Eligibility
              </p>
              <p className="text-sm text-muted-foreground leading-relaxed mb-6">
                Currently open to students and recent alumni (graduated within 3 years) of IIT Delhi.
              </p>
              <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-3">
                How it works
              </p>
              <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
                <li>Complete onboarding (≥70% profile)</li>
                <li>Browse invited tasks in your inbox</li>
                <li>Open the job card — Charter + checklist</li>
                <li>Submit work, pass QA, get paid</li>
              </ol>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
