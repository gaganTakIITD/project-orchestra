"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useStartScopeSession } from "@/lib/hooks";
import { useOrchestraAuth } from "@/lib/use-orchestra-auth";

/**
 * /start bootstrap — creates a scope session then redirects to /scope/[id].
 * Waits for Clerk auth before calling the API (avoids 401 race on first paint).
 */
export default function ScopeChatSurface() {
  const router = useRouter();
  const { isReady, isSignedIn, clerkEnabled } = useOrchestraAuth();
  const [error, setError] = useState<string | null>(null);
  const startSession = useStartScopeSession();
  const startedRef = useRef(false);

  useEffect(() => {
    if (!isReady) return;
    if (clerkEnabled && !isSignedIn) return;
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
  }, [isReady, isSignedIn, clerkEnabled, router, startSession]);

  if (clerkEnabled && isReady && !isSignedIn) {
    return (
      <div className="text-sm text-muted-foreground">
        Sign in to start scoping your outcome.
      </div>
    );
  }

  if (error) {
    return <div className="text-sm text-destructive">{error}</div>;
  }

  return (
    <div className="flex items-center justify-center min-h-[24rem] text-sm text-muted-foreground">
      Opening scope chat…
    </div>
  );
}
