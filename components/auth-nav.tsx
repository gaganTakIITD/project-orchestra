"use client";

import Link from "next/link";
import {
  SignInButton,
  SignUpButton,
  UserButton,
} from "@clerk/nextjs";
import { useOrchestraAuth } from "@/lib/use-orchestra-auth";

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export default function AuthNav({ compact = false }: { compact?: boolean }) {
  const { isReady, isSignedIn } = useOrchestraAuth();

  if (!clerkEnabled) {
    return null;
  }

  if (!isReady) {
    return <div className="h-9 w-9 rounded-full bg-muted animate-pulse" aria-hidden />;
  }

  if (!isSignedIn) {
    return (
      <div className={`flex items-center ${compact ? "flex-col gap-3 w-full" : "gap-2"}`}>
        <SignInButton mode="redirect" forceRedirectUrl="/account">
          <button
            type="button"
            className={
              compact
                ? "w-full text-xs font-mono tracking-widest uppercase text-muted-foreground hover:text-foreground transition-colors"
                : "inline-flex items-center h-9 px-4 rounded-full text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            }
          >
            Sign in
          </button>
        </SignInButton>
        {!compact && (
          <SignUpButton mode="redirect" forceRedirectUrl="/account">
            <button
              type="button"
              className="inline-flex items-center h-9 px-4 bg-secondary text-secondary-foreground rounded-full text-sm font-semibold hover:opacity-85 transition-opacity"
            >
              Sign up
            </button>
          </SignUpButton>
        )}
      </div>
    );
  }

  return (
    <div className={`flex items-center ${compact ? "flex-col gap-4 w-full" : "gap-3"}`}>
      <Link
        href="/account"
        className={
          compact
            ? "text-xs font-mono tracking-widest uppercase text-muted-foreground hover:text-foreground transition-colors"
            : "text-sm text-muted-foreground hover:text-foreground transition-colors"
        }
      >
        Account
      </Link>
      <UserButton
        appearance={{
          elements: {
            avatarBox: "h-9 w-9",
          },
        }}
      />
    </div>
  );
}
