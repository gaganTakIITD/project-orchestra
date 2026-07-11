/**
 * Centralized data definitions for all components
 * Reduces inline data and improves maintainability
 */

export const navigation = {
  product: [
    { label: "Features", href: "#features" },
    { label: "Pricing", href: "#pricing" },
    { label: "Outcomes", href: "#outcomes" },
  ],
  company: [
    { label: "About", href: "/about" },
    { label: "Blog", href: "/blog" },
    { label: "Careers", href: "/careers" },
  ],
  social: [
    { label: "Twitter", href: "https://twitter.com/orchestrateio" },
    { label: "LinkedIn", href: "https://linkedin.com/company/orchestrate" },
    { label: "GitHub", href: "https://github.com/orchestrate" },
  ],
};

export const faqItems = [
  {
    question: "How long does a typical outcome take?",
    answer: "Most outcomes are completed in 3-8 weeks, depending on scope and complexity. We provide firm deadlines upfront.",
  },
  {
    question: "What if I'm not satisfied with the outcome?",
    answer: "We offer a rework guarantee. If the outcome doesn't meet your acceptance criteria, we rework it or reimburse you—no questions asked.",
  },
  {
    question: "How do you ensure quality?",
    answer: "Every milestone is checked by AI models (Gemini vision and reasoning) against your acceptance criteria before delivery. Plus, all workers are IIT Delhi verified.",
  },
  {
    question: "Can I specify my own team?",
    answer: "Absolutely. We match you with the right specialists from our verified talent pool based on your outcome requirements.",
  },
  {
    question: "What payment terms do you offer?",
    answer: "We typically require 50% upfront to secure the team, with the balance due upon completion.",
  },
];

export const trustPoints = [
  {
    label: "01",
    title: "Campus-verified talent",
    description: "Every worker is verified as a student or recent alumni of IIT Delhi. Real credentials, real skills—not resume inflation.",
  },
  {
    label: "02",
    title: "AI-verified quality",
    description: "Gemini vision and reasoning models check every milestone against your acceptance criteria before it ships to you.",
  },
  {
    label: "03",
    title: "Outcome guarantee",
    description: "We rework or reimburse if your outcome doesn't meet spec. No fine print. Your result is guaranteed.",
  },
];

export const steps = [
  {
    number: 1,
    title: "Describe your outcome",
    description: "Tell us what you need built, designed, or solved. Be as specific as possible about requirements and success criteria.",
  },
  {
    number: 2,
    title: "We plan & staff",
    description: "Our team structures the work, breaks it into milestones, and assigns verified specialists matched to your needs.",
  },
  {
    number: 3,
    title: "AI-verified delivery",
    description: "At each milestone, Gemini checks quality against your criteria. You review and approve before we proceed.",
  },
  {
    number: 4,
    title: "You receive outcome",
    description: "Fully completed, tested, and ready to use. Rework guaranteed if it doesn't meet spec.",
  },
];
