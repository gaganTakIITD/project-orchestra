"use client";

import { useAuth } from "@clerk/nextjs";

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export type OrchestraAuthState = {
  clerkEnabled: boolean;
  isReady: boolean;
  isSignedIn: boolean;
};

/**
 * Auth gate for Orchestra screens.
 *
 * IMPORTANT: never call `useAuth()` unless ClerkProvider is mounted.
 * Providers only wrap ClerkProvider when NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
 * is set — calling useAuth unconditionally breaks `next build` prerender
 * (and Vercel projects without Clerk env, e.g. v0-project).
 *
 * Hook choice is fixed at module load from the env flag so Rules of Hooks stay valid.
 */
function useOrchestraAuthClerk(): OrchestraAuthState {
  const clerk = useAuth();
  return {
    clerkEnabled: true,
    isReady: clerk.isLoaded,
    isSignedIn: clerk.isSignedIn ?? false,
  };
}

function useOrchestraAuthDemo(): OrchestraAuthState {
  return { clerkEnabled: false, isReady: true, isSignedIn: true };
}

/** True when API calls can attach a Clerk JWT (or demo mode needs no auth). */
export const useOrchestraAuth: () => OrchestraAuthState = clerkEnabled
  ? useOrchestraAuthClerk
  : useOrchestraAuthDemo;
