"use client";

import { ClerkProvider } from "@clerk/nextjs";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { ClerkAuthBridge } from "./clerk-auth-bridge";
import {
  ClerkAuthStateProvider,
  DemoAuthProvider,
} from "./orchestra-auth-context";

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

/**
 * App-wide client providers. Clerk wraps the tree only when publishable key is set
 * (AUTH_MODE=clerk on the API). Otherwise demo stubs remain.
 */
export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  const inner = (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );

  if (!clerkEnabled) {
    return <DemoAuthProvider>{inner}</DemoAuthProvider>;
  }

  return (
    <ClerkProvider>
      <ClerkAuthBridge>
        <ClerkAuthStateProvider>{inner}</ClerkAuthStateProvider>
      </ClerkAuthBridge>
    </ClerkProvider>
  );
}
