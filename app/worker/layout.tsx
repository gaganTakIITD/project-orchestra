"use client";

import { useEffect, type ReactNode } from "react";
import WorkspaceHeader from "@/components/workspace-header";
import { useMe, useSetRole } from "@/lib/hooks";
import { useOrchestraAuth } from "@/lib/use-orchestra-auth";

/**
 * Worker lane shell + RBAC self-heal.
 * Deep links (e.g. /join → onboarding) set active role to worker so Clerk
 * mode doesn't 403 worker APIs. Layout also hosts WorkspaceHeader.
 */
export default function WorkerLayout({ children }: { children: ReactNode }) {
  const { clerkEnabled, isReady, isSignedIn } = useOrchestraAuth();
  const authReady = !clerkEnabled || (isReady && isSignedIn);
  const { data: user } = useMe({ enabled: authReady });
  const setRole = useSetRole();

  useEffect(() => {
    if (!clerkEnabled || !authReady || !user) return;
    if (user.role === "client" && !setRole.isPending) {
      setRole.mutate("worker");
    }
  }, [clerkEnabled, authReady, user?.role, setRole.isPending]);

  return (
    <>
      <WorkspaceHeader />
      {children}
    </>
  );
}
