"use client";

import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef, ReactNode, memo } from "react";
import { springConfig, staggerContainer } from "@/lib/animations";

interface SectionLayoutProps {
  children: ReactNode;
  id?: string;
  className?: string;
  title?: string;
  description?: string;
  containerClassName?: string;
  variant?: "default" | "dark";
}

/**
 * Standardized section layout component with built-in scroll reveals
 * Handles common patterns: title, description, content with stagger animations
 */
export const SectionLayout = memo(function SectionLayout({
  children,
  id,
  className = "bg-background",
  title,
  description,
  containerClassName = "max-w-6xl mx-auto px-8 lg:px-12 py-20 lg:py-32",
  variant = "default",
}: SectionLayoutProps) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: "0px 0px -100px 0px" });

  return (
    <section id={id} className={className} ref={ref}>
      <div className={containerClassName}>
        {/* Header */}
        {(title || description) && (
          <motion.div
            className="mb-16 md:mb-20"
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={springConfig.scrollReveal}
          >
            {title && (
              <h2 className="font-serif text-5xl sm:text-6xl lg:text-7xl font-bold text-foreground mb-4">
                {title}
              </h2>
            )}
            {description && (
              <p className="text-lg text-muted-foreground max-w-3xl">
                {description}
              </p>
            )}
          </motion.div>
        )}

        {/* Content with stagger */}
        <motion.div
          initial="hidden"
          animate={isInView ? "visible" : "hidden"}
          variants={staggerContainer}
        >
          {children}
        </motion.div>
      </div>
    </section>
  );
});

export default SectionLayout;
