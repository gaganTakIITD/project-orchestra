import Header from "@/components/header";
import Footer from "@/components/footer";
import ScopeChatSurface from "@/components/scope-chat-surface";

export const metadata = {
  title: "Describe your outcome — Project Orchestra",
  description:
    "Co-create your outcome job description with our AI Spec Compiler. Real-time scope, deliverables, and workflow before you commit.",
};

export default function StartPage() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-16 lg:py-20">
          <p className="text-xs font-mono tracking-widest uppercase text-primary mb-6">For clients</p>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight leading-none text-balance mb-4">
            Scope your outcome.
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed mb-10 max-w-2xl">
            Tell us what you need in plain language. We extract a detailed job description — deliverables,
            done-when criteria, scope, and workflow — and ask only what&apos;s still missing before we quote.
          </p>

          <ScopeChatSurface />
        </div>
      </main>

      <Footer />
    </div>
  );
}
