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

          {/* Label */}
          <p className="text-xs font-mono tracking-widest uppercase text-primary mb-8">
            For talent
          </p>

          {/* Headline */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-none text-balance mb-10">
            Apply to join Orchestra.
          </h1>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 lg:gap-24">

            {/* Form side */}
            <div>
              <p className="text-sm text-muted-foreground leading-relaxed mb-10">
                We verify every member of our talent community as a student or recent alumni of IIT Delhi. Once verified, you get matched to scoped outcomes with clear specs, fair pay, and no bad-faith clients.
              </p>

              <form className="flex flex-col gap-6">
                <div className="flex flex-col gap-2">
                  <label htmlFor="name" className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
                    Your name
                  </label>
                  <input
                    id="name"
                    name="name"
                    type="text"
                    placeholder="Priya Mehta"
                    className="h-11 border border-border bg-background px-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <label htmlFor="email" className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
                    IIT Delhi email (preferred)
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    placeholder="you@iitd.ac.in"
                    className="h-11 border border-border bg-background px-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <label htmlFor="role" className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
                    Primary skill
                  </label>
                  <select
                    id="role"
                    name="role"
                    className="h-11 border border-border bg-background px-4 text-sm text-foreground focus:outline-none focus:border-primary transition-colors appearance-none"
                  >
                    <option value="">Select a skill</option>
                    <option value="design">Product / UI Design</option>
                    <option value="frontend">Frontend Development</option>
                    <option value="fullstack">Full-stack Development</option>
                    <option value="motion">Motion / Video</option>
                    <option value="copywriting">Copywriting / Content</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div className="flex flex-col gap-2">
                  <label htmlFor="portfolio" className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
                    Portfolio or GitHub link
                  </label>
                  <input
                    id="portfolio"
                    name="portfolio"
                    type="url"
                    placeholder="https://your-portfolio.com"
                    className="h-11 border border-border bg-background px-4 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors"
                  />
                </div>

                <div className="flex flex-col gap-2">
                  <label htmlFor="bio" className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
                    Briefly describe your experience
                  </label>
                  <textarea
                    id="bio"
                    name="bio"
                    rows={4}
                    placeholder="e.g. 3rd year CSE at IITD, 2 years of freelance frontend work, built 4 production apps."
                    className="border border-border bg-background px-4 py-3 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary transition-colors resize-none leading-relaxed"
                  />
                </div>

                <button
                  type="submit"
                  className="inline-flex items-center justify-center h-11 px-8 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity self-start"
                >
                  Submit application
                </button>

                <p className="text-xs text-muted-foreground">
                  Applications are reviewed within 48 hours. We&apos;ll reach out over email with next steps.
                </p>
              </form>
            </div>

            {/* Benefits side */}
            <div className="flex flex-col gap-8">
              <div className="border border-border p-8 flex flex-col gap-6">
                <h2 className="text-base font-semibold">Why join Orchestra</h2>
                {[
                  { n: "01", title: "Pre-vetted outcomes only", body: "Every project is scoped and priced before you touch it. No scope creep, no bad-faith clients, no unpaid revisions." },
                  { n: "02", title: "Clear specs upfront", body: "You receive a detailed brief with acceptance criteria before accepting a task. You always know what done looks like." },
                  { n: "03", title: "Payouts on delivery", body: "Payments are triggered automatically when your work passes the AI quality gate. No chasing invoices." },
                  { n: "04", title: "Build your verified portfolio", body: "Every completed outcome is a verified credential on your Orchestra profile—more valuable than a generic freelancer rating." },
                ].map((item) => (
                  <div key={item.n} className="flex gap-5">
                    <span className="text-xl font-bold font-mono text-primary flex-shrink-0 w-8">{item.n}</span>
                    <div>
                      <p className="text-sm font-semibold mb-1">{item.title}</p>
                      <p className="text-sm text-muted-foreground leading-relaxed">{item.body}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="border border-border p-6">
                <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-3">Eligibility</p>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  Currently open to students and recent alumni (graduated within 3 years) of IIT Delhi. Expanding to other IITs soon.
                </p>
              </div>
            </div>

          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
