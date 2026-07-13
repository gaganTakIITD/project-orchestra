/**
 * Admin read-only API client (Track D).
 * Separate from lib/api.ts so product screens stay untouched.
 */
import { ApiError } from "./api";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";
const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export interface AdminOrder {
  id: string;
  client_id: string;
  quote_id: string;
  spec_id: string;
  sku_id?: string | null;
  status: string;
  price: number;
  deadline?: string | null;
  revision_limit: number;
  progress_pct: number;
  created_at: string;
  updated_at: string;
}

export interface AdminEvent {
  id: string;
  aggregate_type: string;
  aggregate_id: string;
  event_type: string;
  actor_id?: string | null;
  actor_type?: string | null;
  payload?: Record<string, unknown> | null;
  created_at: string;
}

export interface AdminAiDecision {
  id: string;
  session_id?: string | null;
  agent_type: string;
  source: string;
  model?: string | null;
  input_text?: string | null;
  output_draft?: Record<string, unknown> | null;
  reply?: string | null;
  completeness_pct?: number | null;
  ready_for_quote: boolean;
  confidence?: number | null;
  latency_ms?: number | null;
  error?: string | null;
  created_at: string;
}

export interface AdminOrderList {
  orders: AdminOrder[];
}

export interface AdminEventList {
  order_id: string;
  events: AdminEvent[];
}

export interface AdminAiDecisionList {
  decisions: AdminAiDecision[];
}

async function adminFetch<T>(path: string): Promise<T> {
  const { getAuthToken } = await import("./auth-token");
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { headers });
  if (!res.ok) {
    throw new ApiError(res.status, `GET ${path} failed`);
  }
  return (await res.json()) as T;
}

const MOCK_ORDERS: AdminOrder[] = [
  {
    id: "ord_mock_admin_1",
    client_id: "usr_mock_client",
    quote_id: "q_mock_1",
    spec_id: "spec_mock_1",
    status: "delivery_active",
    price: 2499,
    deadline: new Date(Date.now() + 7 * 86400000).toISOString(),
    revision_limit: 2,
    progress_pct: 40,
    created_at: new Date(Date.now() - 2 * 86400000).toISOString(),
    updated_at: new Date().toISOString(),
  },
];

const MOCK_EVENTS: AdminEvent[] = [
  {
    id: "evt_1",
    aggregate_type: "order",
    aggregate_id: "ord_mock_admin_1",
    event_type: "order.confirmed",
    actor_type: "client",
    created_at: new Date(Date.now() - 2 * 86400000).toISOString(),
  },
  {
    id: "evt_2",
    aggregate_type: "task",
    aggregate_id: "task_mock_1",
    event_type: "task.ready",
    actor_type: "system",
    created_at: new Date(Date.now() - 86400000).toISOString(),
  },
];

const MOCK_DECISIONS: AdminAiDecision[] = [
  {
    id: "ai_1",
    agent_type: "architect",
    source: "fixture",
    model: null,
    reply: "Built 3-task DAG",
    ready_for_quote: false,
    created_at: new Date(Date.now() - 2 * 86400000).toISOString(),
  },
];

export const adminApi = {
  listOrders: (status?: string): Promise<AdminOrderList> => {
    if (USE_MOCKS) {
      const orders = status
        ? MOCK_ORDERS.filter((o) => o.status === status)
        : MOCK_ORDERS;
      return Promise.resolve({ orders });
    }
    const q = status ? `?status=${encodeURIComponent(status)}` : "";
    return adminFetch(`/admin/orders${q}`);
  },

  listOrderEvents: (orderId: string): Promise<AdminEventList> => {
    if (USE_MOCKS) {
      return Promise.resolve({
        order_id: orderId,
        events: MOCK_EVENTS.filter(
          (e) =>
            e.aggregate_id === orderId || e.aggregate_type === "task"
        ),
      });
    }
    return adminFetch(`/admin/orders/${orderId}/events`);
  },

  listAiDecisions: (limit = 50): Promise<AdminAiDecisionList> => {
    if (USE_MOCKS) {
      return Promise.resolve({ decisions: MOCK_DECISIONS.slice(0, limit) });
    }
    return adminFetch(`/admin/ai-decisions?limit=${limit}`);
  },

  listWorkers: (): Promise<{ workers: Array<{ user_id: string; full_name: string; campus_verified: boolean }> }> => {
    if (USE_MOCKS) {
      return Promise.resolve({
        workers: [
          {
            user_id: "usr_mock_worker",
            full_name: "Mock Worker",
            campus_verified: false,
          },
        ],
      });
    }
    return adminFetch("/admin/workers");
  },

  verifyWorker: (workerId: string): Promise<{ user_id: string; campus_verified: boolean }> => {
    if (USE_MOCKS) {
      return Promise.resolve({ user_id: workerId, campus_verified: true });
    }
    return adminMutate(`/admin/workers/${workerId}/verify`, "POST");
  },

  unverifyWorker: (workerId: string): Promise<{ user_id: string; campus_verified: boolean }> => {
    if (USE_MOCKS) {
      return Promise.resolve({ user_id: workerId, campus_verified: false });
    }
    return adminMutate(`/admin/workers/${workerId}/unverify`, "POST");
  },

  aiQuality: (): Promise<{ count: number; avg_confidence: number | null; escalate_count: number }> => {
    if (USE_MOCKS) {
      return Promise.resolve({ count: 1, avg_confidence: 0.88, escalate_count: 0 });
    }
    return adminFetch("/admin/ai-quality");
  },
};

async function adminMutate<T>(path: string, method: string): Promise<T> {
  const { getAuthToken } = await import("./auth-token");
  const token = await getAuthToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { method, headers });
  if (!res.ok) {
    throw new ApiError(res.status, `${method} ${path} failed`);
  }
  return (await res.json()) as T;
}
