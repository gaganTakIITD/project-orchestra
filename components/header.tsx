"use client";

import Link from "next/link";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const navLinks = [
  { href: "#how", label: "How it works" },
  { href: "#outcomes", label: "Outcomes" },
  { href: "#faq", label: "FAQ" },
  { href: "/join", label: "Join as talent" },
];

export default function Header() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-background border-b border-border">
      <div className="max-w-6xl mx-auto px-8 lg:px-12 h-16 flex items-center justify-between">

        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <Link href="/" className="flex items-center gap-2">
            <span className="font-serif text-lg font-light text-foreground">
              Orchestra
            </span>
          </Link>
        </motion.div>

        <nav className="hidden md:flex items-center gap-12" aria-label="Primary">
          {navLinks.map((l, idx) => (
            <motion.div
              key={l.href}
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: idx * 0.05 }}
            >
              <Link
                href={l.href}
                className="text-sm font-light text-muted-foreground hover:text-foreground transition-colors duration-300"
              >
                {l.label}
              </Link>
            </motion.div>
          ))}
        </nav>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
          whileHover={{ opacity: 0.8 }}
          whileTap={{ scale: 0.98 }}
        >
          <Link
            href="/start"
            className="hidden md:inline-flex items-center h-10 px-6 border border-foreground text-foreground text-sm font-light hover:bg-foreground hover:text-background transition-colors duration-300"
          >
            Begin
          </Link>
        </motion.div>

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
