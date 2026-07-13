"use client";

import Link from "next/link";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { springConfig } from "@/lib/animations";

const navLinks = [
  { href: "#how", label: "How it works" },
  { href: "#outcomes", label: "Outcomes" },
  { href: "#faq", label: "FAQ" },
  { href: "/join", label: "Join as talent" },
];

export default function Header() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <a href="#main-content" className="skip-to-main">
        Skip to main content
      </a>
      <header className="sticky top-0 z-50 bg-background border-b border-border">
        <div className="max-w-6xl mx-auto px-8 lg:px-12 h-16 flex items-center justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <Link href="/" className="flex items-center gap-3">
              <div className="w-2 h-2 bg-primary rounded-full" aria-hidden="true" />
              <span className="font-serif text-lg font-bold text-foreground">
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
                whileHover={{ y: -2 }}
              >
                <Link
                  href={l.href}
                  className="text-sm font-light text-muted-foreground hover:text-foreground transition-colors duration-300 relative group"
                >
                  {l.label}
                  <motion.span
                    className="absolute bottom-0 left-0 h-px bg-foreground"
                    initial={{ scaleX: 0, transformOrigin: "left" }}
                    whileHover={{ scaleX: 1 }}
                    transition={springConfig.hover}
                  />
                </Link>
              </motion.div>
            ))}
          </nav>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            whileHover={{ scale: 1.05, boxShadow: "0 10px 25px rgba(0,0,0,0.1)" }}
            whileTap={{ scale: 0.95 }}
          >
            <Link
              href="/start"
              className="hidden md:inline-flex items-center h-9 px-5 bg-primary text-primary-foreground rounded-sm text-sm font-semibold hover:opacity-90 transition-opacity duration-300"
            >
              Begin
            </Link>
          </motion.div>

          {/* Mobile toggle */}
          <button
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen(!open)}
            className="md:hidden flex flex-col justify-center gap-1.5 w-8 h-8"
          >
            <span className={open ? "block h-px bg-foreground transition-transform origin-center rotate-45 translate-y-[5px]" : "block h-px bg-foreground transition-transform origin-center"} />
            <span className={open ? "block h-px bg-foreground transition-opacity opacity-0" : "block h-px bg-foreground transition-opacity"} />
            <span className={open ? "block h-px bg-foreground transition-transform origin-center -rotate-45 -translate-y-[5px]" : "block h-px bg-foreground transition-transform origin-center"} />
          </button>
        </div>

        <AnimatePresence>
          {open && (
            <motion.div
              className="md:hidden border-t border-border bg-background"
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
            >
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
                  className="inline-flex items-center justify-center h-9 px-5 bg-primary text-primary-foreground rounded-sm text-xs font-semibold"
                >
                  Begin
                </Link>
              </nav>
            </motion.div>
          )}
        </AnimatePresence>
      </header>
    </>
  );
}
