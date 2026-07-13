"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect } from "react";

import { setAuthTokenGetter } from "./auth-token";

/**
 * Registers Clerk getToken with apiFetch when Clerk is configured.
 * Mounted only inside ClerkProvider.
 */
export function ClerkAuthBridge({ children }: { children: React.ReactNode }) {
  const { getToken } = useAuth();

  useEffect(() => {
    setAuthTokenGetter(async () => {
      try {
        return (await getToken()) ?? null;
      } catch {
        return null;
      }
    });
    return () => setAuthTokenGetter(null);
  }, [getToken]);

  return <>{children}</>;
}
