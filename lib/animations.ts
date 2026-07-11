// Animation configurations and utilities for Framer Motion
// Inspired by umanodesign.studio's polished motion language

export const springConfig = {
  // Snappy scroll reveals - Bauhaus bold
  scrollReveal: {
    type: "spring" as const,
    stiffness: 100,
    damping: 20,
    mass: 1,
  },
  // Responsive hover effects
  hover: {
    type: "spring" as const,
    stiffness: 150,
    damping: 18,
    mass: 0.8,
  },
  // Smooth accordion expand/collapse
  accordion: {
    type: "spring" as const,
    stiffness: 120,
    damping: 22,
    mass: 1,
  },
  // Gentle, slow animations for subtle reveals
  gentle: {
    type: "spring" as const,
    stiffness: 60,
    damping: 15,
    mass: 1.2,
  },
  // Snappy, tight animations for interactive elements
  snappy: {
    type: "spring" as const,
    stiffness: 180,
    damping: 25,
    mass: 0.6,
  },
  // Page transition animations
  pageTransition: {
    type: "spring" as const,
    stiffness: 90,
    damping: 18,
    mass: 1,
  },
};

// Scroll reveal variants - fade + slide in
export const scrollRevealVariants = {
  hidden: (custom: number = 0) => ({
    opacity: 0,
    y: 60,
    transition: { delay: custom * 0.1 },
  }),
  visible: (custom: number = 0) => ({
    opacity: 1,
    y: 0,
    transition: {
      ...springConfig.scrollReveal,
      delay: custom * 0.1,
    },
  }),
};

// Slide from sides variants
export const slideVariants = {
  slideLeft: {
    hidden: { opacity: 0, x: -100 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { ...springConfig.scrollReveal },
    },
  },
  slideRight: {
    hidden: { opacity: 0, x: 100 },
    visible: {
      opacity: 1,
      x: 0,
      transition: { ...springConfig.scrollReveal },
    },
  },
};

// Stagger container for cascading animations
export const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.1,
    },
  },
};

// Individual item within stagger container
export const staggerItem = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      type: "spring" as const,
      stiffness: 100,
      damping: 20,
      mass: 1,
    },
  },
};

// Hover effect for buttons
export const buttonHoverVariants = {
  initial: { scale: 1 },
  hover: {
    scale: 1.04,
    transition: { ...springConfig.hover },
  },
  tap: { scale: 0.98 },
};

// Hover effect for cards
export const cardHoverVariants = {
  initial: { y: 0, boxShadow: "0 1px 3px rgba(0,0,0,0.1)" },
  hover: {
    y: -4,
    boxShadow: "0 20px 25px rgba(0,0,0,0.15)",
    transition: { ...springConfig.hover },
  },
};

// Link underline animation
export const underlineVariants = {
  initial: { scaleX: 0, transformOrigin: "left" },
  hover: {
    scaleX: 1,
    transition: { duration: 0.3, ease: "easeOut" },
  },
};

/**
 * Get animation config respecting prefers-reduced-motion
 * Returns instant transitions for users with motion preferences
 */
export function getMotionConfig(config: any, respectMotionPreference = true) {
  if (!respectMotionPreference) return config;
  
  if (typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return { duration: 0 };
  }
  
  return config;
}
