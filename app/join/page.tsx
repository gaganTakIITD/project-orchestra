import Link from "next/link";
import Header from "@/components/header";
import Footer from "@/components/footer";

export const metadata = {
  title: "Join as talent — Project Orchestra",
  description:
    "IIT Delhi designers and developers: build a matchable profile, get verified, and deliver scoped digital outcomes.",
};

const REQUIREMENTS = [
  {
    title: "Identity",
    body: "Name, craft headline, bio, and design / tech / both lane.",
  },
  {
    title: "Capabilities",
    body: "Skills, tools, and task types from Orchestra’s taxonomy — what matching actually uses.",
  },
  {
    title: "Proof",
    body: "At least one real project URL plus optional GitHub, Figma, Behance, LinkedIn.",
  },
  {
    title: "Capacity",
    body: "Availability, weekly hours, concurrent tasks, and preferred payout range.",
  },
];

export default function JoinPage() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1">
        <section className="border-b border-border">
          <div className="max-w-6xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-8">
              For talent
            </p>
            <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[0.95] max-w-3xl mb-6">
              Orchestra
            </h1>
            <p className="text-lg sm:text-xl text-foreground/80 max-w-xl mb-4 leading-relaxed">
              Apply once. Get matched to scoped outcomes — not open-ended freelance chats.
            </p>
            <p className="text-sm text-muted-foreground leading-relaxed mb-10 max-w-xl">
              We verify IIT Delhi students and recent alumni. Your profile is the job
              application: clear capabilities, proof of work, and honest capacity.
            </p>

            <div className="flex flex-wrap gap-3">
              <Link
                href="/worker/onboarding"
                className="inline-flex items-center justify-center h-11 px-8 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity"
              >
                Start profile →
              </Link>
              <Link
                href="/worker"
                className="inline-flex items-center justify-center h-11 px-8 border border-border text-sm font-semibold hover:border-primary transition-colors"
              >
                Open inbox
              </Link>
            </div>
          </div>
        </section>

        <section className="border-b border-border">
          <div className="max-w-6xl mx-auto px-6 lg:px-8 py-16 lg:py-20">
            <h2 className="text-xl font-semibold tracking-tight mb-2">
              What we collect — and why
            </h2>
            <p className="text-sm text-muted-foreground mb-10 max-w-xl">
              Matching is only as good as your profile. Reach{" "}
              <span className="text-foreground font-medium">70% completion</span> to go
              live and receive invites.
            </p>
            <ol className="grid grid-cols-1 sm:grid-cols-2 gap-x-12 gap-y-8">
              {REQUIREMENTS.map((item, i) => (
                <li key={item.title} className="flex gap-4">
                  <span className="text-sm font-mono text-primary shrink-0">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <div>
                    <p className="text-sm font-semibold mb-1">{item.title}</p>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      {item.body}
                    </p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section>
          <div className="max-w-6xl mx-auto px-6 lg:px-8 py-16 lg:py-20 grid grid-cols-1 lg:grid-cols-2 gap-12">
            <div>
              <h2 className="text-xl font-semibold tracking-tight mb-4">
                How work runs
              </h2>
              <ol className="space-y-3 text-sm text-muted-foreground list-decimal list-inside leading-relaxed">
                <li>Complete onboarding (≥70% profile)</li>
                <li>Accept invites in your inbox</li>
                <li>Open the job card — Charter + TaskPacket checklist</li>
                <li>Submit work, pass QA, get paid on delivery</li>
              </ol>
            </div>
            <div>
              <h2 className="text-xl font-semibold tracking-tight mb-4">
                Eligibility
              </h2>
              <p className="text-sm text-muted-foreground leading-relaxed mb-6">
                Open to students and recent alumni (graduated within 3 years) of IIT
                Delhi. Campus verification is reviewed by Orchestra ops after you go
                live.
              </p>
              <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground mb-2">
                Not collected yet
              </p>
              <p className="text-sm text-muted-foreground leading-relaxed">
                Bank account and UPI stay off the form until payments leave sandbox —
                we only ask for a preferred payout range for matching.
              </p>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
