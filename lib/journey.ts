/**
 * Journey / stepper model — the shared "where am I?" map for the workspace.
 *
 * Screens must NOT hardcode stage lists. They render `<JourneyStepper/>` from
 * these ordered stages and derive the active stage from backend state
 * (`OrderStatus` for the client tracker, `TaskStatus` for the worker job card).
 *
 * Client-facing status *labels* live in `lib/state-labels.ts`; this file owns the
 * coarser *stage grouping* used by the stepper. Keep the two consistent.
 */
import type { OrderStatus, TaskStatus } from "./types";

export interface JourneyStage {
  id: string;
  label: string;
  /** Optional helper shown under the label on wide layouts. */
  hint?: string;
}

// ---------------------------------------------------------------------------
// Client journey: Scope -> Quote -> Confirm -> Team -> In progress -> Delivery -> Accepted
// ---------------------------------------------------------------------------

export const CLIENT_JOURNEY_STAGES = [
  { id: "scope", label: "Scope" },
  { id: "quote", label: "Quote" },
  { id: "confirm", label: "Confirm" },
  { id: "team", label: "Team" },
  { id: "progress", label: "In progress" },
  { id: "delivery", label: "Delivery" },
  { id: "accepted", label: "Accepted" },
] as const;

export type ClientStageId = (typeof CLIENT_JOURNEY_STAGES)[number]["id"];

/**
 * Order tracker stage, derived from `OrderStatus`.
 *
 * `cancelled` has no natural place on a forward journey — it maps to the final
 * stage so naive callers still get a valid id, but screens should check
 * `isOrderCancelled(status)` first and render a cancelled banner instead.
 */
const ORDER_STATUS_TO_CLIENT_STAGE: Record<OrderStatus, ClientStageId> = {
  confirmed: "team",
  assembling_team: "team",
  delivery_active: "progress",
  under_quality_check: "progress",
  amendment_pending: "progress",
  escalated: "progress",
  delivered: "delivery",
  closed: "accepted",
  cancelled: "accepted",
};

/** Stepper stage id for an order tracker screen. */
export function clientStageForOrder(status: OrderStatus): ClientStageId {
  return ORDER_STATUS_TO_CLIENT_STAGE[status];
}

export function isOrderCancelled(status: OrderStatus): boolean {
  return status === "cancelled";
}

// ---------------------------------------------------------------------------
// Worker journey: Invited -> Accepted -> In progress -> QA -> Completed
// ---------------------------------------------------------------------------

export const WORKER_JOURNEY_STAGES = [
  { id: "invited", label: "Invited" },
  { id: "accepted", label: "Accepted" },
  { id: "progress", label: "In progress" },
  { id: "qa", label: "QA" },
  { id: "completed", label: "Completed" },
] as const;

export type WorkerStageId = (typeof WORKER_JOURNEY_STAGES)[number]["id"];

/**
 * Worker job-card stage, derived from `TaskStatus`.
 * `null` = task is not yet on the worker's journey (blocked) or is terminal
 * (cancelled); the caller decides how to render those.
 */
const TASK_STATUS_TO_WORKER_STAGE: Record<TaskStatus, WorkerStageId | null> = {
  blocked: null,
  ready: "invited",
  invited: "invited",
  interest_pool: "invited",
  priority_active: "accepted",
  start_requested: "accepted",
  mutual_start: "accepted",
  in_progress: "progress",
  rework: "progress",
  submitted: "qa",
  completed: "completed",
  released: "completed",
  cancelled: null,
};

/** Stepper stage id for a worker job card (null when off-journey/terminal). */
export function workerStageForTask(status: TaskStatus): WorkerStageId | null {
  return TASK_STATUS_TO_WORKER_STAGE[status];
}

// ---------------------------------------------------------------------------
// Shared: index lookup for done / current / upcoming rendering
// ---------------------------------------------------------------------------

/** 0-based position of a stage id within an ordered stage list (-1 if absent). */
export function stageIndex(stages: readonly JourneyStage[], id: string): number {
  return stages.findIndex((s) => s.id === id);
}
