/**
 * Portal data hooks (client home + scope resume).
 *
 * The handoff referenced `useMyOrders` / `useMyScopes` as shipped hooks, but
 * they never landed in `lib/hooks.ts` and the guardrails forbid editing
 * `lib/**`. These thin wrappers reproduce that surface on top of the existing
 * `lib/hooks` + `lib/api` without changing the contract. When a real list
 * endpoint exists (e.g. GET /orders, GET /chat/sessions), move these into
 * `lib/hooks.ts` and drop the mock-id fallback below.
 */
"use client";

import { useEffect, useState } from "react";
import { useOrder } from "@/lib/hooks";
import type { OutcomeOrder } from "@/lib/types";

/** Seeded order id used by the mock API (`lib/mock-data.ts`). */
const DEFAULT_ORDER_ID = "ord_healthtrack";
const SCOPE_SESSIONS_KEY = "orchestra:scope_sessions";

/**
 * Returns the signed-in client's outcomes. In mock mode there is a single
 * seeded order; once an order is confirmed its id is stashed in sessionStorage
 * by the proposal flow, so we prefer that.
 */
export function useMyOrders() {
  const [orderId, setOrderId] = useState(DEFAULT_ORDER_ID);

  useEffect(() => {
    const stored = sessionStorage.getItem("order_id");
    if (stored) setOrderId(stored);
  }, []);

  const { data, isLoading, isError } = useOrder(orderId);

  const orders: OutcomeOrder[] = data ? [data] : [];
  return { orders, isLoading, isError };
}

export interface ScopeDraftRef {
  id: string;
  savedAt: string;
}

/** Records a scope session id so it can be resumed later from /start. */
export function rememberScopeSession(sessionId: string) {
  if (typeof window === "undefined" || !sessionId) return;
  try {
    const raw = sessionStorage.getItem(SCOPE_SESSIONS_KEY);
    const list: ScopeDraftRef[] = raw ? JSON.parse(raw) : [];
    const next = [
      { id: sessionId, savedAt: new Date().toISOString() },
      ...list.filter((s) => s.id !== sessionId),
    ].slice(0, 5);
    sessionStorage.setItem(SCOPE_SESSIONS_KEY, JSON.stringify(next));
  } catch {
    // sessionStorage unavailable — resume is a best-effort convenience.
  }
}

/** Returns in-progress scope drafts the client can resume. */
export function useMyScopes() {
  const [scopes, setScopes] = useState<ScopeDraftRef[]>([]);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(SCOPE_SESSIONS_KEY);
      setScopes(raw ? (JSON.parse(raw) as ScopeDraftRef[]) : []);
    } catch {
      setScopes([]);
    }
  }, []);

  return { scopes };
}
