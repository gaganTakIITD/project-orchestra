/**
 * Admin read-only TanStack Query hooks (Track D).
 * Import from here — do not wire through lib/hooks.ts wholesale.
 */
import { useQuery } from "@tanstack/react-query";
import { adminApi } from "./admin-api";

export const useAdminOrders = (status?: string) =>
  useQuery({
    queryKey: ["admin", "orders", status ?? "all"],
    queryFn: () => adminApi.listOrders(status),
  });

export const useAdminOrderEvents = (orderId: string | null) =>
  useQuery({
    queryKey: ["admin", "order-events", orderId],
    queryFn: () => adminApi.listOrderEvents(orderId!),
    enabled: Boolean(orderId),
  });

export const useAdminAiDecisions = (limit = 50) =>
  useQuery({
    queryKey: ["admin", "ai-decisions", limit],
    queryFn: () => adminApi.listAiDecisions(limit),
  });
