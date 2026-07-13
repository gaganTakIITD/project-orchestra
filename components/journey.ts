/**
 * Journey stage definitions + status->stage mapping.
 *
 * NOTE ON OWNERSHIP: the v0 handoff assumed these helpers lived in
 * `lib/journey.ts`, but that module was never shipped to this branch and the
 * guardrails forbid editing `lib/**`. They live here in `components/**`
 * instead. If a real `lib/journey.ts` lands later, swap the imports over — the
 * shapes (`JourneyStage`, `clientStageForOrder`, `workerStageForTask`) are the
 * contract the UI depends on.
 */
import type { OrderStatus, TaskStatus } from "@/lib/types";

export interface JourneyStage {
  id: string;
  label: string;
  /** Short helper shown under the label on wide layouts. */
  hint?: string;
}

/** Client-facing outcome journey (outcome language, internal failures hidden). */
export const CLIENT_JOURNEY_STAGES: JourneyStage[] = [
  { id: "scope", label: "Scope", hint: "Describe the outcome" },
  { id: "quote", label: "Proposal", hint: "Fixed price & plan" },
  { id: "team", label: "Team", hint: "We staff the work" },
  { id: "build", label: "In progress", hint: "Delivery underway" },
  { id: "review", label: "Review", hint: "Accept your delivery" },
];

/** Worker-facing task journey (task language). */
export const WORKER_JOURNEY_STAGES: JourneyStage[] = [
  { id: "invited", label: "Invited", hint: "Available to you" },
  { id: "accepted", label: "Accepted", hint: "Interest confirmed" },
  { id: "start", label: "Start", hint: "Charter agreed" },
  { id: "deliver", label: "Deliver", hint: "Do the work" },
  { id: "review", label: "QA & payout", hint: "Reviewed and paid" },
];

/** Map an order status to a client journey stage id. */
export function clientStageForOrder(status: OrderStatus): string {
  switch (status) {
    case "confirmed":
    case "assembling_team":
      return "team";
    case "delivery_active":
    case "escalated":
    case "amendment_pending":
    case "under_quality_check":
      return "build";
    case "delivered":
    case "closed":
      return "review";
    case "cancelled":
      return "build";
    default:
      return "team";
  }
}

/** Map a task status to a worker journey stage id. */
export function workerStageForTask(status: TaskStatus): string {
  switch (status) {
    case "blocked":
    case "ready":
    case "invited":
      return "invited";
    case "interest_pool":
    case "priority_active":
    case "start_requested":
      return "accepted";
    case "mutual_start":
      return "start";
    case "in_progress":
    case "rework":
      return "deliver";
    case "submitted":
    case "completed":
      return "review";
    case "cancelled":
    case "released":
      return "invited";
    default:
      return "invited";
  }
}
