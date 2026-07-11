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
      {/* Forest green footer — large headline + nav grid below */}
      <div className="bg-secondary">
        {/* Large headline block */}
        <div className="max-w-6xl mx-auto px-8 lg:px-12 pt-20 lg:pt-28 pb-12 border-b border-secondary-foreground/10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
            transition={{ duration: 0.9, ease: "easeOut" }}
          >
            <h2 className="font-serif text-5xl sm:text-6xl lg:text-7xl font-bold text-secondary-foreground leading-tight max-w-3xl">
              Outcome delivery, engineered.
            </h2>
          </motion.div>
        </div>

        {/* Navigation grid */}
        <div className="max-w-6xl mx-auto px-8 lg:px-12 py-12">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.9, delay: 0.15 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-10"
          >
            {/* Product */}
            <div>
              <p className="text-xs text-primary uppercase tracking-widest font-semibold mb-5">Navigate</p>
              <ul className="flex flex-col gap-3">
                {product.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="text-sm text-secondary-foreground/80 hover:text-secondary-foreground transition-colors">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Company */}
            <div>
              <p className="text-xs text-primary uppercase tracking-widest font-semibold mb-5">Company</p>
              <ul className="flex flex-col gap-3">
                {company.map((l) => (
                  <li key={l.href}>
                    <Link href={l.href} className="text-sm text-secondary-foreground/80 hover:text-secondary-foreground transition-colors">
                      {l.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>

            {/* Social */}
            <div>
              <p className="text-xs text-primary uppercase tracking-widest font-semibold mb-5">Socials</p>
              <ul className="flex flex-col gap-3">
                {social.map((l) => (
                  <li key={l.href}>
                    <a href={l.href} target="_blank" rel="noopener noreferrer" className="text-sm text-secondary-foreground/80 hover:text-secondary-foreground transition-colors">
                      {l.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>

            {/* CTA */}
            <div className="flex flex-col justify-between">
              <div>
                <p className="text-xs text-primary uppercase tracking-widest font-semibold mb-5">Get started</p>
                <p className="text-sm text-secondary-foreground/70 leading-relaxed mb-6">
                  IIT Delhi verified talent, AI-enforced quality.
                </p>
              </div>
              <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.95 }}>
                <Link
                  href="/start"
                  className="inline-block px-6 py-2.5 border border-primary text-primary rounded-full text-xs font-semibold uppercase tracking-wide hover:bg-primary hover:text-primary-foreground transition-colors"
                >
                  Begin a project
                </Link>
              </motion.div>
            </div>
          </motion.div>
        </div>

        {/* Bottom bar */}
        <div className="max-w-6xl mx-auto px-8 lg:px-12 py-6 border-t border-secondary-foreground/10">
          <motion.div
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : { opacity: 0 }}
            transition={{ duration: 0.9, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-secondary-foreground/50"
          >
            <p>&copy; {currentYear} Project Orchestra. All rights reserved.</p>
            <p>Global talent, verified outcomes.</p>
          </motion.div>
        </div>
      </div>

    </footer>
  );
}
