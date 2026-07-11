'use client';

import { useRouter } from "next/navigation";
import { useQuote, useSpec, useAcceptQuote } from "@/lib/hooks";
import Header from "@/components/header";
import Footer from "@/components/footer";

export default function ProposalPage({ params }: { params: { quoteId: string } }) {
  const router = useRouter();
  const quoteId = params.quoteId;
  
  const { data: quote, isLoading: quoteLoading } = useQuote(quoteId);
  const { data: spec, isLoading: specLoading } = useSpec(quote?.spec_id || "");
  const acceptQuote = useAcceptQuote();

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
    }).format(price);
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const handleConfirm = async () => {
    if (!quote) return;
    try {
      const result = await acceptQuote.mutateAsync(quote.id);
      sessionStorage.setItem("order_id", result.order_id);
      router.push(`/orders/${result.order_id}`);
    } catch (error) {
      alert("Failed to accept quote. Please try again.");
      console.error("[v0] Quote acceptance failed:", error);
    }
  };

  if (quoteLoading || specLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-muted-foreground">Loading proposal...</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!quote || !spec) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-muted-foreground">Proposal not found</p>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-4xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          
          {/* Header */}
          <div className="mb-16">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-4">
              Your scoped proposal
            </p>
            <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-balance mb-4">
              {spec.outcome_statement}
            </h1>
            <p className="text-lg text-muted-foreground">
              Here&apos;s the plan we&apos;ve compiled from your brief. Review the scope, deadlines, and price. Everything is fixed until completion.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            
            {/* Main content */}
            <div className="lg:col-span-2 space-y-12">
              
              {/* Deliverables */}
              <section>
                <h2 className="text-base font-semibold mb-4">Deliverables</h2>
                <div className="space-y-3">
                  {spec.deliverables.map((d, i) => (
                    <div key={i} className="flex gap-3 items-start p-4 border border-border bg-card">
                      <span className="flex-shrink-0 w-2 h-2 rounded-full bg-primary mt-2" />
                      <div>
                        <p className="text-sm font-medium">{d.name}</p>
                        <p className="text-xs text-muted-foreground mt-1">{d.format}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </section>

              {/* In Scope */}
              <section>
                <h2 className="text-base font-semibold mb-4">What&apos;s included</h2>
                <ul className="space-y-2">
                  {spec.in_scope.map((item, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex gap-2 items-start">
                      <span className="text-primary mt-1">✓</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </section>

              {/* Out of Scope */}
              <section>
                <h2 className="text-base font-semibold mb-4">Not included</h2>
                <ul className="space-y-2">
                  {spec.out_of_scope.map((item, i) => (
                    <li key={i} className="text-sm text-muted-foreground flex gap-2 items-start">
                      <span className="text-muted-foreground">○</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </section>

              {/* Acceptance Criteria */}
              <section>
                <h2 className="text-base font-semibold mb-4">How we measure success</h2>
                <div className="space-y-3">
                  {spec.acceptance_criteria.map((c, i) => (
                    <div key={i} className="p-4 border border-border rounded-sm">
                      <p className="text-sm font-medium mb-2">{c.criterion}</p>
                      <p className="text-xs text-muted-foreground">
                        {c.check_type === "deterministic" && "Automatically verified"}
                        {c.check_type === "ai_judged" && "AI-verified"}
                        {c.check_type === "human_required" && "Team-verified"}
                      </p>
                    </div>
                  ))}
                </div>
              </section>

            </div>

            {/* Quote card */}
            <div className="lg:col-span-1">
              <div className="sticky top-24 border-2 border-border p-8 bg-card space-y-6">
                <div>
                  <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">Fixed price</p>
                  <p className="text-4xl font-bold">{formatPrice(quote.price)}</p>
                </div>

                <div className="border-t border-border pt-6 space-y-4">
                  <div>
                    <p className="text-xs text-muted-foreground">Deadline</p>
                    <p className="text-sm font-medium">{formatDate(quote.deadline)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Revisions included</p>
                    <p className="text-sm font-medium">{quote.revision_limit} rounds</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">AI confidence</p>
                    <p className="text-sm font-medium">{Math.round((quote.ai_confidence || 0) * 100)}%</p>
                  </div>
                </div>

                {quote.ai_rationale && (
                  <div className="border-t border-border pt-4">
                    <p className="text-xs text-muted-foreground mb-2">Why this price</p>
                    <p className="text-xs leading-relaxed text-muted-foreground">{quote.ai_rationale}</p>
                  </div>
                )}

                <button
                  onClick={handleConfirm}
                  disabled={acceptQuote.isPending}
                  className="w-full h-11 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
                >
                  {acceptQuote.isPending ? "Confirming..." : "Confirm & begin work"}
                </button>

                <p className="text-xs text-muted-foreground text-center">
                  Once confirmed, we staff the work and begin immediately.
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
