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
  mockTaskPacket,
  mockClient,
  mockDeliveryBundle,
  mockDiscussion,
  mockInterests,
  mockNotifications,
  mockOrder,
  mockOrders,
  mockPlan,
  mockPreferenceSet,
  mockSkus,
  mockSkills,
  mockTaskTypes,
  mockTools,
  mockWorkerMe,
  mockQAReview,
} from "./mock-data";
import {
  computeProfileCompletionPct,
  PROFILE_LIVE_THRESHOLD,
} from "./profile-completion";
import {
  getOrCreateMockSession,
  getMockQuote,
  getMockSpec,
  mockFinalizeMatcherSession,
  mockFinalizePricingSession,
  mockFinalizeScopeSession,
  mockSendScopeMessage,
  mockSendScopeMessageStream,
  mockStartMatcherSession,
  mockStartPricingSession,
  mockUndoScopeSession,
} from "./mock-chat";
import type {
  Amendment,
  AppNotification,
  Candidate,
  Charter,
  ChatSession,
  ChatSessionSummary,
  ChatStreamEvent,
  ChatStreamHandlers,
  DeliveryBundle,
  DiscussionThread,
  DisputeCase,
  FinalizeChatSessionResult,
  FinalizeMatcherSessionResult,
  FinalizePricingSessionResult,
  FulfillmentPlan,
  LedgerEntry,
  OutcomeOrder,
  OutcomeSku,
  OutcomeSpec,
  PreferenceSet,
  QAReview,
  Quote,
  Skill,
  StartChatSessionInput,
  TaskPacket,
  TaskType,
  Tool,
  User,
  WorkerProfile,
  WorkerProfileSaveInput,
} from "./types";

export const USE_MOCKS =
  process.env.NEXT_PUBLIC_USE_MOCKS !== "false"; // product path: set NEXT_PUBLIC_USE_MOCKS=false

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
  const { getAuthToken } = await import("./auth-token");
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (typeof window !== "undefined" && !headers["X-Orchestra-Role"]) {
    headers["X-Orchestra-Role"] = window.location.pathname.startsWith("/worker")
      ? "worker"
      : "client";
  }

  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });
  if (!res.ok) {
    throw new ApiError(res.status, `${init?.method ?? "GET"} ${path} failed`);
  }
  return (await res.json()) as T;
}

function parseSseBlock(block: string): ChatStreamEvent | null {
  const line = block
    .split("\n")
    .map((l) => l.trim())
    .find((l) => l.startsWith("data:"));
  if (!line) return null;
  const payload = line.slice(5).trim();
  if (!payload) return null;
  return JSON.parse(payload) as ChatStreamEvent;
}

async function streamChatMessage(
  sessionId: string,
  body: string,
  handlers: ChatStreamHandlers
): Promise<ChatSession> {
  const { getAuthToken } = await import("./auth-token");
  const token = await getAuthToken();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (typeof window !== "undefined") {
    headers["X-Orchestra-Role"] = window.location.pathname.startsWith("/worker")
      ? "worker"
      : "client";
  }

  const res = await fetch(`${API_BASE}/chat/sessions/${sessionId}/messages/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify({ body }),
  });
  if (!res.ok) {
    throw new ApiError(res.status, `POST /chat/sessions/${sessionId}/messages/stream failed`);
  }
  if (!res.body) {
    throw new ApiError(500, "Stream body missing");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalSession: ChatSession | null = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) {
      const event = parseSseBlock(part);
      if (!event) continue;
      switch (event.type) {
        case "token":
          handlers.onToken?.(event.content);
          break;
        case "draft_patch":
          handlers.onDraftPatch?.(event);
          break;
        case "artifact_updated":
          handlers.onArtifactUpdated?.(event);
          break;
        case "turn_complete":
          finalSession = event.session;
          handlers.onTurnComplete?.(event.session);
          break;
        case "error":
          handlers.onError?.(event.message);
          throw new ApiError(500, event.message);
      }
    }
  }

  if (!finalSession) {
    throw new ApiError(500, "Stream ended without turn_complete");
  }
  return finalSession;
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
    USE_MOCKS ? mock(getMockSpec(specId)) : apiFetch(`/specs/${specId}`),

  getQuote: (id: string): Promise<Quote> =>
    USE_MOCKS ? mock(getMockQuote(id)) : apiFetch(`/quotes/${id}`),

  acceptQuote: (id: string): Promise<{ order_id: string }> =>
    USE_MOCKS
      ? mock({ order_id: mockOrder.id })
      : apiFetch(`/quotes/${id}/accept`, { method: "POST" }),

  /** The current client's outcomes, newest first — powers the /orders dashboard. */
  listOrders: (): Promise<OutcomeOrder[]> =>
    USE_MOCKS ? mock(mockOrders) : apiFetch("/orders"),

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

  postDiscussion: (
    taskId: string,
    payload: { body: string; message_type?: string }
  ): Promise<DiscussionThread> =>
    USE_MOCKS
      ? mock(mockDiscussion)
      : apiFetch(`/tasks/${taskId}/discussion`, {
          method: "POST",
          body: JSON.stringify(payload),
        }),

  listAmendments: (orderId: string): Promise<{ amendments: Amendment[] }> =>
    USE_MOCKS
      ? mock({ amendments: [] })
      : apiFetch(`/orders/${orderId}/amendments`),

  approveAmendment: (amendmentId: string): Promise<Amendment> =>
    USE_MOCKS
      ? mock({
          id: amendmentId,
          order_id: mockOrder.id,
          requested_by: mockClient.id,
          delta_description: "Mock amendment",
          price_delta: 0,
          time_delta_hours: 0,
          status: "applied" as const,
          created_at: new Date().toISOString(),
        })
      : apiFetch(`/amendments/${amendmentId}/approve`, { method: "POST" }),

  rejectAmendment: (amendmentId: string): Promise<Amendment> =>
    USE_MOCKS
      ? mock({
          id: amendmentId,
          order_id: mockOrder.id,
          requested_by: mockClient.id,
          delta_description: "Mock amendment",
          price_delta: 0,
          time_delta_hours: 0,
          status: "rejected" as const,
          created_at: new Date().toISOString(),
        })
      : apiFetch(`/amendments/${amendmentId}/reject`, { method: "POST" }),

  fundOrder: (orderId: string): Promise<Record<string, unknown>> =>
    USE_MOCKS
      ? mock({ order_id: orderId, ledger_state: "funds_authorized", payments_enabled: false })
      : apiFetch(`/orders/${orderId}/fund`, { method: "POST" }),

  listLedgerEntries: (orderId: string): Promise<{ entries: LedgerEntry[] }> =>
    USE_MOCKS
      ? mock({ entries: [] })
      : apiFetch(`/orders/${orderId}/ledger-entries`),

  openDispute: (
    orderId: string,
    payload: { reason: string; task_id?: string }
  ): Promise<Record<string, unknown>> =>
    USE_MOCKS
      ? mock({ id: "disp_mock", order_id: orderId, status: "open", ...payload })
      : apiFetch(`/orders/${orderId}/disputes`, {
          method: "POST",
          body: JSON.stringify(payload),
        }),

  listDisputes: (orderId: string): Promise<{ disputes: DisputeCase[] }> =>
    USE_MOCKS
      ? mock({ disputes: [] })
      : apiFetch(`/orders/${orderId}/disputes`),
};

// ----------------------------------------------------------------------------
// Worker journey (Spec §7.7–§7.8)
// ----------------------------------------------------------------------------

export const workerApi = {
  getProfile: (): Promise<WorkerProfile> =>
    USE_MOCKS ? mock(mockWorkerMe) : apiFetch("/workers/profile"),

  saveProfile: (payload: WorkerProfileSaveInput): Promise<WorkerProfile> => {
    if (!USE_MOCKS) {
      return apiFetch("/workers/profile", {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
    }
    const merged = {
      ...mockWorkerMe,
      ...payload,
      user_id: mockWorkerMe.user_id,
      campus_verified: mockWorkerMe.campus_verified,
      stats: mockWorkerMe.stats,
      full_name: payload.full_name ?? mockWorkerMe.full_name,
      community_type: payload.community_type ?? mockWorkerMe.community_type,
      headline: payload.headline ?? mockWorkerMe.headline,
      bio: payload.bio ?? mockWorkerMe.bio,
      availability_status:
        payload.availability_status ?? mockWorkerMe.availability_status,
      weekly_hours_available:
        payload.weekly_hours_available ?? mockWorkerMe.weekly_hours_available,
      max_concurrent_tasks:
        payload.max_concurrent_tasks ?? mockWorkerMe.max_concurrent_tasks,
      payout_min:
        payload.payout_min !== undefined
          ? payload.payout_min
          : mockWorkerMe.payout_min,
      payout_max:
        payload.payout_max !== undefined
          ? payload.payout_max
          : mockWorkerMe.payout_max,
      github_url:
        payload.github_url !== undefined
          ? payload.github_url
          : mockWorkerMe.github_url,
      figma_url:
        payload.figma_url !== undefined
          ? payload.figma_url
          : mockWorkerMe.figma_url,
      behance_url:
        payload.behance_url !== undefined
          ? payload.behance_url
          : mockWorkerMe.behance_url,
      linkedin_url:
        payload.linkedin_url !== undefined
          ? payload.linkedin_url
          : mockWorkerMe.linkedin_url,
      skills: payload.skills ?? mockWorkerMe.skills,
      tools: payload.tools ?? mockWorkerMe.tools,
      task_types: payload.task_types ?? mockWorkerMe.task_types,
      portfolio: payload.portfolio ?? mockWorkerMe.portfolio,
    };
    const pct = computeProfileCompletionPct({
      full_name: merged.full_name,
      headline: merged.headline,
      bio: merged.bio,
      community_type: merged.community_type,
      skills: merged.skills,
      tools: merged.tools,
      task_types: merged.task_types,
      portfolio: merged.portfolio,
      github_url: merged.github_url || "",
      figma_url: merged.figma_url || "",
      behance_url: merged.behance_url || "",
      linkedin_url: merged.linkedin_url || "",
      availability_status: merged.availability_status,
      weekly_hours_available: merged.weekly_hours_available,
      max_concurrent_tasks: merged.max_concurrent_tasks,
      payout_min: merged.payout_min ?? null,
      payout_max: merged.payout_max ?? null,
    });
    Object.assign(mockWorkerMe, {
      ...merged,
      profile_completion_pct: pct,
      is_active: Boolean(payload.is_active) && pct >= PROFILE_LIVE_THRESHOLD,
    });
    return mock({ ...mockWorkerMe });
  },

  getMyTasks: (): Promise<FulfillmentPlan["tasks"]> =>
    USE_MOCKS ? mock(mockPlan.tasks) : apiFetch("/workers/me/tasks"),

  getCharter: (taskId: string): Promise<Charter> =>
    USE_MOCKS ? mock(mockCharter) : apiFetch(`/tasks/${taskId}/charter`),

  getTaskPacket: (taskId: string): Promise<TaskPacket> =>
    USE_MOCKS ? mock(mockTaskPacket) : apiFetch(`/tasks/${taskId}/packet`),

  acceptInterest: (taskId: string): Promise<{ status: string }> =>
    USE_MOCKS
      ? mock({ status: "accepted" })
      : apiFetch(`/tasks/${taskId}/accept-interest`, { method: "POST" }),

  readyToStart: (taskId: string): Promise<{ status: string }> =>
    USE_MOCKS
      ? mock({ status: "in_progress" })
      : apiFetch(`/tasks/${taskId}/ready-to-start`, { method: "POST" }),

  submit: (
    taskId: string,
    payload: { notes: string; asset_urls: string[] }
  ): Promise<{ status: string }> =>
    USE_MOCKS
      ? mock({ status: "completed" })
      : apiFetch(`/tasks/${taskId}/submit`, {
          method: "POST",
          body: JSON.stringify(payload),
        }),

  getTaskQA: (taskId: string): Promise<QAReview> =>
    USE_MOCKS ? mock(mockQAReview) : apiFetch(`/tasks/${taskId}/qa`),
};

export const notificationsApi = {
  list: (): Promise<AppNotification[]> =>
    USE_MOCKS ? mock(mockNotifications) : apiFetch("/notifications"),

  markRead: (id: string): Promise<AppNotification> =>
    USE_MOCKS
      ? mock({
          ...(mockNotifications.find((n) => n.id === id) ?? mockNotifications[0]),
          read: true,
        })
      : apiFetch(`/notifications/${id}/read`, { method: "POST" }),
};

export const authApi = {
  me: (): Promise<User> => (USE_MOCKS ? mock(mockClient) : apiFetch<User>("/auth/me")),

  setRole: (role: "client" | "worker"): Promise<User> =>
    USE_MOCKS
      ? mock({ ...mockClient, role })
      : apiFetch<User>("/auth/role", {
          method: "PATCH",
          body: JSON.stringify({ role }),
        }),
};

// ----------------------------------------------------------------------------
// Chat surfaces — Scope (Stage 1) + Pricing (Stage 2) + Matcher (Stage 3)
// ----------------------------------------------------------------------------

export const chatApi = {
  startScopeSession: (): Promise<ChatSession> =>
    USE_MOCKS
      ? mock(getOrCreateMockSession())
      : apiFetch("/chat/sessions", { method: "POST" }),

  /** Active scope drafts for the current client — powers "Resume scope". */
  listScopes: (): Promise<ChatSessionSummary[]> =>
    USE_MOCKS
      ? mock(
          [getOrCreateMockSession()]
            .filter((s) => s.agent_type === "spec_compiler" && s.status === "active")
            .map<ChatSessionSummary>((s) => ({
              id: s.id,
              agent_type: s.agent_type,
              status: s.status,
              title: s.spec_draft?.outcome_statement?.trim() || "Untitled outcome",
              completeness_pct: s.completeness_pct,
              ready_for_quote: s.ready_for_quote,
              spec_version: s.spec_version,
              created_at: s.created_at,
            }))
        )
      : apiFetch("/chat/sessions"),

  /** Stage 2 — Pricing Reasoner Confirm Chat bound to an issued quote. */
  startPricingSession: (quoteId: string): Promise<ChatSession> =>
    USE_MOCKS
      ? mock(mockStartPricingSession(quoteId))
      : apiFetch("/chat/sessions", {
          method: "POST",
          body: JSON.stringify({
            agent_type: "pricing",
            ref_type: "quote",
            ref_id: quoteId,
          } satisfies StartChatSessionInput),
        }),

  /** Stage 3 — Matcher Preference Chat bound to an order task. */
  startMatcherSession: (orderId: string, taskId: string): Promise<ChatSession> =>
    USE_MOCKS
      ? mock(mockStartMatcherSession(orderId, taskId))
      : apiFetch("/chat/sessions", {
          method: "POST",
          body: JSON.stringify({
            agent_type: "matcher",
            ref_type: "task",
            ref_id: taskId,
            order_id: orderId,
          } satisfies StartChatSessionInput),
        }),

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

  /** SSE stream — draft_patch|artifact_updated → tokens → turn_complete. */
  sendMessageStream: (
    sessionId: string,
    body: string,
    handlers: ChatStreamHandlers
  ): Promise<ChatSession> => {
    if (USE_MOCKS) {
      return mockSendScopeMessageStream(sessionId, body, handlers);
    }
    return streamChatMessage(sessionId, body, handlers);
  },

  finalizeSession: (sessionId: string): Promise<FinalizeChatSessionResult> =>
    USE_MOCKS
      ? mock(mockFinalizeScopeSession(sessionId))
      : apiFetch(`/chat/sessions/${sessionId}/finalize`, { method: "POST" }),

  finalizeMatcherSession: (
    sessionId: string,
    ranked_worker_ids?: string[]
  ): Promise<FinalizeMatcherSessionResult> =>
    USE_MOCKS
      ? mock(mockFinalizeMatcherSession(sessionId))
      : apiFetch(`/chat/sessions/${sessionId}/finalize`, {
          method: "POST",
          body: JSON.stringify(
            ranked_worker_ids?.length ? { ranked_worker_ids } : {}
          ),
        }),

  finalizePricingSession: (sessionId: string): Promise<FinalizePricingSessionResult> =>
    USE_MOCKS
      ? mock(mockFinalizePricingSession(sessionId))
      : apiFetch(`/chat/sessions/${sessionId}/finalize`, { method: "POST" }),

  undoSession: (sessionId: string): Promise<ChatSession> =>
    USE_MOCKS
      ? mock(mockUndoScopeSession(sessionId))
      : apiFetch(`/chat/sessions/${sessionId}/undo`, { method: "POST" }),
};
