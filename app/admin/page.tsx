"use client";

import Link from "next/link";
import Footer from "@/components/footer";
import { useMe } from "@/lib/hooks";
import type { User } from "@/lib/types";

const SECTIONS = [
  {
    title: "Outcomes",
    description: "Monitor active orders, quality checks, and escalations across the marketplace.",
  },
  {
    title: "Specialists",
    description: "Review worker onboarding, seller levels, and availability.",
  },
  {
    title: "Payouts",
    description: "Track completed tasks awaiting payout and released funds.",
  },
];

export default function AdminConsolePage() {
  const { data, isLoading } = useMe();
  const me = data as User | undefined;
  const isAdmin = me?.role === "admin";

  return (
    <div className="flex min-h-screen flex-col bg-background font-sans text-foreground">
      <main id="main-content" className="flex-1 border-b border-border">
        <div className="mx-auto max-w-5xl px-6 py-16 lg:px-8 lg:py-24">
          <p className="mb-3 font-mono text-xs uppercase tracking-widest text-primary">
            Admin console
          </p>
          <h1 className="text-4xl font-bold tracking-tight">Operations overview</h1>

          {isLoading ? (
            <div className="mt-10 h-40 animate-pulse rounded-sm bg-muted" aria-hidden="true" />
          ) : !isAdmin ? (
            <div className="mt-10 rounded-sm border border-border bg-card px-6 py-12 text-center">
              <h2 className="text-lg font-semibold">Admins only</h2>
              <p className="mx-auto mt-2 max-w-sm text-pretty text-sm text-muted-foreground">
                This console is restricted to Orchestra operators. Head back to your workspace.
              </p>
              <Link
                href="/orders"
                className="mt-6 inline-flex h-10 items-center justify-center rounded-sm bg-primary px-5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
              >
                Go to my workspace
              </Link>
            </div>
          ) : (
            <div className="mt-10 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {SECTIONS.map((s) => (
                <section key={s.title} className="rounded-sm border border-border bg-card p-6">
                  <h2 className="text-base font-semibold">{s.title}</h2>
                  <p className="mt-2 text-pretty text-sm text-muted-foreground">
                    {s.description}
                  </p>
                  <p className="mt-4 font-mono text-xs uppercase tracking-widest text-muted-foreground">
                    Wire to admin API
                  </p>
                </section>
              ))}
            </div>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}
