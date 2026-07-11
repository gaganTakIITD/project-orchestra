"use client";

import { SignIn } from "@clerk/nextjs";
import Link from "next/link";

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export default function SignInPage() {
  if (!clerkEnabled) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-4 text-center">
        <h1 className="text-2xl font-semibold">Sign-in not configured</h1>
        <p className="max-w-md text-muted-foreground">
          Set <code>NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code> and API{" "}
          <code>AUTH_MODE=clerk</code> + <code>CLERK_JWKS_URL</code> to enable
          Stage D auth. Until then the product path uses demo client/worker stubs.
        </p>
        <Link href="/" className="underline">
          Back home
        </Link>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" />
    </main>
  );
}
