/**
 * Project Orchestra — Mock-first API client
 * =========================================
 * Every screen talks to the backend ONLY through this module. Today it returns
 * typed fixtures from `lib/mock-data.ts`; when the FastAPI backend (Stage 4) is
 * live, flip `USE_MOCKS` to false (or set NEXT_PUBLIC_USE_MOCKS=false) and the
 * same function signatures hit real endpoints — no screen changes required.
 *
 * Endpoint paths below mirror Technical Spec §7 exactly.
 * OWNERSHIP: thin-frontend (Cursor) side.
 */
import {
  mockCandidates,
  mockCharter,
  mockClient,
  mockDeliveryBundle,
  mockDiscussion,
  mockInterests,
  mockNotifications,
  mockOrder,
  mockPlan,
  mockPreferenceSet,
  mockQuote,
  mockSkus,
  mockSpec,
  mockSkills,
  mockTaskTypes,
  mockTools,
  mockWorkerMe,
} from "./mock-data";
import {
  getOrCreateMockSession,
  mockFinalizeScopeSession,
  mockSendScopeMessage,
} from "./mock-chat";
import type {
  Candidate,
  Charter,
  ChatSession,
  DeliveryBundle,
  DiscussionThread,
  FinalizeChatSessionResult,
  FulfillmentPlan,
  OutcomeOrder,
  OutcomeSku,
  OutcomeSpec,
  PreferenceSet,
  Quote,
  Skill,
  TaskType,
  Tool,
  WorkerProfile,
} from "./types";

export const USE_MOCKS =
  process.env.NEXT_PUBLIC_USE_MOCKS !== "false"; // default true until backend lands

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

/** Real network call — used when USE_MOCKS is false. */
async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    ...init,
  });
  if (!res.ok) {
    throw new ApiError(res.status, `${init?.method ?? "GET"} ${path} failed`);
  }
  return (await res.json()) as T;
}

/** Simulate a little latency so loading states are exercised in mock mode. */
const mock = <T>(data: T, ms = 350): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(data), ms));

// ----------------------------------------------------------------------------
// Catalog & taxonomy (Spec §7.2)
// ----------------------------------------------------------------------------

export const catalogApi = {
  listSkus: (): Promise<OutcomeSku[]> =>
    USE_MOCKS ? mock(mockSkus) : apiFetch("/catalog/skus"),
  getSku: (slug: string): Promise<OutcomeSku | undefined> =>
    USE_MOCKS
      ? mock(mockSkus.find((s) => s.slug === slug))
      : apiFetch(`/catalog/skus/${slug}`),
  listSkills: (): Promise<Skill[]> =>
    USE_MOCKS ? mock(mockSkills) : apiFetch("/taxonomy/skills"),
  listTools: (): Promise<Tool[]> =>
    USE_MOCKS ? mock(mockTools) : apiFetch("/taxonomy/tools"),
  listTaskTypes: (): Promise<TaskType[]> =>
    USE_MOCKS ? mock(mockTaskTypes) : apiFetch("/taxonomy/task-types"),
};

// ----------------------------------------------------------------------------
// Client journey (Spec §7.3–§7.6)
// ----------------------------------------------------------------------------

export const clientApi = {
  createIntent: (raw_text: string): Promise<{ intent_id: string; quote_id: string }> =>
    USE_MOCKS
      ? mock({ intent_id: "int_healthtrack", quote_id: "quote_healthtrack" })
      : apiFetch("/intents", { method: "POST", body: JSON.stringify({ raw_text, attachments: [] }) }),

  /** spec_id from Quote — matches v0 proposal page (`useSpec(quote.spec_id)`). */
  getSpec: (specId: string): Promise<OutcomeSpec> =>
    USE_MOCKS ? mock(mockSpec) : apiFetch(`/specs/${specId}`),

  getQuote: (id: string): Promise<Quote> =>
    USE_MOCKS ? mock(mockQuote) : apiFetch(`/quotes/${id}`),

  acceptQuote: (id: string): Promise<{ order_id: string }> =>
    USE_MOCKS
      ? mock({ order_id: mockOrder.id })
      : apiFetch(`/quotes/${id}/accept`, { method: "POST" }),

  getOrder: (id: string): Promise<OutcomeOrder> =>
    USE_MOCKS ? mock(mockOrder) : apiFetch(`/orders/${id}`),

  getPlan: (orderId: string): Promise<FulfillmentPlan> =>
    USE_MOCKS ? mock(mockPlan) : apiFetch(`/orders/${orderId}/milestones`),

  getCandidates: (orderId: string, taskId: string): Promise<Candidate[]> =>
    USE_MOCKS
      ? mock(mockCandidates)
      : apiFetch(`/orders/${orderId}/tasks/${taskId}/candidates`),

  setPreferences: (
    orderId: string,
    taskId: string,
    ranked_worker_ids: string[]
  ): Promise<PreferenceSet> =>
    USE_MOCKS
      ? mock(mockPreferenceSet)
      : apiFetch(`/orders/${orderId}/tasks/${taskId}/preferences`, {
          method: "POST",
          body: JSON.stringify({ ranked_worker_ids }),
        }),

  getDelivery: (orderId: string): Promise<DeliveryBundle> =>
    USE_MOCKS ? mock(mockDeliveryBundle) : apiFetch(`/orders/${orderId}/delivery`),

  acceptDelivery: (orderId: string): Promise<{ status: string }> =>
    USE_MOCKS
      ? mock({ status: "closed" })
      : apiFetch(`/orders/${orderId}/accept-delivery`, { method: "POST" }),

  getDiscussion: (taskId: string): Promise<DiscussionThread> =>
    USE_MOCKS ? mock(mockDiscussion) : apiFetch(`/tasks/${taskId}/discussion`),
};

// ----------------------------------------------------------------------------
// Worker journey (Spec §7.7–§7.8)
// ----------------------------------------------------------------------------

export const workerApi = {
  getProfile: (): Promise<WorkerProfile> =>
    USE_MOCKS ? mock(mockWorkerMe) : apiFetch("/workers/profile"),

  getMyTasks: (): Promise<FulfillmentPlan["tasks"]> =>
    USE_MOCKS ? mock(mockPlan.tasks) : apiFetch("/workers/me/tasks"),

  getCharter: (taskId: string): Promise<Charter> =>
    USE_MOCKS ? mock(mockCharter) : apiFetch(`/tasks/${taskId}/charter`),

  acceptInterest: (taskId: string): Promise<{ status: string }> =>
    USE_MOCKS
      ? mock({ status: "accepted" })
      : apiFetch(`/tasks/${taskId}/accept-interest`, { method: "POST" }),

  readyToStart: (taskId: string): Promise<{ status: string }> =>
    USE_MOCKS
      ? mock({ status: "start_requested" })
      : apiFetch(`/tasks/${taskId}/ready-to-start`, { method: "POST" }),

  submit: (
    taskId: string,
    payload: { notes: string; asset_urls: string[] }
  ): Promise<{ status: string }> =>
    USE_MOCKS
      ? mock({ status: "submitted" })
      : apiFetch(`/tasks/${taskId}/submit`, {
          method: "POST",
          body: JSON.stringify(payload),
        }),
};

export const notificationsApi = {
  list: () => (USE_MOCKS ? mock(mockNotifications) : apiFetch("/notifications")),
};

export const authApi = {
  me: () => (USE_MOCKS ? mock(mockClient) : apiFetch("/auth/me")),
};

// ----------------------------------------------------------------------------
// Scope chat — schema-driven job description extraction
// ----------------------------------------------------------------------------

export const chatApi = {
  startScopeSession: (): Promise<ChatSession> =>
    USE_MOCKS
      ? mock(getOrCreateMockSession())
      : apiFetch("/chat/sessions", { method: "POST" }),

  getSession: (sessionId: string): Promise<ChatSession> =>
    USE_MOCKS
      ? mock(getOrCreateMockSession(sessionId))
      : apiFetch(`/chat/sessions/${sessionId}`),

  sendMessage: (sessionId: string, body: string): Promise<ChatSession> =>
    USE_MOCKS
      ? mock(mockSendScopeMessage(sessionId, body))
      : apiFetch(`/chat/sessions/${sessionId}/messages`, {
          method: "POST",
          body: JSON.stringify({ body }),
        }),

  finalizeSession: (sessionId: string): Promise<FinalizeChatSessionResult> =>
    USE_MOCKS
      ? mock(mockFinalizeScopeSession(sessionId))
      : apiFetch(`/chat/sessions/${sessionId}/finalize`, { method: "POST" }),
};
