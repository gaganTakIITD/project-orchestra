"use client";

import { SignUp } from "@clerk/nextjs";
import Link from "next/link";

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

export default function SignUpPage() {
  if (!clerkEnabled) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-background px-4 text-center">
        <h1 className="text-2xl font-semibold">Sign-up not configured</h1>
        <p className="max-w-md text-muted-foreground">
          Add Clerk keys to enable Stage D auth. Demo stubs remain the default
          product path until then.
        </p>
        <Link href="/" className="underline">
          Back home
        </Link>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-background px-4">
      <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" />
    </main>
  );
}
