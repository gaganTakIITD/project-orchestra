"use client";

import { useEffect, useRef, type ReactNode } from "react";
import WorkspaceHeader from "@/components/workspace-header";
import { useMe, useSetRole } from "@/lib/hooks";
import { useOrchestraAuth } from "@/lib/use-orchestra-auth";

/**
 * Worker lane shell + RBAC self-heal.
 * Deep links (e.g. /join → onboarding) set active role to worker so Clerk
 * mode doesn't 403 worker APIs. Layout also hosts WorkspaceHeader.
 *
 * In Clerk mode, children stay gated until role is worker/admin so pages
 * never hit worker APIs while still on the client role.
 */
export default function WorkerLayout({ children }: { children: ReactNode }) {
  const { clerkEnabled, isReady, isSignedIn } = useOrchestraAuth();
  const authReady = !clerkEnabled || (isReady && isSignedIn);
  const { data: user, isLoading: meLoading } = useMe({ enabled: authReady });
  const setRole = useSetRole();
  const switchStarted = useRef(false);

  useEffect(() => {
    if (!clerkEnabled || !authReady || !user) return;
    if (user.role === "worker" || user.role === "admin") {
      switchStarted.current = false;
      return;
    }
    if (user.role !== "client" || setRole.isPending || switchStarted.current) return;
    switchStarted.current = true;
    void setRole.mutateAsync("worker").catch(() => {
      switchStarted.current = false;
    });
  }, [clerkEnabled, authReady, user?.role, setRole.isPending]);

  // Demo / non-Clerk: no role switch required.
  // Clerk: wait until me is loaded and active role is worker or admin.
  const roleReady =
    !clerkEnabled ||
    (!meLoading &&
      !!user &&
      (user.role === "worker" || user.role === "admin"));

  return (
    <>
      <WorkspaceHeader />
      {roleReady ? children : null}
    </>
  );
}
