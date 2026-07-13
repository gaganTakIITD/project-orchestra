"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  useQuote,
  useSpec,
  useAcceptQuote,
  useFinalizePricingSession,
  useSendChatMessage,
  useStartPricingSession,
} from "@/lib/hooks";
import type { ChatSession } from "@/lib/types";
import Header from "@/components/header";
import Footer from "@/components/footer";

export default function ProposalPage() {
  const router = useRouter();
  const routeParams = useParams<{ quoteId: string }>();
  const quoteId =
    typeof routeParams.quoteId === "string" ? routeParams.quoteId : "";

  // isPending (not only isLoading): RQ v5 isLoading is false while pending+idle on SSR
  const { data: quote, isPending: quotePending, isError: quoteError } = useQuote(quoteId);
  const {
    data: spec,
    isPending: specPending,
    isError: specError,
  } = useSpec(quote?.spec_id || "");
  const acceptQuote = useAcceptQuote();
  const startPricing = useStartPricingSession();
  const [pricingSession, setPricingSession] = useState<ChatSession | null>(null);
  const [pricingInput, setPricingInput] = useState("");
  const [pricingError, setPricingError] = useState<string | null>(null);
  const pricingBottomRef = useRef<HTMLDivElement>(null);
  const sendPricing = useSendChatMessage(pricingSession?.id ?? "");
  const finalizePricing = useFinalizePricingSession();

  useEffect(() => {
    pricingBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [pricingSession?.messages.length, sendPricing.streamingText]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
    }).format(Number(price));
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

  const handleStartPricing = async () => {
    if (!quoteId || pricingSession || startPricing.isPending) return;
    setPricingError(null);
    try {
      const session = await startPricing.mutateAsync(quoteId);
      setPricingSession(session);
    } catch {
      setPricingError("Could not start pricing chat.");
    }
  };

  const handlePricingSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pricingSession || !pricingInput.trim() || sendPricing.isPending) return;
    setPricingError(null);
    const text = pricingInput.trim();
    setPricingInput("");
    try {
      const updated = await sendPricing.mutateAsync(text);
      setPricingSession(updated);
    } catch {
      setPricingError("Message failed. Please try again.");
    }
  };

  const handlePricingFinalize = async () => {
    if (!pricingSession?.ready_to_confirm) return;
    setPricingError(null);
    try {
      const result = await finalizePricing.mutateAsync(pricingSession.id);
      sessionStorage.setItem("order_id", result.order_id);
      router.push(`/orders/${result.order_id}`);
    } catch {
      setPricingError("Could not accept quote from pricing chat.");
    }
  };

  if (!quoteId || quotePending || (quote && specPending)) {
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

  if (quoteError || specError || !quote || !spec) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-4">
            <p className="text-muted-foreground">Proposal not found</p>
            <Link
              href="/start"
              className="inline-flex items-center justify-center h-10 px-6 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              Start new scope →
            </Link>
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
            <div className="lg:col-span-2 space-y-12">
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

              {spec.workflow_summary ? (
                <section>
                  <h2 className="text-base font-semibold mb-4">Workflow</h2>
                  <p className="text-sm leading-relaxed text-muted-foreground">
                    {spec.workflow_summary}
                  </p>
                </section>
              ) : null}

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

              {spec.client_inputs_required.length > 0 ? (
                <section>
                  <h2 className="text-base font-semibold mb-4">We need from you</h2>
                  <ul className="space-y-2">
                    {spec.client_inputs_required.map((item, i) => (
                      <li key={i} className="text-sm text-muted-foreground flex gap-2 items-start">
                        <span className="text-primary mt-1">·</span>
                        <span>{item.replace(/_/g, " ")}</span>
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}

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

              {/* Pricing Reasoner confirm chat (Stage 2) */}
              <section className="border border-border">
                <div className="px-5 py-4 border-b border-border flex items-center justify-between gap-3">
                  <div>
                    <p className="text-xs font-mono tracking-widest uppercase text-primary">
                      Pricing Reasoner
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Ask about SKU drivers and risk before you accept
                    </p>
                  </div>
                  {!pricingSession ? (
                    <button
                      type="button"
                      onClick={handleStartPricing}
                      disabled={startPricing.isPending}
                      className="h-9 px-4 border border-border text-xs font-semibold hover:border-primary disabled:opacity-50"
                    >
                      {startPricing.isPending ? "Starting…" : "Ask about price"}
                    </button>
                  ) : null}
                </div>
                {pricingSession ? (
                  <>
                    <div className="max-h-64 overflow-y-auto px-5 py-4 space-y-3">
                      {pricingSession.messages.map((msg) => (
                        <div
                          key={msg.id}
                          className={msg.role === "user" ? "flex justify-end" : "flex justify-start"}
                        >
                          <div
                            className={
                              msg.role === "user"
                                ? "max-w-[90%] bg-primary text-primary-foreground px-3 py-2 text-sm"
                                : "max-w-[90%] border border-border bg-muted/30 px-3 py-2 text-sm whitespace-pre-wrap"
                            }
                          >
                            {msg.body}
                          </div>
                        </div>
                      ))}
                      {sendPricing.isPending && sendPricing.streamingText ? (
                        <div className="flex justify-start">
                          <div className="max-w-[90%] border border-border bg-muted/30 px-3 py-2 text-sm">
                            {sendPricing.streamingText}
                          </div>
                        </div>
                      ) : null}
                      <div ref={pricingBottomRef} />
                    </div>
                    <form
                      onSubmit={handlePricingSend}
                      className="p-4 border-t border-border flex flex-col gap-2"
                    >
                      <textarea
                        value={pricingInput}
                        onChange={(e) => setPricingInput(e.target.value)}
                        rows={2}
                        placeholder='e.g. "Why this price?" or "confirm"'
                        className="w-full border border-border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:border-primary"
                        disabled={sendPricing.isPending}
                      />
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="submit"
                          disabled={!pricingInput.trim() || sendPricing.isPending}
                          className="h-9 px-4 bg-primary text-primary-foreground text-xs font-semibold disabled:opacity-50"
                        >
                          Send
                        </button>
                        <button
                          type="button"
                          onClick={handlePricingFinalize}
                          disabled={
                            !pricingSession.ready_to_confirm || finalizePricing.isPending
                          }
                          className="h-9 px-4 border border-primary text-primary text-xs font-semibold disabled:opacity-40"
                        >
                          {finalizePricing.isPending
                            ? "Accepting…"
                            : "Accept via chat →"}
                        </button>
                      </div>
                      {pricingError ? (
                        <p className="text-xs text-destructive">{pricingError}</p>
                      ) : null}
                    </form>
                  </>
                ) : pricingError ? (
                  <p className="px-5 py-3 text-xs text-destructive">{pricingError}</p>
                ) : null}
              </section>
            </div>

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
