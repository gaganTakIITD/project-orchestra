"use client";

import {
  useAcceptDelivery,
  useDelivery,
  useDiscussion,
  useMe,
  useOrder,
  usePlan,
  usePostDiscussion,
} from "@/lib/hooks";
import { useOrderLiveInvalidation } from "@/lib/live";
import { taskStatusClientLabel, taskStatusTone } from "@/lib/state-labels";
import Header from "@/components/header";
import Footer from "@/components/footer";
import { LedgerStrip } from "@/components/ledger-strip";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

function isScopeFlaggedMessage(msg: {
  scope_flagged?: boolean;
  message_type?: string;
}): boolean {
  return Boolean(
    msg.scope_flagged || msg.message_type === "scope_change_request"
  );
}

const toneColors: Record<string, string> = {
  neutral: "bg-muted text-muted-foreground",
  info: "bg-blue-100 text-blue-900",
  active: "bg-indigo-100 text-indigo-900",
  review: "bg-amber-100 text-amber-900",
  success: "bg-green-100 text-green-900",
  danger: "bg-red-100 text-red-900",
};

export default function OrderTrackerPage() {
  const routeParams = useParams<{ orderId: string }>();
  const orderId =
    typeof routeParams.orderId === "string" ? routeParams.orderId : "";
  const [acceptError, setAcceptError] = useState<string | null>(null);
  const [chatTaskId, setChatTaskId] = useState<string>("");
  const [chatInput, setChatInput] = useState("");
  const [chatError, setChatError] = useState<string | null>(null);

  const { data: order, isPending: orderLoading } = useOrder(orderId);
  const { data: plan, isPending: planLoading } = usePlan(orderId);
  const { data: delivery } = useDelivery(orderId);
  const { data: me } = useMe();
  const acceptDelivery = useAcceptDelivery(orderId);
  useOrderLiveInvalidation(orderId || undefined);

  const defaultChatTaskId = useMemo(() => {
    if (!plan?.tasks?.length) return "";
    const preferred =
      plan.tasks.find((t) =>
        ["ready", "invited", "priority_active", "in_progress", "submitted", "qa_review"].includes(
          t.status
        )
      ) ?? plan.tasks[0];
    return preferred?.id ?? "";
  }, [plan?.tasks]);

  useEffect(() => {
    if (!chatTaskId && defaultChatTaskId) {
      setChatTaskId(defaultChatTaskId);
    }
  }, [chatTaskId, defaultChatTaskId]);

  const activeChatTaskId = chatTaskId || defaultChatTaskId;
  const { data: discussion, isPending: discussionPending } = useDiscussion(activeChatTaskId);
  const postDiscussion = usePostDiscussion(activeChatTaskId);
  const chatTask = plan?.tasks.find((t) => t.id === activeChatTaskId);
  const hasScopeWarning = Boolean(
    discussion?.messages?.some((msg) => isScopeFlaggedMessage(msg))
  );

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
    }).format(Number(price));
  };

  const handleSendChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeChatTaskId || !chatInput.trim() || postDiscussion.isPending) return;
    setChatError(null);
    const body = chatInput.trim();
    setChatInput("");
    try {
      await postDiscussion.mutateAsync({ body });
    } catch {
      setChatInput(body);
      setChatError("Message failed. Please try again.");
    }
  };

  if (!orderId || orderLoading || planLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">Loading order...</p>
        </main>
        <Footer />
      </div>
    );
  }

  if (!order || !plan) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">Order not found</p>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-5xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          <div className="mb-12">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-4">Order tracker</p>
            <h1 className="text-4xl font-bold mb-6">Your outcome in progress</h1>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Fixed price</p>
                <p className="text-lg font-semibold">{formatPrice(order.price)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Deadline</p>
                <p className="text-lg font-semibold">{formatDate(order.deadline)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Progress</p>
                <p className="text-lg font-semibold">{order.progress_pct}% complete</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Revisions</p>
                <p className="text-lg font-semibold">{order.revision_limit} rounds available</p>
              </div>
            </div>

            <div className="mt-8">
              <LedgerStrip
                orderStatus={order.status}
                deliveryAcceptedAt={delivery?.accepted_at}
              />
            </div>
          </div>

          <div className="mb-16">
            <div className="flex justify-between items-center mb-2">
              <p className="text-sm font-medium">Overall progress</p>
              <p className="text-sm text-muted-foreground">{order.progress_pct}%</p>
            </div>
            <div className="w-full h-2 bg-border rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${order.progress_pct}%` }}
              />
            </div>
          </div>

          <div className="space-y-8">
            {plan.milestones.map((milestone, i) => {
              const milestoneTasks = plan.tasks.filter((t) => milestone.task_ids.includes(t.id));
              const allTasksCompleted = milestoneTasks.every((t) => t.status === "completed");

              return (
                <section key={i} className="border border-border p-8 bg-card">
                  <div className="flex gap-4 mb-6">
                    <div className="flex-shrink-0">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                          allTasksCompleted
                            ? "bg-primary text-primary-foreground"
                            : "bg-border text-muted-foreground"
                        }`}
                      >
                        {i + 1}
                      </div>
                    </div>
                    <div className="flex-1">
                      <h2 className="text-lg font-semibold mb-1">{milestone.name}</h2>
                      <p className="text-sm text-muted-foreground">{milestone.client_label}</p>
                    </div>
                    {allTasksCompleted && (
                      <div className="text-xs font-mono tracking-widest uppercase text-green-600 font-semibold self-center">
                        ✓ Done
                      </div>
                    )}
                  </div>

                  <div className="space-y-3">
                    {milestoneTasks.map((task) => {
                      const tone = taskStatusTone[task.status];
                      const colorClass = toneColors[tone] || toneColors.neutral;
                      const statusLabel = taskStatusClientLabel[task.status];
                      const canPickTeam = task.status === "ready" || task.status === "invited";

                      return (
                        <div
                          key={task.id}
                          className="flex gap-4 items-start p-4 border border-border rounded-sm hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium">{task.title}</p>
                            {task.description && (
                              <p className="text-xs text-muted-foreground mt-1">{task.description}</p>
                            )}
                            <div className="mt-2 flex flex-wrap gap-2">
                              {canPickTeam ? (
                                <Link
                                  href={`/orders/${orderId}/preferences/${task.id}`}
                                  className="text-xs font-semibold text-primary hover:underline"
                                >
                                  Pick your team →
                                </Link>
                              ) : null}
                              <button
                                type="button"
                                onClick={() => setChatTaskId(task.id)}
                                className="text-xs text-muted-foreground hover:text-foreground"
                              >
                                Open chat
                              </button>
                            </div>
                          </div>
                          <span
                            className={`flex-shrink-0 text-xs px-3 py-1 rounded-full whitespace-nowrap font-medium ${colorClass}`}
                          >
                            {statusLabel}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>

          <div className="mt-16 pt-8 border-t border-border">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <section>
                <div className="flex items-center justify-between gap-3 mb-4">
                  <h2 className="text-base font-semibold">Chat with team</h2>
                  <div className="flex items-center gap-2">
                    {hasScopeWarning ? (
                      <span className="text-[10px] font-mono uppercase tracking-wide px-2 py-0.5 border border-amber-600/40 bg-amber-100 text-amber-900 dark:bg-amber-950/40 dark:text-amber-200">
                        Scope warning
                      </span>
                    ) : null}
                    {plan.tasks.length > 0 ? (
                      <select
                        value={activeChatTaskId}
                        onChange={(e) => setChatTaskId(e.target.value)}
                        className="text-xs border border-border bg-background px-2 py-1 max-w-[14rem]"
                      >
                        {plan.tasks.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.title}
                          </option>
                        ))}
                      </select>
                    ) : null}
                  </div>
                </div>

                <div className="border border-border bg-card flex flex-col min-h-[20rem]">
                  <div className="px-4 py-3 border-b border-border">
                    <p className="text-xs font-mono tracking-widest uppercase text-primary">
                      Task thread
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      {chatTask?.title ?? "Select a task"}
                    </p>
                  </div>

                  <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 max-h-72">
                    {!activeChatTaskId ? (
                      <p className="text-sm text-muted-foreground">No tasks on this plan yet.</p>
                    ) : discussionPending ? (
                      <p className="text-sm text-muted-foreground">Loading conversation…</p>
                    ) : discussion?.messages?.length ? (
                      discussion.messages.map((msg) => {
                        const isMine = Boolean(me?.id && msg.sender_id === me.id);
                        const isSystem = msg.message_type === "system";
                        const flagged = isScopeFlaggedMessage(msg);
                        return (
                          <div
                            key={msg.id}
                            className={isMine && !isSystem ? "flex justify-end" : "flex justify-start"}
                          >
                            <div
                              className={
                                flagged
                                  ? "max-w-[90%] border border-amber-600/50 bg-amber-50 dark:bg-amber-950/30 px-3 py-2 text-sm"
                                  : isMine && !isSystem
                                    ? "max-w-[90%] bg-primary text-primary-foreground px-3 py-2 text-sm"
                                    : "max-w-[90%] border border-border bg-muted/30 px-3 py-2 text-sm"
                              }
                            >
                              <div className="flex items-center gap-2 mb-1">
                                <p className="text-[10px] font-mono uppercase tracking-wide opacity-70">
                                  {msg.sender_name}
                                </p>
                                {flagged ? (
                                  <span className="text-[10px] font-mono uppercase tracking-wide text-amber-800 dark:text-amber-200">
                                    Scope change
                                  </span>
                                ) : null}
                              </div>
                              <p className="leading-relaxed">{msg.body}</p>
                            </div>
                          </div>
                        );
                      })
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        No messages yet — say hello to kick off this task thread.
                      </p>
                    )}
                  </div>

                  <form
                    onSubmit={handleSendChat}
                    className="p-3 border-t border-border flex flex-col gap-2"
                  >
                    <textarea
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      rows={2}
                      placeholder="Message the team about this task…"
                      className="w-full border border-border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:border-primary"
                      disabled={!activeChatTaskId || postDiscussion.isPending}
                    />
                    <div className="flex items-center gap-3">
                      <button
                        type="submit"
                        disabled={
                          !activeChatTaskId || !chatInput.trim() || postDiscussion.isPending
                        }
                        className="h-9 px-4 bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50"
                      >
                        {postDiscussion.isPending ? "Sending…" : "Send"}
                      </button>
                      {chatError ? (
                        <p className="text-xs text-destructive">{chatError}</p>
                      ) : null}
                    </div>
                  </form>
                </div>
              </section>

              <section>
                <h2 className="text-base font-semibold mb-4">Deliverables</h2>
                {delivery ? (
                  <div className="border border-border p-6 space-y-4">
                    <p className="text-sm text-muted-foreground">{delivery.qa_summary}</p>
                    <ul className="space-y-2">
                      {delivery.assets.map((asset) => (
                        <li key={asset.url} className="text-sm">
                          <a
                            href={asset.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-primary font-medium hover:underline"
                          >
                            {asset.name}
                          </a>
                          <span className="text-xs text-muted-foreground font-mono ml-2">
                            {asset.type}
                          </span>
                        </li>
                      ))}
                    </ul>
                    {order.status === "delivered" || order.status === "closed" ? (
                      <div className="pt-2">
                        {order.status === "closed" || delivery.accepted_at ? (
                          <p className="text-sm text-green-700 font-medium">Outcome accepted</p>
                        ) : (
                          <button
                            type="button"
                            disabled={acceptDelivery.isPending}
                            onClick={async () => {
                              setAcceptError(null);
                              try {
                                await acceptDelivery.mutateAsync();
                              } catch {
                                setAcceptError("Could not accept delivery.");
                              }
                            }}
                            className="h-10 px-5 bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50"
                          >
                            {acceptDelivery.isPending ? "Accepting…" : "Accept delivery"}
                          </button>
                        )}
                        {acceptError ? (
                          <p className="text-xs text-destructive mt-2">{acceptError}</p>
                        ) : null}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">
                        Bundle ready when work is submitted and QA advances the order.
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="border border-border p-6 rounded-sm bg-muted/30 text-center">
                    <p className="text-sm text-muted-foreground">Assets appear after submission</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Final files for review and acceptance
                    </p>
                  </div>
                )}
              </section>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
