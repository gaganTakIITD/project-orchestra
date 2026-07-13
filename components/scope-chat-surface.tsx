"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMyScopes, useStartScopeSession } from "@/lib/hooks";
import { useOrchestraAuth } from "@/lib/use-orchestra-auth";

/**
 * /start bootstrap — offers "Resume scope" when drafts exist, otherwise creates
 * a scope session and redirects to /scope/[id].
 * Waits for Clerk auth before calling the API (avoids 401 race on first paint).
 */
export default function ScopeChatSurface() {
  const router = useRouter();
  const { isReady, isSignedIn, clerkEnabled } = useOrchestraAuth();
  const [error, setError] = useState<string | null>(null);
  const [startFresh, setStartFresh] = useState(false);
  const startSession = useStartScopeSession();
  const authReady = isReady && (!clerkEnabled || isSignedIn);
  const { data: scopes = [], isPending: scopesPending } = useMyScopes({
    enabled: authReady,
  });
  const startedRef = useRef(false);

  const activeDrafts = scopes.filter((s) => s.status === "active");
  const showResume = authReady && !scopesPending && activeDrafts.length > 0 && !startFresh;

  useEffect(() => {
    if (!authReady) return;
    if (scopesPending) return;
    if (showResume) return;
    if (startedRef.current) return;
    startedRef.current = true;

    startSession.mutate(undefined, {
      onSuccess: (s) => {
        router.push(`/scope/${s.id}`);
      },
      onError: () => {
        startedRef.current = false;
        setError("Could not start scope chat. Please refresh.");
      },
    });
  }, [authReady, scopesPending, showResume, router, startSession]);

  if (clerkEnabled && isReady && !isSignedIn) {
    return (
      <div className="text-sm text-muted-foreground">
        Sign in to start scoping your outcome.{" "}
        <Link href="/sign-in" className="text-primary font-semibold hover:underline">
          Sign in
        </Link>
      </div>
    );
  }

  if (error) {
    return <div className="text-sm text-destructive">{error}</div>;
  }

  if (!authReady || scopesPending) {
    return (
      <div className="flex items-center justify-center min-h-[24rem] text-sm text-muted-foreground">
        Checking for open drafts…
      </div>
    );
  }

  if (showResume) {
    return (
      <div className="space-y-8 max-w-xl">
        <div>
          <h2 className="text-lg font-semibold mb-2">Resume scope</h2>
          <p className="text-sm text-muted-foreground mb-4">
            You have an open draft. Continue where you left off, or start fresh.
          </p>
          <ul className="flex flex-col gap-3">
            {activeDrafts.map((s) => (
              <li key={s.id}>
                <Link
                  href={`/scope/${s.id}`}
                  className="flex items-center justify-between rounded-sm border border-border bg-card px-5 py-4 transition-colors hover:border-primary/50"
                >
                  <span className="text-sm font-medium">
                    {s.title || `Draft scope · ${s.id}`}
                  </span>
                  <span className="font-mono text-xs text-muted-foreground">
                    {s.completeness_pct}% · Resume →
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </div>
        <button
          type="button"
          onClick={() => setStartFresh(true)}
          className="inline-flex h-10 items-center justify-center rounded-sm border border-border px-5 text-sm font-semibold text-foreground transition-colors hover:border-primary/50"
        >
          Start fresh
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-[24rem] text-sm text-muted-foreground">
      Opening scope chat…
    </div>
  );
}
