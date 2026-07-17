import type { ReactNode } from "react";

/** Account hub depends on Clerk session — skip static prerender. */
export const dynamic = "force-dynamic";

export default function AccountLayout({ children }: { children: ReactNode }) {
  return children;
}
