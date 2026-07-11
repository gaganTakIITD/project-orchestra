import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind classes with conditional class support.
 * Used by shadcn/ui components (owned by v0) and shared UI helpers.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
