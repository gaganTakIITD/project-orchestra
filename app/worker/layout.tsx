"use client";

import { useEffect } from "react";
import { useMe, useSetRole } from "@/lib/hooks";
import { useOrchestraAuth } from "@/lib/use-orchestra-auth";

/**
 * Ensures the signed-in account's active role is `worker` when entering the
 * worker lane. Under real RBAC (Clerk) a `client` account would otherwise 403
 * on worker APIs — this makes deep links (e.g. /join → onboarding) self-heal
 * the same way the portal hub does. In demo/mocks mode worker endpoints resolve
 * the seeded worker regardless, so we skip the switch.
 */
export default function WorkerLayout({ children }: { children: React.ReactNode }) {
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

  return <>{children}</>;
}
