"use client";

import { useAuth } from "@clerk/nextjs";
import { createContext, useContext, useMemo, type ReactNode } from "react";

export type OrchestraAuthState = {
  clerkEnabled: boolean;
  isReady: boolean;
  isSignedIn: boolean;
};

const DEMO_AUTH: OrchestraAuthState = {
  clerkEnabled: false,
  isReady: true,
  isSignedIn: true,
};

const OrchestraAuthContext = createContext<OrchestraAuthState>(DEMO_AUTH);

export function useOrchestraAuth(): OrchestraAuthState {
  return useContext(OrchestraAuthContext);
}

/** Demo / CI build path — no Clerk hooks, always "ready". */
export function DemoAuthProvider({ children }: { children: ReactNode }) {
  return (
    <OrchestraAuthContext.Provider value={DEMO_AUTH}>
      {children}
    </OrchestraAuthContext.Provider>
  );
}

/** Must render inside ClerkProvider. */
export function ClerkAuthStateProvider({ children }: { children: ReactNode }) {
  const clerk = useAuth();
  const value = useMemo<OrchestraAuthState>(
    () => ({
      clerkEnabled: true,
      isReady: clerk.isLoaded,
      isSignedIn: clerk.isSignedIn ?? false,
    }),
    [clerk.isLoaded, clerk.isSignedIn]
  );
  return (
    <OrchestraAuthContext.Provider value={value}>
      {children}
    </OrchestraAuthContext.Provider>
  );
}
