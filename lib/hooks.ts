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
import { useState } from "react";
import {
  authApi,
  catalogApi,
  chatApi,
  clientApi,
  notificationsApi,
  workerApi,
} from "./api";
import type { ChatSession } from "./types";

// --- Catalog ---------------------------------------------------------------

export const useSkus = () =>
  useQuery({ queryKey: ["skus"], queryFn: catalogApi.listSkus });

export const useTaskTypes = () =>
  useQuery({ queryKey: ["task-types"], queryFn: catalogApi.listTaskTypes });

// --- Auth ------------------------------------------------------------------

export const useMe = (options?: { enabled?: boolean }) =>
  useQuery({
    queryKey: ["me"],
    queryFn: authApi.me,
    enabled: options?.enabled ?? true,
  });

export const useSetRole = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (role: "client" | "worker") => authApi.setRole(role),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["me"] });
      qc.invalidateQueries({ queryKey: ["worker-profile"] });
    },
  });
};

// --- Scope chat (job description extraction) -------------------------------

/** Active scope drafts for the current client — powers "Resume scope" on /start. */
export const useMyScopes = (opts?: { enabled?: boolean }) =>
  useQuery({
    queryKey: ["scopes"],
    queryFn: () => chatApi.listScopes(),
    enabled: opts?.enabled ?? true,
  });

export const useStartScopeSession = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => chatApi.startScopeSession(),
    onSuccess: (session) => qc.setQueryData(["chat-session", session.id], session),
  });
};

export const useStartMatcherSession = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ orderId, taskId }: { orderId: string; taskId: string }) =>
      chatApi.startMatcherSession(orderId, taskId),
    onSuccess: (session) => qc.setQueryData(["chat-session", session.id], session),
  });
};

export const useStartPricingSession = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (quoteId: string) => chatApi.startPricingSession(quoteId),
    onSuccess: (session) => qc.setQueryData(["chat-session", session.id], session),
  });
};

export const useChatSession = (sessionId: string) =>
  useQuery({
    queryKey: ["chat-session", sessionId],
    queryFn: () => chatApi.getSession(sessionId),
    enabled: Boolean(sessionId),
  });

export const useSendChatMessage = (sessionId: string) => {
  const qc = useQueryClient();
  const [streamingText, setStreamingText] = useState("");

  const mutation = useMutation({
    mutationFn: (body: string) =>
      chatApi.sendMessageStream(sessionId, body, {
        onToken: (content) => setStreamingText((prev) => prev + content),
        onDraftPatch: (event) => {
          qc.setQueryData<ChatSession>(
            ["chat-session", sessionId],
            (old) =>
              old
                ? {
                    ...old,
                    spec_draft: event.spec_draft,
                    spec_version: event.spec_version,
                    completeness_pct: event.completeness_pct,
                    missing_fields: event.missing_fields,
                    ready_for_quote: event.ready_for_quote,
                  }
                : old
          );
        },
        onArtifactUpdated: (event) => {
          qc.setQueryData<ChatSession>(
            ["chat-session", sessionId],
            (old) =>
              old
                ? {
                    ...old,
                    candidates: event.candidates,
                    spec_version: event.version,
                    ready_to_confirm: event.ready_to_confirm,
                  }
                : old
          );
        },
      }),
    onMutate: () => {
      setStreamingText("");
    },
    onSuccess: (session) => {
      setStreamingText("");
      qc.setQueryData(["chat-session", sessionId], session);
    },
    onError: () => {
      setStreamingText("");
    },
  });

  return { ...mutation, streamingText };
};

export const useFinalizeChatSession = () =>
  useMutation({
    mutationFn: (sessionId: string) => chatApi.finalizeSession(sessionId),
  });

export const useFinalizeMatcherSession = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      sessionId,
      ranked_worker_ids,
    }: {
      sessionId: string;
      ranked_worker_ids?: string[];
    }) => chatApi.finalizeMatcherSession(sessionId, ranked_worker_ids),
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["order", result.order_id] });
      qc.invalidateQueries({ queryKey: ["plan", result.order_id] });
      qc.invalidateQueries({
        queryKey: ["candidates", result.order_id, result.task_id],
      });
    },
  });
};

export const useFinalizePricingSession = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => chatApi.finalizePricingSession(sessionId),
    onSuccess: (result) => {
      qc.invalidateQueries({ queryKey: ["quote", result.quote_id] });
      qc.invalidateQueries({ queryKey: ["order", result.order_id] });
    },
  });
};

export const useUndoChatSession = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => chatApi.undoSession(sessionId),
    onSuccess: (session) => {
      qc.setQueryData(["chat-session", session.id], session);
    },
  });
};

// --- Client journey --------------------------------------------------------

/** The current client's outcomes, newest first — client home / re-entry point. */
export const useMyOrders = () =>
  useQuery({
    queryKey: ["orders"],
    queryFn: () => clientApi.listOrders(),
  });

export const useOrder = (orderId: string) =>
  useQuery({
    queryKey: ["order", orderId],
    queryFn: () => clientApi.getOrder(orderId),
    enabled: Boolean(orderId),
  });

export const usePlan = (orderId: string) =>
  useQuery({
    queryKey: ["plan", orderId],
    queryFn: () => clientApi.getPlan(orderId),
    enabled: Boolean(orderId),
  });

export const useSpec = (specId: string) =>
  useQuery({
    queryKey: ["spec", specId],
    queryFn: () => clientApi.getSpec(specId),
    enabled: Boolean(specId),
  });

export const useCreateIntent = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (rawText: string) => clientApi.createIntent(rawText),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["spec"] }),
  });
};

export const useAcceptQuote = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (quoteId: string) => clientApi.acceptQuote(quoteId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["orders"] });
      qc.invalidateQueries({ queryKey: ["order"] });
      qc.invalidateQueries({ queryKey: ["plan"] });
    },
  });
};

export const useQuote = (quoteId: string) =>
  useQuery({
    queryKey: ["quote", quoteId],
    queryFn: () => clientApi.getQuote(quoteId),
    enabled: Boolean(quoteId),
  });

export const useCandidates = (orderId: string, taskId: string) =>
  useQuery({
    queryKey: ["candidates", orderId, taskId],
    queryFn: () => clientApi.getCandidates(orderId, taskId),
    enabled: Boolean(orderId && taskId),
  });

export const useDelivery = (orderId: string) =>
  useQuery({
    queryKey: ["delivery", orderId],
    queryFn: () => clientApi.getDelivery(orderId),
    enabled: Boolean(orderId),
    retry: false,
  });

export const useDiscussion = (taskId: string) =>
  useQuery({
    queryKey: ["discussion", taskId],
    queryFn: () => clientApi.getDiscussion(taskId),
    enabled: Boolean(taskId),
  });

export const useSetPreferences = (orderId: string, taskId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (rankedWorkerIds: string[]) =>
      clientApi.setPreferences(orderId, taskId, rankedWorkerIds),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["order", orderId] });
      qc.invalidateQueries({ queryKey: ["plan", orderId] });
      qc.invalidateQueries({ queryKey: ["candidates", orderId, taskId] });
    },
  });
};

// --- Worker journey --------------------------------------------------------

export const useWorkerProfile = (options?: { enabled?: boolean }) =>
  useQuery({
    queryKey: ["worker-profile"],
    queryFn: workerApi.getProfile,
    enabled: options?.enabled ?? true,
  });

export const useSaveWorkerProfile = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: workerApi.saveProfile,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["worker-profile"] }),
  });
};

export const useMyTasks = () =>
  useQuery({ queryKey: ["my-tasks"], queryFn: workerApi.getMyTasks });

export const useCharter = (taskId: string) =>
  useQuery({ queryKey: ["charter", taskId], queryFn: () => workerApi.getCharter(taskId) });

export const useTaskPacket = (taskId: string) =>
  useQuery({
    queryKey: ["task-packet", taskId],
    queryFn: () => workerApi.getTaskPacket(taskId),
    enabled: Boolean(taskId),
  });

export const useAcceptInterest = (taskId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => workerApi.acceptInterest(taskId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-tasks"] }),
  });
};

export const useReadyToStart = (taskId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => workerApi.readyToStart(taskId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["my-tasks"] });
      qc.invalidateQueries({ queryKey: ["charter", taskId] });
    },
  });
};

export const useSubmit = (taskId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { notes: string; asset_urls: string[] }) =>
      workerApi.submit(taskId, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["my-tasks"] });
      qc.invalidateQueries({ queryKey: ["task-qa", taskId] });
    },
  });
};

export const useTaskQA = (taskId: string, enabled = true) =>
  useQuery({
    queryKey: ["task-qa", taskId],
    queryFn: () => workerApi.getTaskQA(taskId),
    enabled: Boolean(taskId) && enabled,
  });

export const useAcceptDelivery = (orderId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => clientApi.acceptDelivery(orderId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["order", orderId] });
      qc.invalidateQueries({ queryKey: ["delivery", orderId] });
    },
  });
};

export const usePostDiscussion = (taskId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { body: string; message_type?: string; attachments?: string[] }) =>
      clientApi.postDiscussion(taskId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["discussion", taskId] }),
  });
};

// --- Amendments ------------------------------------------------------------

export const useAmendments = (orderId: string) =>
  useQuery({
    queryKey: ["amendments", orderId],
    queryFn: () => clientApi.listAmendments(orderId),
    enabled: Boolean(orderId),
  });

export const useApproveAmendment = (orderId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (amendmentId: string) => clientApi.approveAmendment(amendmentId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["amendments", orderId] });
      qc.invalidateQueries({ queryKey: ["order", orderId] });
    },
  });
};

export const useRejectAmendment = (orderId: string) => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (amendmentId: string) => clientApi.rejectAmendment(amendmentId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["amendments", orderId] }),
  });
};

// --- Notifications ---------------------------------------------------------

export const useNotifications = () =>
  useQuery({ queryKey: ["notifications"], queryFn: notificationsApi.list });
