"use client";

import Link from "next/link";
import Footer from "@/components/footer";
import JourneyStepper from "@/components/journey-stepper";
import { CLIENT_JOURNEY_STAGES, clientStageForOrder } from "@/components/journey";
import { useMyOrders, useMyScopes } from "@/components/portal-data";
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

export default function MyOutcomesPage() {
  const { orders, isLoading } = useMyOrders();
  const { scopes } = useMyScopes();

  return (
    <div className="flex min-h-screen flex-col bg-background font-sans text-foreground">
      <main id="main-content" className="flex-1 border-b border-border">
        <div className="mx-auto max-w-5xl px-6 py-16 lg:px-8 lg:py-24">
          <div className="mb-12 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="mb-3 font-mono text-xs uppercase tracking-widest text-primary">
                Your workspace
              </p>
              <h1 className="text-4xl font-bold tracking-tight text-balance">My outcomes</h1>
              <p className="mt-3 max-w-xl text-pretty text-muted-foreground">
                Track every outcome you have commissioned, from scoping through delivery.
              </p>
            </div>
            <Link
              href="/start"
              className="inline-flex h-11 flex-shrink-0 items-center justify-center rounded-sm bg-primary px-6 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              Start a new outcome
            </Link>
          </div>

          {/* Resume in-progress scopes */}
          {scopes.length > 0 ? (
            <section className="mb-12">
              <h2 className="mb-4 text-sm font-semibold text-muted-foreground">
                Pick up where you left off
              </h2>
              <ul className="flex flex-col gap-3">
                {scopes.map((s) => (
                  <li key={s.id}>
                    <Link
                      href={`/scope/${s.id}`}
                      className="flex items-center justify-between rounded-sm border border-border bg-card px-5 py-4 transition-colors hover:border-primary/50"
                    >
                      <span className="text-sm font-medium">Draft scope · {s.id}</span>
                      <span className="font-mono text-xs text-muted-foreground">Resume →</span>
                    </Link>
                  </li>
                ))}
              </ul>
            </section>
          ) : null}

          {isLoading ? (
            <OutcomeSkeleton />
          ) : orders.length === 0 ? (
            <EmptyState />
          ) : (
            <ul className="flex flex-col gap-6">
              {orders.map((order) => (
                <li key={order.id}>
                  <OutcomeCard order={order} />
                </li>
              ))}
            </ul>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

function OutcomeCard({ order }: { order: OutcomeOrder }) {
  return (
    <Link
      href={`/orders/${order.id}`}
      className="block rounded-sm border border-border bg-card p-6 transition-colors hover:border-primary/50 lg:p-8"
    >
      <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <h3 className="text-xl font-semibold">HealthTrack — Launch Studio</h3>
          <p className="mt-1 font-mono text-xs text-muted-foreground">{order.id}</p>
        </div>
        <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-medium text-primary">
          {orderStatusClientLabel[order.status]}
        </span>
      </div>

      <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <Stat label="Fixed price" value={formatPrice(order.price)} />
        <Stat label="Deadline" value={formatDate(order.deadline)} />
        <Stat label="Progress" value={`${order.progress_pct}%`} />
        <Stat label="Revisions" value={`${order.revision_limit} rounds`} />
      </div>

      <JourneyStepper
        stages={CLIENT_JOURNEY_STAGES}
        currentStageId={clientStageForOrder(order.status)}
      />
    </Link>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="mb-1 text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-semibold">{value}</p>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-sm border border-dashed border-border bg-card px-6 py-16 text-center">
      <h2 className="text-lg font-semibold">No outcomes yet</h2>
      <p className="mx-auto mt-2 max-w-sm text-pretty text-sm text-muted-foreground">
        Describe what you need and we&apos;ll turn it into a fixed-price plan with a team to deliver it.
      </p>
      <Link
        href="/start"
        className="mt-6 inline-flex h-10 items-center justify-center rounded-sm bg-primary px-5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
      >
        Start a new outcome
      </Link>
    </div>
  );
}

function OutcomeSkeleton() {
  return (
    <div className="flex flex-col gap-6" aria-hidden="true">
      {[0, 1].map((i) => (
        <div key={i} className="rounded-sm border border-border bg-card p-6 lg:p-8">
          <div className="mb-6 h-6 w-56 animate-pulse rounded bg-muted" />
          <div className="mb-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            {[0, 1, 2, 3].map((j) => (
              <div key={j} className="h-8 animate-pulse rounded bg-muted" />
            ))}
          </div>
          <div className="h-8 animate-pulse rounded bg-muted" />
        </div>
      ))}
    </div>
  );
}
