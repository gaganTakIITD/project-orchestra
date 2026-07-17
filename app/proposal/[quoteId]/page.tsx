"use client";

import { useState, type ReactNode } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { ApiError } from "@/lib/api";
import { useQuote, useSpec, useAcceptQuote } from "@/lib/hooks";
import Footer from "@/components/footer";
import JourneyStepper from "@/components/journey-stepper";
import { CLIENT_JOURNEY_STAGES } from "@/lib/journey";

function formatPrice(price: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
  }).format(price);
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export default function ProposalPage() {
  const router = useRouter();
  const routeParams = useParams<{ quoteId: string }>();
  const quoteId =
    typeof routeParams.quoteId === "string" ? routeParams.quoteId : "";
  const [confirmError, setConfirmError] = useState<string | null>(null);

  const { data: quote, isLoading: quoteLoading } = useQuote(quoteId);
  const { data: spec, isLoading: specLoading } = useSpec(quote?.spec_id || "");
  const acceptQuote = useAcceptQuote();

  const handleConfirm = async () => {
    if (!quote || acceptQuote.isPending) return;
    setConfirmError(null);
    try {
      const result = await acceptQuote.mutateAsync(quote.id);
      try {
        sessionStorage.setItem("order_id", result.order_id);
      } catch {
        /* ignore */
      }
      router.push(`/orders/${result.order_id}`);
    } catch (err) {
      const detail =
        err instanceof ApiError && err.message
          ? err.message
          : "Could not confirm. Please try again.";
      setConfirmError(detail);
    }
  };

  if (!quoteId || quoteLoading || specLoading) {
    return (
      <Shell>
        <p className="text-sm font-mono text-muted-foreground">
          Loading proposal…
        </p>
      </Shell>
    );
  }

  if (!quote || !spec) {
    return (
      <Shell>
        <h1 className="text-2xl font-serif font-bold mb-3">Proposal not found</h1>
        <p className="text-sm text-muted-foreground mb-6">
          This quote may have expired or the link is incomplete.
        </p>
        <Link href="/start" className="text-sm font-semibold text-primary">
          Start a new outcome →
        </Link>
      </Shell>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main id="main-content" className="flex-1">
        <div className="max-w-4xl mx-auto px-6 lg:px-8 py-12 lg:py-20">
          <div className="mb-8">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-3">
              Confirm proposal
            </p>
            <h1 className="text-3xl sm:text-4xl font-serif font-bold tracking-tight text-balance mb-3">
              {spec.outcome_statement}
            </h1>
            <p className="text-sm text-muted-foreground max-w-2xl leading-relaxed">
              Fixed scope, fixed price, fixed deadline. Confirming freezes this
              job description and starts staffing.
            </p>
          </div>

          <div className="mb-10 border border-border bg-card p-5 lg:p-6">
            <JourneyStepper
              stages={CLIENT_JOURNEY_STAGES}
              currentStageId="confirm"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-10 lg:gap-12">
            <div className="lg:col-span-2 space-y-10">
              <section>
                <h2 className="text-base font-semibold mb-4">Deliverables</h2>
                <ul className="space-y-2">
                  {spec.deliverables.map((d, i) => (
                    <li
                      key={i}
                      className="flex gap-3 items-start border border-border px-4 py-3"
                    >
                      <span className="w-1.5 h-1.5 bg-primary mt-2 shrink-0" />
                      <div>
                        <p className="text-sm font-medium">{d.name}</p>
                        {d.format ? (
                          <p className="text-xs text-muted-foreground mt-0.5">
                            {d.format}
                          </p>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              </section>

              <section className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                <div>
                  <h2 className="text-base font-semibold mb-3">Included</h2>
                  <ul className="space-y-2">
                    {spec.in_scope.map((item, i) => (
                      <li
                        key={i}
                        className="text-sm text-muted-foreground flex gap-2"
                      >
                        <span className="text-primary">✓</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h2 className="text-base font-semibold mb-3">Not included</h2>
                  <ul className="space-y-2">
                    {spec.out_of_scope.map((item, i) => (
                      <li
                        key={i}
                        className="text-sm text-muted-foreground flex gap-2"
                      >
                        <span className="opacity-40">○</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </section>

              <section>
                <h2 className="text-base font-semibold mb-4">
                  How we measure success
                </h2>
                <ul className="space-y-2">
                  {spec.acceptance_criteria.map((c, i) => (
                    <li key={i} className="border border-border px-4 py-3">
                      <p className="text-sm font-medium">{c.criterion}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {c.check_type === "deterministic" &&
                          "Automatically verified"}
                        {c.check_type === "ai_judged" && "Quality-checked"}
                        {c.check_type === "human_required" && "Team-verified"}
                      </p>
                    </li>
                  ))}
                </ul>
              </section>
            </div>

            <aside className="lg:col-span-1">
              <div className="sticky top-24 border border-border bg-card p-6 space-y-5">
                <div>
                  <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">
                    Fixed price
                  </p>
                  <p className="text-3xl font-bold tabular-nums">
                    {formatPrice(quote.price)}
                  </p>
                </div>

                <dl className="border-t border-border pt-5 space-y-3 text-sm">
                  <div className="flex justify-between gap-3">
                    <dt className="text-muted-foreground">Deadline</dt>
                    <dd className="font-medium">{formatDate(quote.deadline)}</dd>
                  </div>
                  <div className="flex justify-between gap-3">
                    <dt className="text-muted-foreground">Revisions</dt>
                    <dd className="font-medium">{quote.revision_limit} rounds</dd>
                  </div>
                </dl>

                <div className="border-t border-border pt-4">
                  <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-2">
                    On confirm
                  </p>
                  <ul className="text-xs text-muted-foreground space-y-1.5 leading-relaxed">
                    <li>Scope freezes as the job description</li>
                    <li>Funds show as Held on your tracker</li>
                    <li>We staff tasks and invite talent</li>
                  </ul>
                </div>

                {quote.ai_rationale ? (
                  <div className="border-t border-border pt-4">
                    <p className="text-xs text-muted-foreground mb-1">
                      Why this price
                    </p>
                    <p className="text-xs leading-relaxed text-muted-foreground">
                      {quote.ai_rationale}
                    </p>
                  </div>
                ) : null}

                <button
                  type="button"
                  onClick={handleConfirm}
                  disabled={acceptQuote.isPending}
                  className="w-full h-11 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
                >
                  {acceptQuote.isPending
                    ? "Creating your order…"
                    : "Confirm & begin work"}
                </button>

                {confirmError ? (
                  <p className="text-xs text-destructive text-center" role="alert">
                    {confirmError}
                  </p>
                ) : acceptQuote.isPending ? (
                  <p className="text-xs text-muted-foreground text-center">
                    Freezing scope and building the task plan — usually a few seconds.
                  </p>
                ) : (
                  <p className="text-xs text-muted-foreground text-center">
                    You can still chat with the team after confirm. Scope changes
                    go through amendments.
                  </p>
                )}
              </div>
            </aside>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="max-w-md text-center">{children}</div>
      </main>
      <Footer />
    </div>
  );
}
