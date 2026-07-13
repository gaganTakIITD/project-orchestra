"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { UserButton } from "@clerk/nextjs";
import { useMe } from "@/lib/hooks";
import type { UserRole } from "@/lib/types";

const clerkEnabled = Boolean(process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY);

type NavLink = { href: string; label: string };

const PORTAL_HOME: Record<UserRole, string> = {
  client: "/orders",
  worker: "/worker",
  admin: "/admin",
};

const ROLE_LINKS: Record<UserRole, NavLink[]> = {
  client: [
    { href: "/orders", label: "My outcomes" },
    { href: "/start", label: "New outcome" },
  ],
  worker: [{ href: "/worker", label: "Inbox" }],
  admin: [{ href: "/admin", label: "Console" }],
};

function isActive(pathname: string, href: string) {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function WorkspaceHeader() {
  const { data: me } = useMe();
  const [open, setOpen] = useState(false);

  const role: UserRole = me?.role ?? "client";
  const homeHref = PORTAL_HOME[role];
  const links: NavLink[] = [...ROLE_LINKS[role], { href: "/account", label: "Account" }];
  const pathname = usePathname() ?? "";

  return (
    <>
      <a href="#main-content" className="skip-to-main">
        Skip to main content
      </a>
      <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6 lg:px-10">
          <Link href={homeHref} className="flex items-center gap-3" aria-label="Orchestra home">
            <span className="h-2 w-2 rounded-full bg-primary" aria-hidden="true" />
            <span className="font-serif text-lg font-bold text-foreground">Orchestra</span>
            <span className="hidden text-[10px] font-mono uppercase tracking-widest text-muted-foreground sm:inline">
              {role} workspace
            </span>
          </Link>

          <nav className="hidden items-center gap-8 md:flex" aria-label="Primary">
            {links.map((l) => {
              const active = isActive(pathname, l.href);
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  aria-current={active ? "page" : undefined}
                  className={
                    "relative text-sm transition-colors duration-200 " +
                    (active
                      ? "font-semibold text-foreground"
                      : "font-light text-muted-foreground hover:text-foreground")
                  }
                >
                  {l.label}
                  {active ? (
                    <span
                      aria-hidden="true"
                      className="absolute -bottom-1 left-0 h-px w-full bg-primary"
                    />
                  ) : null}
                </Link>
              );
            })}
          </nav>

          <div className="flex items-center gap-3">
            <div className="hidden md:block">
              <AccountControl role={role} name={me?.full_name} />
            </div>
            <button
              type="button"
              aria-label={open ? "Close menu" : "Open menu"}
              aria-expanded={open}
              onClick={() => setOpen((v) => !v)}
              className="flex h-9 w-9 flex-col items-center justify-center gap-1.5 md:hidden"
            >
              <span className={"block h-px w-5 bg-foreground transition-transform " + (open ? "translate-y-[7px] rotate-45" : "")} />
              <span className={"block h-px w-5 bg-foreground transition-opacity " + (open ? "opacity-0" : "")} />
              <span className={"block h-px w-5 bg-foreground transition-transform " + (open ? "-translate-y-[7px] -rotate-45" : "")} />
            </button>
          </div>
        </div>

        {open ? (
          <div className="border-t border-border bg-background md:hidden">
            <nav className="flex flex-col gap-4 px-6 py-5" aria-label="Mobile">
              {links.map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  onClick={() => setOpen(false)}
                  aria-current={isActive(pathname, l.href) ? "page" : undefined}
                  className={
                    "text-sm " +
                    (isActive(pathname, l.href)
                      ? "font-semibold text-foreground"
                      : "font-light text-muted-foreground")
                  }
                >
                  {l.label}
                </Link>
              ))}
              <div className="pt-1">
                <AccountControl role={role} name={me?.full_name} />
              </div>
            </nav>
          </div>
        ) : null}
      </header>
    </>
  );
}

/**
 * Clerk's <UserButton/> requires a ClerkProvider, which is only mounted when a
 * publishable key is set (see lib/providers.tsx). In mock/demo mode we fall
 * back to an initials avatar that links to /account so the nav still works.
 */
function AccountControl({ role, name }: { role: UserRole; name?: string }) {
  if (clerkEnabled) {
    return <UserButton afterSignOutUrl="/" />;
  }

  const initial = (name?.trim()?.[0] ?? role[0] ?? "?").toUpperCase();
  return (
    <Link
      href="/account"
      aria-label="Account"
      className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary text-xs font-semibold text-secondary-foreground transition-opacity hover:opacity-90"
    >
      {initial}
    </Link>
  );
}
