/**
 * Best-effort sessionStorage helpers for scope resume UX.
 * Prefer `useMyScopes` from `@/lib/hooks` for the real list.
 */
"use client";

const SCOPE_SESSIONS_KEY = "orchestra:scope_sessions";

export interface ScopeDraftRef {
  id: string;
  savedAt: string;
}

/** Records a scope session id so it can be resumed later from /start or /orders. */
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
