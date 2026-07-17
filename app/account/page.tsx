"use client";

import Link from "next/link";
import Footer from "@/components/footer";
import PortalHub from "@/components/portal-hub";
import { useMe, useWorkerProfile } from "@/lib/hooks";
import { useOrchestraAuth } from "@/lib/use-orchestra-auth";

export default function AccountPage() {
  const { clerkEnabled, isReady, isSignedIn } = useOrchestraAuth();
  const authReady = !clerkEnabled || (isReady && isSignedIn);

  const { data: user, isPending, isError } = useMe({ enabled: authReady });
  // Profile row can exist while browsing as client — still show completion %.
  const { data: workerProfile } = useWorkerProfile({
    enabled: authReady && !!user,
  });

  if (clerkEnabled && isReady && !isSignedIn) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <main className="flex-1 flex items-center justify-center px-6">
          <div className="max-w-md text-center space-y-4">
            <h1 className="text-2xl font-semibold">Sign in to choose your portal</h1>
            <p className="text-sm text-muted-foreground">
              One Orchestra account ? enter as client, worker, or admin (if assigned).
            </p>
            <Link
              href="/sign-in"
              className="inline-flex items-center h-10 px-6 bg-secondary text-secondary-foreground rounded-full text-sm font-semibold"
            >
              Sign in
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const loading = isPending || (clerkEnabled && !isReady);

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main className="flex-1 border-b border-border">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-16 lg:py-20">
          <p className="text-xs font-mono tracking-widest uppercase text-primary mb-6">
            Account
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-4">
            Choose your portal
          </h1>

          {loading ? (
            <div className="rounded-xl border border-border p-8 text-sm text-muted-foreground">
              Loading account?
            </div>
          ) : isError || !user ? (
            <div className="rounded-xl border border-destructive/30 bg-destructive/5 p-8 text-sm text-destructive">
              Could not load your account. Try refreshing or signing in again.
            </div>
          ) : (
            <div className="space-y-10">
              <section className="rounded-xl border border-border p-6 lg:p-8">
                <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-3">
                  Signed in as
                </p>
                <h2 className="text-xl font-semibold">{user.full_name}</h2>
                <p className="text-sm text-muted-foreground mt-1">{user.email}</p>
              </section>

              <PortalHub user={user} workerProfile={workerProfile ?? null} />
            </div>
          )}
        </div>
      </main>

      <Footer />
    </div>
  );
}
