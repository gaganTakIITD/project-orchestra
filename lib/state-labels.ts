/**
 * Dual-view state labels — "one task, two languages" (Design Notes §11, Diagram E9).
 *
 * The same backend Task/Order state renders differently for the client (outcome
 * language, internal failures hidden) vs the worker (task language). Keep these
 * maps here so v0's UI and any future surface stay consistent.
 */
import type { OrderStatus, TaskStatus } from "./types";

export const taskStatusClientLabel: Record<TaskStatus, string> = {
  blocked: "Queued",
  ready: "Finding your team",
  invited: "Finding your team",
  interest_pool: "Team forming",
  priority_active: "Starting soon",
  start_requested: "Starting soon",
  mutual_start: "Work started",
  in_progress: "In progress",
  submitted: "In review",
  rework: "In progress", // internal failure hidden from client
  completed: "Delivered",
  cancelled: "Cancelled",
  released: "—",
};

export const taskStatusWorkerLabel: Record<TaskStatus, string> = {
  blocked: "Locked",
  ready: "Available",
  invited: "You're invited",
  interest_pool: "Interest received",
  priority_active: "You have priority",
  start_requested: "Start requested",
  mutual_start: "Start confirmed",
  in_progress: "Deliver now",
  submitted: "Under QA",
  rework: "Fix checklist",
  completed: "Passed + paid",
  cancelled: "Cancelled",
  released: "Released",
};

export const orderStatusClientLabel: Record<OrderStatus, string> = {
  confirmed: "Confirmed",
  assembling_team: "Assembling your team",
  delivery_active: "In progress",
  under_quality_check: "Final quality check",
  delivered: "Ready to review",
  closed: "Completed",
  amendment_pending: "Amendment review",
  escalated: "In progress",
  cancelled: "Cancelled",
};

/** Coarse status tone for badges/pills. v0 can map these to colors. */
export type StatusTone = "neutral" | "info" | "active" | "review" | "success" | "danger";

export const taskStatusTone: Record<TaskStatus, StatusTone> = {
  blocked: "neutral",
  ready: "info",
  invited: "info",
  interest_pool: "info",
  priority_active: "active",
  start_requested: "active",
  mutual_start: "active",
  in_progress: "active",
  submitted: "review",
  rework: "danger",
  completed: "success",
  cancelled: "danger",
  released: "neutral",
};
