"use client";

import type { Amendment } from "@/lib/types";

type Props = {
  amendment: Amendment;
  onApprove?: (id: string) => void;
  onReject?: (id: string) => void;
  busy?: boolean;
};

export function AmendmentCard({ amendment, onApprove, onReject, busy }: Props) {
  const pending =
    amendment.status === "requested" || amendment.status === "priced";

  return (
    <div className="border border-border p-4 space-y-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
            Amendment · {amendment.status}
          </p>
          <p className="text-sm mt-1 whitespace-pre-wrap">
            {amendment.delta_description}
          </p>
        </div>
        {amendment.price_delta ? (
          <p className="text-sm font-mono shrink-0">
            {amendment.price_delta > 0 ? "+" : ""}
            {amendment.price_delta}
          </p>
        ) : null}
      </div>
      {pending && (onApprove || onReject) ? (
        <div className="flex gap-2">
          {onApprove ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => onApprove(amendment.id)}
              className="h-8 px-3 text-xs border border-border bg-foreground text-background disabled:opacity-50"
            >
              Approve
            </button>
          ) : null}
          {onReject ? (
            <button
              type="button"
              disabled={busy}
              onClick={() => onReject(amendment.id)}
              className="h-8 px-3 text-xs border border-border disabled:opacity-50"
            >
              Reject
            </button>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
