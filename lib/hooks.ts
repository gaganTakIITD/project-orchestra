/**
 * Project Orchestra — data hooks
 * ==============================
 * Thin TanStack Query wrappers over `lib/api.ts`. v0's screens call these
 * instead of fetching directly, so caching, loading, and error states are
 * consistent and the mock->real swap stays invisible to the UI.
 *
 * OWNERSHIP: thin-frontend (Cursor) side. v0 may add more hooks following this
 * pattern, but data access must always go through `lib/api.ts`.
 */
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  authApi,
  catalogApi,
  clientApi,
  notificationsApi,
  workerApi,
} from "./api";

// --- Catalog ---------------------------------------------------------------

export const useSkus = () =>
  useQuery({ queryKey: ["skus"], queryFn: catalogApi.listSkus });

export const useTaskTypes = () =>
  useQuery({ queryKey: ["task-types"], queryFn: catalogApi.listTaskTypes });

// --- Auth ------------------------------------------------------------------

export const useMe = () =>
  useQuery({ queryKey: ["me"], queryFn: authApi.me });

// --- Client journey --------------------------------------------------------

export const useOrder = (orderId: string) =>
  useQuery({ queryKey: ["order", orderId], queryFn: () => clientApi.getOrder(orderId) });

export const usePlan = (orderId: string) =>
  useQuery({ queryKey: ["plan", orderId], queryFn: () => clientApi.getPlan(orderId) });

export const useSpec = () =>
  useQuery({ queryKey: ["spec"], queryFn: clientApi.getSpec });

export const useQuote = (quoteId: string) =>
  useQuery({ queryKey: ["quote", quoteId], queryFn: () => clientApi.getQuote(quoteId) });

export const useCandidates = (orderId: string, taskId: string) =>
  useQuery({
    queryKey: ["candidates", orderId, taskId],
    queryFn: () => clientApi.getCandidates(orderId, taskId),
  });

export const useDelivery = (orderId: string) =>
  useQuery({ queryKey: ["delivery", orderId], queryFn: () => clientApi.getDelivery(orderId) });

export const useDiscussion = (taskId: string) =>
  useQuery({ queryKey: ["discussion", taskId], queryFn: () => clientApi.getDiscussion(taskId) });

export const useSetPreferences = (orderId: string, taskId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (rankedWorkerIds: string[]) =>
      clientApi.setPreferences(orderId, taskId, rankedWorkerIds),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["order", orderId] }),
  });
};

// --- Worker journey --------------------------------------------------------

export const useWorkerProfile = () =>
  useQuery({ queryKey: ["worker-profile"], queryFn: workerApi.getProfile });

export const useMyTasks = () =>
  useQuery({ queryKey: ["my-tasks"], queryFn: workerApi.getMyTasks });

export const useCharter = (taskId: string) =>
  useQuery({ queryKey: ["charter", taskId], queryFn: () => workerApi.getCharter(taskId) });

export const useAcceptInterest = (taskId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => workerApi.acceptInterest(taskId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-tasks"] }),
  });
};

export const useSubmit = (taskId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { notes: string; asset_urls: string[] }) =>
      workerApi.submit(taskId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-tasks"] }),
  });
};

// --- Notifications ---------------------------------------------------------

export const useNotifications = () =>
  useQuery({ queryKey: ["notifications"], queryFn: notificationsApi.list });
