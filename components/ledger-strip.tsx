"use client";

import type { LedgerState, OrderStatus } from "@/lib/types";

/** Coarse client-facing steps: Held → Reserved → Released (no payout math). */
export const LEDGER_STRIP_STEPS = [
  { state: "funds_authorized" as const, label: "Held" },
  { state: "milestone_reserved" as const, label: "Reserved" },
  { state: "payout_released" as const, label: "Released" },
] as const;

export type LedgerStripStepState = (typeof LEDGER_STRIP_STEPS)[number]["state"];

const LEDGER_STEP_LABEL: Record<LedgerStripStepState, string> = {
  funds_authorized: "Held",
  milestone_reserved: "Reserved",
  payout_released: "Released",
};

/**
 * Prefer Spine-persisted `ledgerState` from GET /orders/{id}.
 * Fallback maps order status when the field is absent (mocks / legacy).
 */
export function ledgerStateFromOrder(input: {
  orderStatus: OrderStatus;
  deliveryAcceptedAt?: string | null;
  ledgerState?: LedgerState | null;
}): LedgerState {
  if (input.ledgerState) {
    return input.ledgerState;
  }

  const { orderStatus, deliveryAcceptedAt } = input;

  if (orderStatus === "cancelled") {
    return "refunded";
  }

  if (orderStatus === "closed" || deliveryAcceptedAt) {
    return "payout_released";
  }

  if (orderStatus === "confirmed") {
    return "funds_authorized";
  }

  // assembling_team stays Held until mutual start — only advance past Held
  // when delivery is active (mutual start happened) or further along.
  if (
    orderStatus === "delivery_active" ||
    orderStatus === "under_quality_check" ||
    orderStatus === "delivered" ||
    orderStatus === "amendment_pending" ||
    orderStatus === "escalated"
  ) {
    return "milestone_reserved";
  }

  // assembling_team (and unknown): still Held after confirm, not yet reserved
  return "funds_authorized";
}

function stepIndexForState(state: LedgerState): number {
  if (state === "payout_released") return 2;
  if (
    state === "milestone_reserved" ||
    state === "worker_payable" ||
    state === "tds_deducted"
  ) {
    return 1;
  }
  if (state === "funds_authorized") return 0;
  // unfunded | refund_pending | refunded — no active step
  return -1;
}

export type LedgerStripProps = {
  /** Preferred: Spine-persisted state from the order API. */
  ledgerState?: LedgerState | null;
  orderStatus: OrderStatus;
  /** When set (e.g. delivery.accepted_at), funds show as Released if no ledgerState. */
  deliveryAcceptedAt?: string | null;
  className?: string;
};

/**
 * Presentational mock ledger strip for Track Z to mount on the order tracker.
 *
 * @example
 * ```tsx
 * import { LedgerStrip } from "@/components/ledger-strip";
 * <LedgerStrip
 *   ledgerState={order.ledger_state}
 *   orderStatus={order.status}
 * />
 * ```
 */
export function LedgerStrip({
  ledgerState,
  orderStatus,
  deliveryAcceptedAt,
  className = "",
}: LedgerStripProps) {
  const resolved = ledgerStateFromOrder({
    ledgerState,
    orderStatus,
    deliveryAcceptedAt,
  });
  const activeIndex = stepIndexForState(resolved);
  const isTerminalRefund =
    resolved === "refunded" || resolved === "refund_pending";

  return (
    <div
      className={`border border-border bg-card px-4 py-3 ${className}`.trim()}
      role="status"
      aria-label={`Funds status: ${
        isTerminalRefund
          ? "Refunded"
          : activeIndex >= 0
            ? LEDGER_STEP_LABEL[LEDGER_STRIP_STEPS[activeIndex].state]
            : "Unfunded"
      }`}
    >
      <p className="text-xs text-muted-foreground mb-2 tracking-wide uppercase">
        Funds
      </p>
      <ol className="flex items-center gap-0 w-full">
        {LEDGER_STRIP_STEPS.map((step, index) => {
          const reached = activeIndex >= 0 && index <= activeIndex;
          const current = index === activeIndex;
          return (
            <li key={step.state} className="flex items-center flex-1 min-w-0">
              <div className="flex flex-col items-center gap-1 min-w-0 flex-1">
                <span
                  className={`h-2 w-2 rounded-full shrink-0 ${
                    current
                      ? "bg-primary"
                      : reached
                        ? "bg-primary/60"
                        : "bg-border"
                  }`}
                  aria-hidden
                />
                <span
                  className={`text-xs truncate ${
                    current
                      ? "text-foreground font-medium"
                      : reached
                        ? "text-muted-foreground"
                        : "text-muted-foreground/60"
                  }`}
                >
                  {step.label}
                </span>
              </div>
              {index < LEDGER_STRIP_STEPS.length - 1 && (
                <div
                  className={`h-px flex-1 mx-1 min-w-[1rem] ${
                    activeIndex > index ? "bg-primary/60" : "bg-border"
                  }`}
                  aria-hidden
                />
              )}
            </li>
          );
        })}
      </ol>
      {isTerminalRefund && (
        <p className="text-xs text-muted-foreground mt-2">Refunded</p>
      )}
    </div>
  );
}
