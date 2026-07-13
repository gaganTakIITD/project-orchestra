"use client";

import { useAuth } from "@clerk/nextjs";

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

/** True when API calls can attach a Clerk JWT (or demo mode needs no auth). */
export function useOrchestraAuth() {
  const clerk = useAuth();

  if (!clerkEnabled) {
    return { clerkEnabled: false, isReady: true, isSignedIn: true };
  }

  return {
    clerkEnabled: true,
    isReady: clerk.isLoaded,
    isSignedIn: clerk.isSignedIn ?? false,
  };
}
