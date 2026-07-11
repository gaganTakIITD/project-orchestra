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
    <footer className="border-t border-border bg-background" ref={ref}>
      <div className="max-w-6xl mx-auto px-8 lg:px-12 py-20 lg:py-32">

        <motion.div 
          className="grid grid-cols-2 md:grid-cols-3 gap-16 mb-16 pb-16 border-b border-border"
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={{
            hidden: { opacity: 0 },
            visible: {
              opacity: 1,
              transition: {
                staggerChildren: 0.1,
                delayChildren: 0.1,
              },
            },
          }}
        >
          {/* Brand */}
          <motion.div 
            className="col-span-2 md:col-span-1 flex flex-col gap-4"
            variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
          >
            <Link href="/" className="inline-block">
              <span className="font-serif text-lg font-light text-foreground">
                Orchestra
              </span>
            </Link>
            <p className="text-sm text-muted-foreground font-light leading-relaxed">
              Describe your outcome. We deliver it.
            </p>
          </motion.div>

          {/* Product */}
          <motion.div 
            className="flex flex-col gap-4"
            variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
          >
            <p className="text-xs text-muted-foreground uppercase tracking-widest font-light">Product</p>
            <ul className="flex flex-col gap-3">
              {product.map((l) => (
                <motion.li key={l.href} whileHover={{ opacity: 0.6 }}>
                  <Link href={l.href} className="text-sm text-foreground hover:text-primary transition-colors font-light">
                    {l.label}
                  </Link>
                </motion.li>
              ))}
            </ul>
          </motion.div>

          {/* Company */}
          <motion.div 
            className="flex flex-col gap-4"
            variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
          >
            <p className="text-xs text-muted-foreground uppercase tracking-widest font-light">Company</p>
            <ul className="flex flex-col gap-3">
              {company.map((l) => (
                <motion.li key={l.href} whileHover={{ opacity: 0.6 }}>
                  <Link href={l.href} className="text-sm text-foreground hover:text-primary transition-colors font-light">
                    {l.label}
                  </Link>
                </motion.li>
              ))}
            </ul>
          </motion.div>
        </motion.div>

        <motion.div 
          className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-xs text-muted-foreground font-light"
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : { opacity: 0 }}
          transition={{ duration: 0.8, delay: 0.3 }}
        >
          <p>
            &copy; {currentYear} Project Orchestra. All rights reserved.
          </p>
          <p>
            Building outcomes with verified talent.
          </p>
        </motion.div>

      </div>
    </footer>
  );
}
