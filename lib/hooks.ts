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

export const useMe = () =>
  useQuery({ queryKey: ["me"], queryFn: authApi.me });

// --- Scope chat (job description extraction) -------------------------------

export const useStartScopeSession = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => chatApi.startScopeSession(),
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

// --- Client journey --------------------------------------------------------

export const useOrder = (orderId: string) =>
  useQuery({ queryKey: ["order", orderId], queryFn: () => clientApi.getOrder(orderId) });

export const usePlan = (orderId: string) =>
  useQuery({ queryKey: ["plan", orderId], queryFn: () => clientApi.getPlan(orderId) });

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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["order"] }),
  });
};

export const useQuote = (quoteId: string) =>
  useQuery({ queryKey: ["quote", quoteId], queryFn: () => clientApi.getQuote(quoteId) });

export const useCandidates = (orderId: string, taskId: string) =>
  useQuery({
    queryKey: ["candidates", orderId, taskId],
    queryFn: () => clientApi.getCandidates(orderId, taskId),
  });

export const useDelivery = (orderId: string) =>
  useQuery({
    queryKey: ["delivery", orderId],
    queryFn: () => clientApi.getDelivery(orderId),
    enabled: Boolean(orderId),
    retry: false,
  });

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
    onSuccess: () => qc.invalidateQueries({ queryKey: ["my-tasks"] }),
  });
};

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

// --- Notifications ---------------------------------------------------------

export const useNotifications = () =>
  useQuery({ queryKey: ["notifications"], queryFn: notificationsApi.list });
