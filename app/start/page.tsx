import Header from "@/components/header";
import Footer from "@/components/footer";
import IntentForm from "@/components/intent-form";

export const metadata = {
  title: "Describe your outcome — Project Orchestra",
  description:
    "Tell us the digital result you need. Our AI general contractor will spec it, staff it with verified IIT Delhi talent, and deliver it.",
};

export default function StartPage() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-20 lg:py-28">

          {/* Label */}
          <p className="text-xs font-mono tracking-widest uppercase text-primary mb-8">
            For clients
          </p>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-none text-balance mb-10">
            Describe your outcome.
          </h1>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-24">

            {/* Form side */}
            <div>
              <p className="text-sm text-muted-foreground leading-relaxed mb-10">
                Tell us what you need in plain English. Our AI will turn it into a scoped plan with deliverables, acceptance criteria, and a fixed price—before any work begins.
              </p>

              <IntentForm />
            </div>

            {/* What happens next */}
            <div className="border border-border p-8 self-start flex flex-col gap-8">
              <h2 className="text-base font-semibold">What happens next</h2>
              <div className="flex flex-col gap-6">
                {[
                  { n: "01", title: "We receive your brief", body: "Your description lands with our AI orchestrator, which begins mapping deliverables and acceptance criteria." },
                  { n: "02", title: "You get a scoped plan", body: "Within 24 hours: full scope, fixed price, firm deadline. No surprises, no scope creep." },
                  { n: "03", title: "You approve & we staff", body: "Once you confirm, we match verified IIT Delhi talent to each task. Work begins immediately." },
                  { n: "04", title: "You receive the outcome", body: "Every milestone is AI-verified before delivery. You accept, and the work is 100% yours." },
                ].map((step) => (
                  <div key={step.n} className="flex gap-5">
                    <span className="text-xl font-bold font-mono text-primary flex-shrink-0 w-8">{step.n}</span>
                    <div>
                      <p className="text-sm font-semibold mb-1">{step.title}</p>
                      <p className="text-sm text-muted-foreground leading-relaxed">{step.body}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
