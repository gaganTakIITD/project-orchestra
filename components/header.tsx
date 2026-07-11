"use client";

import Link from "next/link";
import { useState } from "react";

const navLinks = [
  { href: "#how", label: "How it works" },
  { href: "#outcomes", label: "Outcomes" },
  { href: "#faq", label: "FAQ" },
  { href: "/join", label: "Join as talent" },
];

export default function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-background border-b-2 border-foreground">
      <div className="max-w-7xl mx-auto px-6 lg:px-8 h-16 flex items-center justify-between">

        <Link href="/" className="flex items-center gap-3">
          <div className="w-6 h-6 bg-primary border border-foreground" aria-hidden="true" />
          <span className="text-xs font-mono font-bold tracking-widest uppercase text-foreground">
            Orchestra
          </span>
        </Link>

        <nav className="hidden md:flex items-center gap-8" aria-label="Primary">
          {navLinks.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className="text-xs font-mono tracking-widest uppercase text-foreground font-semibold hover:text-primary transition-colors"
            >
              {l.label}
            </Link>
          ))}
        </nav>

        <Link
          href="/start"
          className="hidden md:inline-flex items-center h-9 px-5 bg-primary text-primary-foreground text-xs font-mono tracking-widest uppercase font-bold hover:opacity-80 transition-opacity border border-primary-foreground"
        >
          Describe outcome
        </Link>

        {/* Mobile toggle — pure CSS bars, no lucide dependency */}
        <button
          aria-label={open ? "Close menu" : "Open menu"}
          onClick={() => setOpen(!open)}
          className="md:hidden flex flex-col justify-center gap-1.5 w-8 h-8"
        >
          <span className={`block h-px bg-foreground transition-transform origin-center ${open ? "rotate-45 translate-y-[5px]" : ""}`} />
          <span className={`block h-px bg-foreground transition-opacity ${open ? "opacity-0" : ""}`} />
          <span className={`block h-px bg-foreground transition-transform origin-center ${open ? "-rotate-45 -translate-y-[5px]" : ""}`} />
        </button>
      </div>

      {open && (
        <div className="md:hidden border-t border-border bg-background">
          <nav className="flex flex-col px-6 py-5 gap-5" aria-label="Mobile">
            {navLinks.map((l) => (
              <Link
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                className="text-xs font-mono tracking-widest uppercase text-muted-foreground hover:text-foreground transition-colors"
              >
                {l.label}
              </Link>
            ))}
            <Link
              href="/start"
              onClick={() => setOpen(false)}
              className="inline-flex items-center justify-center h-9 px-5 bg-primary text-primary-foreground text-xs font-mono tracking-widest uppercase"
            >
              Describe outcome
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
