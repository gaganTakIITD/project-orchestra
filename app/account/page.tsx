"use client";

import Footer from "@/components/footer";
import { useMe } from "@/lib/hooks";
import type { User } from "@/lib/types";

const ROLE_LABEL: Record<string, string> = {
  client: "Client",
  worker: "Specialist",
  admin: "Administrator",
};

export default function AccountPage() {
  const { data, isLoading } = useMe();
  const me = data as User | undefined;

  return (
    <div className="flex min-h-screen flex-col bg-background font-sans text-foreground">
      <main id="main-content" className="flex-1 border-b border-border">
        <div className="mx-auto max-w-3xl px-6 py-16 lg:px-8 lg:py-24">
          <p className="mb-3 font-mono text-xs uppercase tracking-widest text-primary">
            Account
          </p>
          <h1 className="text-4xl font-bold tracking-tight">Your profile</h1>
          <p className="mt-3 text-pretty text-muted-foreground">
            Manage how you appear across the Orchestra workspace.
          </p>

          {isLoading ? (
            <div className="mt-10 h-40 animate-pulse rounded-sm bg-muted" aria-hidden="true" />
          ) : me ? (
            <dl className="mt-10 divide-y divide-border rounded-sm border border-border bg-card">
              <Row label="Name" value={me.full_name} />
              <Row label="Email" value={me.email} />
              <Row label="Role" value={ROLE_LABEL[me.role] ?? me.role} />
              <Row
                label="Email verified"
                value={me.email_verified ? "Verified" : "Not verified"}
              />
            </dl>
          ) : (
            <p className="mt-10 text-sm text-muted-foreground">
              We couldn&apos;t load your profile. Please sign in again.
            </p>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-1 px-6 py-5 sm:flex-row sm:items-center sm:justify-between">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className="text-sm font-medium">{value}</dd>
    </div>
  );
}
