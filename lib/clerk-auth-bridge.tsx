"use client";

import { useAuth } from "@clerk/nextjs";
import { useEffect } from "react";

import { setAuthTokenGetter } from "./auth-token";

/**
 * Registers Clerk getToken with apiFetch when Clerk is configured.
 * Mounted only inside ClerkProvider.
 */
export function ClerkAuthBridge({ children }: { children: React.ReactNode }) {
  const { getToken, isLoaded } = useAuth();

  useEffect(() => {
    if (!isLoaded) return;
    setAuthTokenGetter(async () => {
      try {
        return (await getToken()) ?? null;
      } catch {
        return null;
      }
    });
    return () => setAuthTokenGetter(null);
  }, [getToken, isLoaded]);

  return <>{children}</>;
}
