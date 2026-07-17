"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import Link from "next/link";
import WorkspaceHeader from "@/components/workspace-header";
import { useMe, useSetRole } from "@/lib/hooks";
import { useOrchestraAuth } from "@/lib/use-orchestra-auth";

/**
 * Worker lane shell + RBAC self-heal.
 * Deep links (e.g. /join → onboarding) set active role to worker so Clerk
 * mode doesn't 403 worker APIs. Layout also hosts WorkspaceHeader.
 *
 * Never render a blank main area — show loading / error while switching roles.
 */
export default function WorkerLayout({ children }: { children: ReactNode }) {
  const { clerkEnabled, isReady, isSignedIn } = useOrchestraAuth();
  const authReady = !clerkEnabled || (isReady && isSignedIn);
  const { data: user, isLoading: meLoading, isError: meError, refetch } = useMe({
    enabled: authReady,
  });
  const setRole = useSetRole();
  const switchStarted = useRef(false);
  const [switchError, setSwitchError] = useState<string | null>(null);

  useEffect(() => {
    if (!clerkEnabled || !authReady || !user) return;
    if (user.role === "worker" || user.role === "admin") {
      switchStarted.current = false;
      setSwitchError(null);
      return;
    }
    if (user.role !== "client" || setRole.isPending || switchStarted.current) return;
    switchStarted.current = true;
    setSwitchError(null);
    void setRole
      .mutateAsync("worker")
      .then(() => {
        setSwitchError(null);
      })
      .catch(() => {
        switchStarted.current = false;
        setSwitchError("Could not switch to the worker portal. Try again.");
      });
  }, [clerkEnabled, authReady, user?.role, setRole.isPending]);

  const roleReady =
    !clerkEnabled ||
    (!meLoading && !!user && (user.role === "worker" || user.role === "admin"));

  const switching =
    clerkEnabled &&
    authReady &&
    !!user &&
    user.role === "client" &&
    (setRole.isPending || switchStarted.current) &&
    !switchError;

  return (
    <>
      <WorkspaceHeader />
      {roleReady ? (
        children
      ) : (
        <div className="min-h-[50vh] flex items-center justify-center px-6">
          <div className="max-w-md text-center space-y-4">
            {!authReady || meLoading || switching ? (
              <p className="text-sm font-mono text-muted-foreground">
                Opening worker portal…
              </p>
            ) : meError || !user ? (
              <>
                <p className="text-sm text-destructive">
                  Could not load your account. Sign in again, then retry.
                </p>
                <div className="flex items-center justify-center gap-3">
                  <button
                    type="button"
                    onClick={() => void refetch()}
                    className="h-10 px-5 border border-border text-sm font-semibold"
                  >
                    Retry
                  </button>
                  <Link
                    href="/sign-in"
                    className="h-10 px-5 bg-primary text-primary-foreground text-sm font-semibold inline-flex items-center"
                  >
                    Sign in
                  </Link>
                </div>
              </>
            ) : switchError ? (
              <>
                <p className="text-sm text-destructive">{switchError}</p>
                <button
                  type="button"
                  onClick={() => {
                    switchStarted.current = false;
                    setSwitchError(null);
                  }}
                  className="h-10 px-5 bg-primary text-primary-foreground text-sm font-semibold"
                >
                  Try again
                </button>
              </>
            ) : (
              <p className="text-sm font-mono text-muted-foreground">
                Opening worker portal…
              </p>
            )}
          </div>
        </div>
      )}
    </>
  );
}
