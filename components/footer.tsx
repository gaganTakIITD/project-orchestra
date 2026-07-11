"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";

const product = [
  { href: "/start", label: "For clients" },
  { href: "/join", label: "For talent" },
  { href: "#how", label: "How it works" },
  { href: "#outcomes", label: "Outcomes" },
];

const company = [
  { href: "#faq", label: "FAQ" },
  { href: "/blog", label: "Blog" },
  { href: "/privacy", label: "Privacy" },
  { href: "/terms", label: "Terms" },
];

const social = [
  { href: "https://x.com", label: "X (Twitter)" },
  { href: "https://github.com", label: "GitHub" },
  { href: "https://linkedin.com", label: "LinkedIn" },
];

export default function Footer() {
  const currentYear = new Date().getFullYear();
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <footer className="bg-background" ref={ref}>
      {/* Dark teal section with light text */}
      <div className="bg-secondary py-20 lg:py-28">
        <div className="max-w-6xl mx-auto px-8 lg:px-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.9 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-12"
          >
            {/* Brand */}
            <div className="col-span-2 md:col-span-1">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-2 h-2 bg-primary rounded-full" aria-hidden="true" />
                <span className="font-serif text-lg font-bold text-secondary-foreground">
                  Orchestra
                </span>
              </div>
              <p className="text-sm text-secondary-foreground/80">
                Describe your outcome. We deliver it.
              </p>
            </div>

            {/* Product */}
            <div>
              <p className="text-xs text-primary uppercase tracking-widest font-semibold mb-4">Product</p>
              <ul className="flex flex-col gap-3">
                {product.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="text-sm text-secondary-foreground hover:text-primary transition-colors">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Company */}
            <div>
              <p className="text-xs text-primary uppercase tracking-widest font-semibold mb-4">Company</p>
              <ul className="flex flex-col gap-3">
                {company.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="text-sm text-secondary-foreground hover:text-primary transition-colors">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Social & CTA */}
            <div>
              <p className="text-xs text-primary uppercase tracking-widest font-semibold mb-4">Follow</p>
              <ul className="flex flex-col gap-3 mb-6">
                {social.map((l) => (
                  <li key={l.href}>
                    <a href={l.href} target="_blank" rel="noopener noreferrer" className="text-sm text-secondary-foreground hover:text-primary transition-colors">
                      {l.label}
                    </a>
                  </li>
                ))}
              </ul>
              <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.95 }}>
                <Link
                  href="/join"
                  className="inline-block px-6 py-2 bg-primary text-primary-foreground rounded-full text-xs font-semibold hover:opacity-85 transition-opacity"
                >
                  Join talent
                </Link>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Light bottom section */}
      <div className="bg-background border-t border-border">
        <div className="max-w-6xl mx-auto px-8 lg:px-12 py-8">
          <motion.div
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : { opacity: 0 }}
            transition={{ duration: 0.9, delay: 0.2 }}
            className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-muted-foreground"
          >
            <p>&copy; {currentYear} Project Orchestra. All rights reserved.</p>
            <p>Built for outcome-driven builders.</p>
          </motion.div>
        </div>
      </div>

    </footer>
  );
}
