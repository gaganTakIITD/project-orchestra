"use client";

import {
  useAcceptDelivery,
  useAmendments,
  useApproveAmendment,
  useDelivery,
  useDiscussion,
  useEnrichOrderPlan,
  useMe,
  useOrder,
  usePlan,
  usePostDiscussion,
  useRejectAmendment,
} from "@/lib/hooks";
import { useOrderLiveInvalidation } from "@/lib/live";
import { taskStatusClientLabel, orderStatusClientLabel } from "@/lib/state-labels";
import { AmendmentCard } from "@/components/amendment-card";
import Footer from "@/components/footer";
import JourneyStepper from "@/components/journey-stepper";
import { LedgerStrip } from "@/components/ledger-strip";
import {
  CLIENT_JOURNEY_STAGES,
  clientStageForOrder,
  isOrderCancelled,
} from "@/lib/journey";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

function isScopeFlaggedMessage(msg: {
  scope_flagged?: boolean;
  message_type?: string;
}): boolean {
  return Boolean(
    msg.scope_flagged || msg.message_type === "scope_change_request"
  );
}

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString("en-IN", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatPrice(price: number) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 0,
  }).format(Number(price));
}

export default function OrderTrackerPage() {
  const routeParams = useParams<{ orderId: string }>();
  const orderId =
    typeof routeParams.orderId === "string" ? routeParams.orderId : "";
  const [acceptError, setAcceptError] = useState<string | null>(null);
  const [acceptedFlash, setAcceptedFlash] = useState(false);
  const [chatTaskId, setChatTaskId] = useState("");
  const [chatInput, setChatInput] = useState("");
  const [chatError, setChatError] = useState<string | null>(null);
  const [milestonesOpen, setMilestonesOpen] = useState(false);
  const [enrichBanner, setEnrichBanner] = useState<string | null>(null);
  const enrichStarted = useRef(false);

  const { data: order, isPending: orderLoading, isError: orderError } =
    useOrder(orderId);
  const { data: plan, isPending: planLoading } = usePlan(orderId);
  const { data: delivery } = useDelivery(orderId);
  const { data: me } = useMe();
  const acceptDelivery = useAcceptDelivery(orderId);
  const enrichPlan = useEnrichOrderPlan();
  useOrderLiveInvalidation(orderId || undefined);

  // Progressive AI: after fast confirm, polish task briefs in parallel (background).
  useEffect(() => {
    if (!orderId || enrichStarted.current) return;
    let shouldEnrich = false;
    try {
      if (sessionStorage.getItem(`enrich_plan:${orderId}`) === "1") {
        shouldEnrich = true;
        sessionStorage.removeItem(`enrich_plan:${orderId}`);
      }
    } catch {
      /* ignore */
    }
    if (!shouldEnrich) return;
    enrichStarted.current = true;
    setEnrichBanner("Polishing task briefs with AI…");
    enrichPlan.mutate(orderId, {
      onSuccess: (res) => {
        if (res.tasks_enriched > 0) {
          setEnrichBanner(
            `AI updated ${res.tasks_enriched} task brief${res.tasks_enriched === 1 ? "" : "s"}.`
          );
        } else {
          setEnrichBanner(res.message || "Plan ready.");
        }
        window.setTimeout(() => setEnrichBanner(null), 6000);
      },
      onError: () => {
        setEnrichBanner(null);
      },
    });
  }, [orderId, enrichPlan]);

  const defaultChatTaskId = useMemo(() => {
    if (!plan?.tasks?.length) return "";
    const preferred =
      plan.tasks.find((t) =>
        [
          "ready",
          "invited",
          "priority_active",
          "in_progress",
          "submitted",
        ].includes(t.status)
      ) ?? plan.tasks[0];
    return preferred?.id ?? "";
  }, [plan?.tasks]);

  useEffect(() => {
    if (!chatTaskId && defaultChatTaskId) setChatTaskId(defaultChatTaskId);
  }, [chatTaskId, defaultChatTaskId]);

  const activeChatTaskId = chatTaskId || defaultChatTaskId;
  const { data: discussion, isPending: discussionPending } =
    useDiscussion(activeChatTaskId);
  const postDiscussion = usePostDiscussion(activeChatTaskId);
  const { data: amendmentsData } = useAmendments(orderId);
  const approveAmendment = useApproveAmendment(orderId);
  const rejectAmendment = useRejectAmendment(orderId);
  const chatTask = plan?.tasks.find((t) => t.id === activeChatTaskId);
  const hasScopeWarning = Boolean(
    discussion?.messages?.some((msg) => isScopeFlaggedMessage(msg))
  );
  const amendments = amendmentsData?.amendments ?? [];

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
      <Shell>
        <p className="text-sm font-mono text-muted-foreground">Loading outcome…</p>
      </Shell>
    );
  }

  if (orderError || !order || !plan) {
    return (
      <Shell>
        <h1 className="text-2xl font-serif font-bold mb-3">Outcome not found</h1>
        <p className="text-sm text-muted-foreground mb-6">
          This order may have moved or you may not have access.
        </p>
        <Link href="/orders" className="text-sm font-semibold text-primary">
          ← Back to My outcomes
        </Link>
      </Shell>
    );
  }

  const assembleTask =
    plan.tasks.find((t) => t.status === "ready" || t.status === "invited") ??
    null;
  const cancelled = isOrderCancelled(order.status);
  const isDelivered = order.status === "delivered";
  const isClosed = order.status === "closed" || Boolean(delivery?.accepted_at);
  const activeTasks = plan.tasks.filter(
    (t) => !["completed", "cancelled", "released", "blocked"].includes(t.status)
  );
  const completedCount = plan.tasks.filter((t) => t.status === "completed").length;

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main id="main-content" className="flex-1">
        <div className="max-w-5xl mx-auto px-6 lg:px-8 py-12 lg:py-16">
          {/* Header */}
          <div className="mb-8">
            {enrichBanner ? (
              <div className="mb-4 rounded-sm border border-primary/30 bg-primary/5 px-4 py-3 text-sm text-foreground">
                {enrichBanner}
              </div>
            ) : null}
            <div className="flex flex-wrap items-center gap-3 mb-3">
              <p className="text-xs font-mono tracking-widest uppercase text-primary">
                Outcome
              </p>
              <span className="text-xs font-mono uppercase tracking-wider border border-border px-2 py-0.5 text-muted-foreground">
                {orderStatusClientLabel[order.status]}
              </span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-serif font-bold tracking-tight text-balance mb-4">
              {isClosed
                ? "Outcome delivered"
                : isDelivered
                  ? "Your outcome is ready to review"
                  : "Your outcome in progress"}
            </h1>
            <div className="flex flex-wrap gap-x-8 gap-y-2 text-sm">
              <Meta label="Fixed price" value={formatPrice(order.price)} />
              <Meta label="Deadline" value={formatDate(order.deadline)} />
              <Meta
                label="Progress"
                value={`${order.progress_pct}% · ${completedCount}/${plan.tasks.length} tasks`}
              />
              <Meta
                label="Revisions"
                value={`${order.revision_limit} rounds`}
              />
            </div>
          </div>

          {cancelled ? (
            <div className="mb-8 border border-border bg-muted/40 px-5 py-4">
              <p className="text-sm font-semibold">This outcome was cancelled</p>
              <p className="text-sm text-muted-foreground mt-1">
                Funds follow the refund path if any were held.
              </p>
            </div>
          ) : null}

          {/* Stage CTA — primary action above the fold */}
          {!cancelled && assembleTask ? (
            <PrimaryBanner
              title="Assemble your team"
              body="Rank the specialists we shortlisted so we can invite your top choices first."
              href={`/orders/${orderId}/preferences/${assembleTask.id}`}
              cta="Assemble your team →"
            />
          ) : null}

          {!cancelled && isDelivered && !isClosed ? (
            <PrimaryBanner
              title="Review & accept delivery"
              body="Open the deliverables below. Accepting releases funds and closes the outcome."
              href="#deliverables"
              cta="Jump to deliverables →"
            />
          ) : null}

          {!cancelled && isClosed ? (
            <div className="mb-8 border border-primary/20 bg-primary/5 px-5 py-4">
              <p className="text-sm font-semibold">Outcome accepted</p>
              <p className="text-sm text-muted-foreground mt-1">
                Thanks — this order is closed. Funds move to Released on the strip below.
              </p>
            </div>
          ) : null}

          {(acceptedFlash || (isClosed && delivery?.accepted_at)) && !cancelled ? null : null}

          <div className="mb-8 grid grid-cols-1 lg:grid-cols-3 gap-4">
            <div className="lg:col-span-2 border border-border bg-card p-5">
              <JourneyStepper
                stages={CLIENT_JOURNEY_STAGES}
                currentStageId={clientStageForOrder(order.status)}
              />
            </div>
            <LedgerStrip
              ledgerState={order.ledger_state}
              orderStatus={order.status}
              deliveryAcceptedAt={delivery?.accepted_at}
              className="p-5"
            />
          </div>

          {/* Progress */}
          <div className="mb-10">
            <div className="flex justify-between items-center mb-2">
              <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
                Overall progress
              </p>
              <p className="text-sm font-semibold tabular-nums">{order.progress_pct}%</p>
            </div>
            <div className="w-full h-1.5 bg-border overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-500"
                style={{ width: `${order.progress_pct}%` }}
              />
            </div>
          </div>

          {/* What's happening now */}
          {activeTasks.length > 0 && !isDelivered && !isClosed ? (
            <section className="mb-10">
              <h2 className="text-base font-semibold mb-3">Happening now</h2>
              <ul className="border border-border divide-y divide-border">
                {activeTasks.map((task) => {
                  const canPick =
                    task.status === "ready" || task.status === "invited";
                  return (
                    <li
                      key={task.id}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-4 py-4"
                    >
                      <div>
                        <p className="text-sm font-medium">{task.title}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {taskStatusClientLabel[task.status]}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        {canPick ? (
                          <Link
                            href={`/orders/${orderId}/preferences/${task.id}`}
                            className="text-xs font-semibold text-primary hover:underline"
                          >
                            Pick team →
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
                    </li>
                  );
                })}
              </ul>
            </section>
          ) : null}

          {/* Deliverables — primary for delivery stage */}
          <section id="deliverables" className="mb-10 scroll-mt-24">
            <div className="flex items-end justify-between gap-4 mb-4">
              <div>
                <h2 className="text-lg font-semibold">Deliverables</h2>
                <p className="text-sm text-muted-foreground mt-1">
                  Final assets for review. Accepting closes the outcome.
                </p>
              </div>
            </div>

            {delivery ? (
              <div className="border border-border bg-card">
                {delivery.qa_summary ? (
                  <div className="px-5 py-4 border-b border-border">
                    <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-1">
                      Quality summary
                    </p>
                    <p className="text-sm leading-relaxed">{delivery.qa_summary}</p>
                  </div>
                ) : null}
                <ul className="divide-y divide-border">
                  {delivery.assets.map((asset) => (
                    <li
                      key={asset.url}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 px-5 py-4"
                    >
                      <div>
                        <a
                          href={asset.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-sm font-semibold text-primary hover:underline"
                        >
                          {asset.name}
                        </a>
                        <p className="text-xs font-mono text-muted-foreground mt-1">
                          {asset.type}
                        </p>
                      </div>
                      <a
                        href={asset.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-xs font-semibold border border-border px-3 py-1.5 hover:border-primary transition-colors self-start"
                      >
                        Open →
                      </a>
                    </li>
                  ))}
                </ul>
                <div className="px-5 py-5 border-t border-border bg-muted/20">
                  {isClosed ? (
                    <p className="text-sm font-semibold text-primary">
                      Outcome accepted
                      {delivery.accepted_at
                        ? ` · ${formatDate(delivery.accepted_at)}`
                        : ""}
                    </p>
                  ) : isDelivered ? (
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <p className="text-sm text-muted-foreground max-w-md">
                        Review every asset. Accepting confirms the outcome and
                        releases held funds.
                      </p>
                      <button
                        type="button"
                        disabled={acceptDelivery.isPending}
                        onClick={async () => {
                          setAcceptError(null);
                          try {
                            await acceptDelivery.mutateAsync();
                            setAcceptedFlash(true);
                          } catch {
                            setAcceptError("Could not accept delivery. Try again.");
                          }
                        }}
                        className="h-11 px-6 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 disabled:opacity-50 shrink-0"
                      >
                        {acceptDelivery.isPending
                          ? "Accepting…"
                          : "Accept delivery"}
                      </button>
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground">
                      Bundle unlocks when all work passes quality check.
                    </p>
                  )}
                  {acceptError ? (
                    <p className="text-xs text-destructive mt-3" role="alert">
                      {acceptError}
                    </p>
                  ) : null}
                  {acceptedFlash && !acceptError ? (
                    <p className="text-xs text-primary mt-3">
                      Accepted — funds moving to Released.
                    </p>
                  ) : null}
                </div>
              </div>
            ) : (
              <div className="border border-dashed border-border px-5 py-10 text-center">
                <p className="text-sm font-medium mb-1">No deliverables yet</p>
                <p className="text-sm text-muted-foreground max-w-sm mx-auto">
                  Assets appear here after the team submits work and quality
                  check advances the order.
                </p>
              </div>
            )}
          </section>

          {/* Chat + amendments */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
            <section>
              <div className="flex items-center justify-between gap-3 mb-3">
                <h2 className="text-base font-semibold">Chat with team</h2>
                <div className="flex items-center gap-2">
                  {hasScopeWarning ? (
                    <span className="text-[10px] font-mono uppercase tracking-wide px-2 py-0.5 border border-amber-600/40 bg-highlight text-highlight-foreground">
                      Scope note
                    </span>
                  ) : null}
                  {plan.tasks.length > 0 ? (
                    <select
                      value={activeChatTaskId}
                      onChange={(e) => setChatTaskId(e.target.value)}
                      className="text-xs border border-border bg-background px-2 py-1 max-w-[12rem]"
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

              <div className="border border-border bg-card flex flex-col min-h-[18rem]">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-xs text-muted-foreground">
                    {chatTask?.title ?? "Select a task"}
                  </p>
                </div>
                <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3 max-h-64">
                  {!activeChatTaskId ? (
                    <p className="text-sm text-muted-foreground">No tasks yet.</p>
                  ) : discussionPending ? (
                    <p className="text-sm text-muted-foreground">Loading…</p>
                  ) : discussion?.messages?.length ? (
                    discussion.messages.map((msg) => {
                      const isMine = Boolean(me?.id && msg.sender_id === me.id);
                      const isSystem = msg.message_type === "system";
                      const flagged = isScopeFlaggedMessage(msg);
                      return (
                        <div
                          key={msg.id}
                          className={
                            isMine && !isSystem
                              ? "flex justify-end"
                              : "flex justify-start"
                          }
                        >
                          <div
                            className={
                              flagged
                                ? "max-w-[90%] border border-amber-600/40 bg-highlight px-3 py-2 text-sm text-highlight-foreground"
                                : isMine && !isSystem
                                  ? "max-w-[90%] bg-primary text-primary-foreground px-3 py-2 text-sm"
                                  : "max-w-[90%] border border-border bg-muted/30 px-3 py-2 text-sm"
                            }
                          >
                            <p className="text-[10px] font-mono uppercase tracking-wide opacity-70 mb-1">
                              {msg.sender_name}
                              {flagged ? " · Scope" : ""}
                            </p>
                            <p className="leading-relaxed">{msg.body}</p>
                          </div>
                        </div>
                      );
                    })
                  ) : (
                    <p className="text-sm text-muted-foreground">
                      No messages yet — ask a question about this task.
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
                    placeholder="Message the team…"
                    className="w-full border border-border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:border-primary"
                    disabled={!activeChatTaskId || postDiscussion.isPending}
                  />
                  <div className="flex items-center gap-3">
                    <button
                      type="submit"
                      disabled={
                        !activeChatTaskId ||
                        !chatInput.trim() ||
                        postDiscussion.isPending
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
              <h2 className="text-base font-semibold mb-3">Amendments</h2>
              {amendments.length > 0 ? (
                <div className="space-y-3">
                  <p className="text-sm text-muted-foreground mb-2">
                    Scope changes from discussion — approve to update the charter.
                  </p>
                  {amendments.map((a) => (
                    <AmendmentCard
                      key={a.id}
                      amendment={a}
                      busy={
                        approveAmendment.isPending || rejectAmendment.isPending
                      }
                      onApprove={(id) => approveAmendment.mutate(id)}
                      onReject={(id) => rejectAmendment.mutate(id)}
                    />
                  ))}
                </div>
              ) : (
                <div className="border border-dashed border-border px-4 py-8 text-center">
                  <p className="text-sm text-muted-foreground">
                    No amendments. Scope changes from chat appear here.
                  </p>
                </div>
              )}
            </section>
          </div>

          {/* Full milestone history — collapsed by default */}
          <section className="border-t border-border pt-8">
            <button
              type="button"
              onClick={() => setMilestonesOpen((o) => !o)}
              className="flex w-full items-center justify-between text-left mb-4"
            >
              <h2 className="text-base font-semibold">Full plan</h2>
              <span className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                {milestonesOpen ? "Hide" : "Show"} · {plan.milestones.length}{" "}
                milestones
              </span>
            </button>
            {milestonesOpen ? (
              <div className="space-y-4">
                {plan.milestones.map((milestone, i) => {
                  const milestoneTasks = plan.tasks.filter((t) =>
                    milestone.task_ids.includes(t.id)
                  );
                  const done = milestoneTasks.every(
                    (t) => t.status === "completed"
                  );
                  return (
                    <div key={i} className="border border-border px-4 py-4">
                      <div className="flex items-center gap-3 mb-3">
                        <span
                          className={`w-6 h-6 flex items-center justify-center text-[10px] font-mono ${
                            done
                              ? "bg-primary text-primary-foreground"
                              : "bg-border text-muted-foreground"
                          }`}
                        >
                          {i + 1}
                        </span>
                        <div>
                          <p className="text-sm font-semibold">{milestone.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {milestone.client_label}
                          </p>
                        </div>
                      </div>
                      <ul className="space-y-2 pl-9">
                        {milestoneTasks.map((task) => (
                          <li
                            key={task.id}
                            className="flex justify-between gap-3 text-sm"
                          >
                            <span>{task.title}</span>
                            <span className="text-xs text-muted-foreground shrink-0">
                              {taskStatusClientLabel[task.status]}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main className="flex-1 flex items-center justify-center px-6">
        <div className="max-w-md text-center">{children}</div>
      </main>
      <Footer />
    </div>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-semibold">{value}</p>
    </div>
  );
}

function PrimaryBanner({
  title,
  body,
  href,
  cta,
}: {
  title: string;
  body: string;
  href: string;
  cta: string;
}) {
  const isHash = href.startsWith("#");
  const className =
    "mb-8 flex flex-col gap-4 bg-highlight p-6 text-highlight-foreground sm:flex-row sm:items-center sm:justify-between";
  const ctaClass =
    "inline-flex h-11 flex-shrink-0 items-center justify-center bg-primary px-6 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90";
  return (
    <div className={className}>
      <div>
        <p className="text-sm font-semibold">{title}</p>
        <p className="mt-1 text-sm text-highlight-foreground/80">{body}</p>
      </div>
      {isHash ? (
        <a href={href} className={ctaClass}>
          {cta}
        </a>
      ) : (
        <Link href={href} className={ctaClass}>
          {cta}
        </Link>
      )}
    </div>
  );
}
