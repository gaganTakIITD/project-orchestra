// Animation configurations and utilities for Framer Motion
// Inspired by umanodesign.studio's polished motion language

export const springConfig = {
  // Snappy scroll reveals - Bauhaus bold
  scrollReveal: {
    type: "spring",
    stiffness: 100,
    damping: 20,
    mass: 1,
  },
  // Responsive hover effects
  hover: {
    type: "spring",
    stiffness: 150,
    damping: 18,
    mass: 0.8,
  },
  // Smooth accordion expand/collapse
  accordion: {
    type: "spring",
    stiffness: 120,
    damping: 22,
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
    transition: { ...springConfig.scrollReveal },
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
