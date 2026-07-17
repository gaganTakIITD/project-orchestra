"use client";

import Link from "next/link";
import Footer from "@/components/footer";
import { clientStageForOrder } from "@/lib/journey";
import { useMyOrders, useMyScopes } from "@/lib/hooks";
import { orderStatusClientLabel } from "@/lib/state-labels";
import type { OutcomeOrder } from "@/lib/types";

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

function nextAction(order: OutcomeOrder): string {
  switch (order.status) {
    case "confirmed":
    case "assembling_team":
      return "Assemble team";
    case "delivery_active":
    case "under_quality_check":
    case "amendment_pending":
    case "escalated":
      return "Track progress";
    case "delivered":
      return "Accept delivery";
    case "closed":
      return "View outcome";
    case "cancelled":
      return "View details";
    default:
      return "Open";
  }
}

export default function MyOutcomesPage() {
  const {
    data: orders = [],
    isLoading,
    isError,
    refetch,
  } = useMyOrders();
  const { data: scopes = [], isLoading: scopesLoading } = useMyScopes();
  const activeScopes = scopes.filter(
    (s) => !s.title?.toLowerCase().includes("finalized")
  );

  return (
    <div className="flex min-h-screen flex-col bg-background font-sans text-foreground">
      <main id="main-content" className="flex-1">
        <div className="mx-auto max-w-5xl px-6 py-12 lg:px-8 lg:py-16">
          <div className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="mb-2 font-mono text-xs uppercase tracking-widest text-primary">
                Client workspace
              </p>
              <h1 className="font-serif text-3xl sm:text-4xl font-bold tracking-tight">
                My outcomes
              </h1>
              <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                Drafts you&apos;re still scoping, and outcomes in delivery.
              </p>
            </div>
            <Link
              href="/start"
              className="inline-flex h-11 flex-shrink-0 items-center justify-center bg-primary px-6 text-sm font-semibold text-primary-foreground hover:opacity-90"
            >
              Start a new outcome
            </Link>
          </div>

          {scopesLoading ? (
            <div className="mb-10 h-16 animate-pulse bg-muted" />
          ) : activeScopes.length > 0 ? (
            <section className="mb-10">
              <h2 className="mb-3 text-xs font-mono uppercase tracking-wider text-muted-foreground">
                Resume scoping
              </h2>
              <ul className="flex flex-col gap-2">
                {activeScopes.map((s) => (
                  <li key={s.id}>
                    <Link
                      href={`/scope/${s.id}`}
                      className="flex items-center justify-between gap-4 border border-border bg-card px-4 py-3 transition-colors hover:border-primary/40"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">
                          {s.title || "Untitled draft"}
                        </p>
                        <div className="mt-2 h-1 w-32 bg-border overflow-hidden">
                          <div
                            className="h-full bg-primary"
                            style={{ width: `${s.completeness_pct}%` }}
                          />
                        </div>
                      </div>
                      <span className="text-xs font-mono text-muted-foreground shrink-0">
                        {s.completeness_pct}% · Resume →
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          <section>
            <h2 className="mb-4 text-xs font-mono uppercase tracking-wider text-muted-foreground">
              Active & past outcomes
            </h2>
            {isLoading ? (
              <OutcomeSkeleton />
            ) : isError ? (
              <div className="border border-border px-5 py-8 text-center">
                <p className="text-sm text-muted-foreground mb-3">
                  Could not load outcomes.
                </p>
                <button
                  type="button"
                  onClick={() => refetch()}
                  className="text-sm font-semibold text-primary"
                >
                  Retry
                </button>
              </div>
            ) : orders.length === 0 ? (
              <EmptyState />
            ) : (
              <ul className="flex flex-col gap-3">
                {orders.map((order) => (
                  <li key={order.id}>
                    <OutcomeCard order={order} />
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}

function OutcomeCard({ order }: { order: OutcomeOrder }) {
  const stage = clientStageForOrder(order.status);
  const action = nextAction(order);

  return (
    <Link
      href={`/orders/${order.id}`}
      className="block border border-border bg-card px-5 py-5 transition-colors hover:border-primary/40"
    >
      <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
        <div>
          <p className="text-base font-semibold">
            {orderStatusClientLabel[order.status]}
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Due {formatDate(order.deadline)} · {formatPrice(order.price)}
          </p>
        </div>
        <span className="text-xs font-semibold text-primary">{action} →</span>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex-1 h-1.5 bg-border overflow-hidden">
          <div
            className="h-full bg-primary transition-all"
            style={{ width: `${order.progress_pct}%` }}
          />
        </div>
        <span className="text-xs font-mono tabular-nums text-muted-foreground shrink-0">
          {order.progress_pct}%
        </span>
      </div>
      <p className="mt-2 text-[11px] font-mono uppercase tracking-wider text-muted-foreground">
        Stage · {stage}
      </p>
    </Link>
  );
}

function EmptyState() {
  return (
    <div className="border border-dashed border-border px-6 py-14 text-center">
      <h2 className="text-lg font-semibold">No outcomes yet</h2>
      <p className="mx-auto mt-2 max-w-sm text-sm text-muted-foreground">
        Describe what you need — we&apos;ll turn it into a fixed-price plan and
        deliver it.
      </p>
      <Link
        href="/start"
        className="mt-6 inline-flex h-10 items-center justify-center bg-primary px-5 text-sm font-semibold text-primary-foreground hover:opacity-90"
      >
        Start a new outcome
      </Link>
    </div>
  );
}

function OutcomeSkeleton() {
  return (
    <div className="flex flex-col gap-3" aria-hidden="true">
      {[0, 1].map((i) => (
        <div key={i} className="border border-border bg-card px-5 py-5">
          <div className="mb-4 h-5 w-40 animate-pulse bg-muted" />
          <div className="h-1.5 animate-pulse bg-muted" />
        </div>
      ))}
    </div>
  );
}
