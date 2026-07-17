"use client";

import { useAuth } from "@clerk/nextjs";

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

/** True when API calls can attach a Clerk JWT (or demo mode needs no auth). */
export function useOrchestraAuth() {
  // Demo mode: no ClerkProvider is mounted (see lib/providers.tsx), so calling
  // Clerk's useAuth() here throws "useAuth can only be used within <ClerkProvider>".
  // Guard first — clerkEnabled is a build-time constant, so hook order stays stable.
  if (!clerkEnabled) {
    return { clerkEnabled: false, isReady: true, isSignedIn: true };
  }

  const clerk = useAuth();

  return {
    clerkEnabled: true,
    isReady: clerk.isLoaded,
    isSignedIn: clerk.isSignedIn ?? false,
  };
}
