/**
 * Live Spine — WebSocket subscribe → React Query invalidation.
 * Track Z: wire useOrderLiveInvalidation on the order page (app/orders/**).
 */
"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { getAuthToken } from "./auth-token";

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

const INVALIDATION_DEBOUNCE_MS = 400;

export type LiveSpineEvent = {
  aggregate_type: string;
  aggregate_id: string;
  event_type: string;
  actor_id?: string | null;
  actor_type?: string;
  order_id?: string;
  payload?: Record<string, unknown>;
};

function toWsBase(httpBase: string): string {
  if (httpBase.startsWith("https://")) return `wss://${httpBase.slice("https://".length)}`;
  if (httpBase.startsWith("http://")) return `ws://${httpBase.slice("http://".length)}`;
  return httpBase;
}

function buildWsUrl(path: string, token: string | null, role?: string): string {
  const url = new URL(`${toWsBase(API_BASE)}${path}`);
  if (token) url.searchParams.set("token", token);
  if (role) url.searchParams.set("role", role);
  return url.toString();
}

type SubscribeOpts = {
  role?: "client" | "worker";
  onEvent?: (event: LiveSpineEvent) => void;
};

function subscribeChannel(
  path: string,
  onEvent: (event: LiveSpineEvent) => void,
  opts?: SubscribeOpts,
): () => void {
  let disposed = false;
  let socket: WebSocket | null = null;
  let attempt = 0;
  let timer: ReturnType<typeof setTimeout> | null = null;

  const connect = async () => {
    if (disposed) return;
    const token = await getAuthToken();
    if (disposed) return;
    const url = buildWsUrl(path, token, opts?.role);
    const ws = new WebSocket(url);
    socket = ws;

    ws.onopen = () => {
      attempt = 0;
    };
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(String(ev.data)) as LiveSpineEvent;
        onEvent(data);
      } catch {
        /* ignore malformed frames */
      }
    };
    ws.onclose = () => {
      if (disposed) return;
      const delay = Math.min(1000 * 2 ** attempt, 15_000);
      attempt += 1;
      timer = setTimeout(() => {
        void connect();
      }, delay);
    };
  };

  void connect();

  return () => {
    disposed = true;
    if (timer) clearTimeout(timer);
    socket?.close();
    socket = null;
  };
}

/** Subscribe to order:{id} live events (reconnect with backoff). */
export function subscribeOrderLive(
  orderId: string,
  onEvent: (event: LiveSpineEvent) => void,
  opts?: SubscribeOpts,
): () => void {
  return subscribeChannel(`/ws/orders/${orderId}`, onEvent, {
    role: opts?.role ?? "client",
    ...opts,
  });
}

/** Subscribe to task:{id} live events — Track Z wires worker task page. */
export function subscribeTaskLive(
  taskId: string,
  onEvent: (event: LiveSpineEvent) => void,
  opts?: SubscribeOpts,
): () => void {
  return subscribeChannel(`/ws/tasks/${taskId}`, onEvent, {
    role: opts?.role ?? "worker",
    ...opts,
  });
}

/**
 * Invalidates tracker query keys when the order live channel fires.
 * Debounced + scoped — avoids refetch storms during active delivery.
 */
export function useOrderLiveInvalidation(orderId: string | undefined) {
  const qc = useQueryClient();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!orderId) return;

    const flush = () => {
      void qc.invalidateQueries({ queryKey: ["order", orderId] });
      void qc.invalidateQueries({ queryKey: ["plan", orderId] });
      void qc.invalidateQueries({ queryKey: ["delivery", orderId] });
      // Discussion is task-scoped — do not blanket-invalidate ["discussion"].
      void qc.invalidateQueries({ queryKey: ["my-tasks"] });
    };

    const unsub = subscribeOrderLive(orderId, () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(flush, INVALIDATION_DEBOUNCE_MS);
    });

    return () => {
      unsub();
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [orderId, qc]);
}

/** Invalidates worker task query keys when the task live channel fires. */
export function useTaskLiveInvalidation(taskId: string | undefined) {
  const qc = useQueryClient();
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const flush = () => {
      void qc.invalidateQueries({ queryKey: ["my-tasks"] });
      void qc.invalidateQueries({ queryKey: ["discussion", taskId] });
      void qc.invalidateQueries({ queryKey: ["charter", taskId] });
      void qc.invalidateQueries({ queryKey: ["task-packet", taskId] });
      void qc.invalidateQueries({ queryKey: ["task-qa", taskId] });
    };

    const unsub = subscribeTaskLive(taskId, () => {
      if (timerRef.current) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(flush, INVALIDATION_DEBOUNCE_MS);
    });

    return () => {
      unsub();
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [taskId, qc]);
}
