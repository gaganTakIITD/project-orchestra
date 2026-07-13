/**
 * Admin TanStack Query hooks (Track D + Sprint 3 verify).
 * Import from here — do not wire through lib/hooks.ts wholesale.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

export const useAdminWorkers = () =>
  useQuery({
    queryKey: ["admin", "workers"],
    queryFn: () => adminApi.listWorkers(),
  });

export const useAdminVerifyWorker = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      workerId,
      verify,
    }: {
      workerId: string;
      verify: boolean;
    }) =>
      verify
        ? adminApi.verifyWorker(workerId)
        : adminApi.unverifyWorker(workerId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["admin", "workers"] }),
  });
};
