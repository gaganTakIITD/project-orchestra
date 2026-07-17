"use client";

import { useMemo, useState, type ReactNode } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import Footer from "@/components/footer";
import JourneyStepper from "@/components/journey-stepper";
import {
  useAcceptInterest,
  useCharter,
  useDiscussion,
  useMyTasks,
  usePostDiscussion,
  useReadyToStart,
  useSubmit,
  useTaskPacket,
  useTaskQA,
} from "@/lib/hooks";
import { WORKER_JOURNEY_STAGES, workerStageForTask } from "@/lib/journey";
import { useTaskLiveInvalidation } from "@/lib/live";
import { taskStatusWorkerLabel } from "@/lib/state-labels";

function isScopeFlaggedMessage(msg: {
  scope_flagged?: boolean;
  message_type?: string;
}): boolean {
  return Boolean(
    msg.scope_flagged || msg.message_type === "scope_change_request"
  );
}

function isValidHttpUrl(value: string): boolean {
  try {
    const u = new URL(value.trim());
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

export default function WorkerTaskDetail() {
  const routeParams = useParams<{ taskId: string }>();
  const taskId =
    typeof routeParams.taskId === "string" ? routeParams.taskId : "";
  const { data: tasks, isLoading: tasksLoading } = useMyTasks();
  const { data: charter, isLoading: charterLoading } = useCharter(taskId);
  const { data: packet, isLoading: packetLoading } = useTaskPacket(taskId);

  const task = useMemo(
    () => tasks?.find((t) => t.id === taskId),
    [tasks, taskId]
  );
  // Discussion is allowed only after Accept interest sets assigned_worker_id.
  const canDiscuss = Boolean(task?.assigned_worker_id);
  const {
    data: discussion,
    isPending: discussionPending,
    isError: discussionIsError,
    error: discussionQueryError,
  } = useDiscussion(taskId, { enabled: Boolean(taskId) && canDiscuss });
  const postDiscussion = usePostDiscussion(taskId);
  const acceptInterest = useAcceptInterest(taskId);
  const readyToStart = useReadyToStart(taskId);
  const submit = useSubmit(taskId);
  useTaskLiveInvalidation(taskId || undefined);

  const [notes, setNotes] = useState("");
  const [assetUrl, setAssetUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatError, setChatError] = useState<string | null>(null);
  const [checklistDone, setChecklistDone] = useState<Record<string, boolean>>(
    {}
  );

  const { data: qaReview } = useTaskQA(taskId, task?.status === "rework");

  const requiredChecklist = packet?.checklist.filter((c) => c.required) ?? [];
  const requiredDone = requiredChecklist.every(
    (c) => checklistDone[c.id] ?? Boolean(c.done)
  );

  const handleAccept = async () => {
    setError(null);
    setSuccess(null);
    try {
      await acceptInterest.mutateAsync();
      setSuccess("Interest accepted — you have priority. Start when ready.");
    } catch {
      setError("Could not accept interest. Try again.");
    }
  };

  const handleReady = async () => {
    setError(null);
    setSuccess(null);
    try {
      await readyToStart.mutateAsync();
      setSuccess("Work started — deliver against the checklist, then submit.");
    } catch {
      setError("Could not start work. Try again.");
    }
  };

  const handleSubmit = async () => {
    setError(null);
    setSuccess(null);
    const urls = assetUrl
      .split(/[\n,]/)
      .map((s) => s.trim())
      .filter(Boolean);
    if (!notes.trim()) {
      setError("Add submission notes describing what you delivered.");
      return;
    }
    if (urls.length === 0) {
      setError("Add at least one asset URL (Figma, GitHub, live site, etc.).");
      return;
    }
    if (urls.some((u) => !isValidHttpUrl(u))) {
      setError("Every asset URL must be a valid http(s) link.");
      return;
    }
    if (requiredChecklist.length > 0 && !requiredDone) {
      setError("Check off all required checklist items before submitting.");
      return;
    }
    try {
      await submit.mutateAsync({ notes, asset_urls: urls });
      setSuccess("Submitted — in quality review. You'll see QA feedback if rework is needed.");
      setNotes("");
      setAssetUrl("");
    } catch {
      setError("Submit failed. Check notes and asset URLs.");
    }
  };

  const handleChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canDiscuss || !chatInput.trim() || postDiscussion.isPending) return;
    setChatError(null);
    const body = chatInput.trim();
    setChatInput("");
    try {
      await postDiscussion.mutateAsync({ body });
    } catch {
      setChatInput(body);
      setChatError("Message failed. Try again.");
    }
  };

  if (!taskId || tasksLoading) {
    return (
      <Shell>
        <p className="text-sm text-muted-foreground font-mono">Loading job card…</p>
      </Shell>
    );
  }

  if (!task) {
    return (
      <Shell>
        <h1 className="text-2xl font-serif font-bold mb-4">Task not found</h1>
        <Link href="/worker" className="text-sm text-primary font-semibold">
          ← Back to inbox
        </Link>
      </Shell>
    );
  }

  const workerStage = workerStageForTask(task.status);
  const canAccept =
    task.status === "invited" ||
    task.status === "interest_pool" ||
    task.status === "ready";
  const canReady = task.status === "priority_active";
  const canSubmit =
    task.status === "mutual_start" ||
    task.status === "in_progress" ||
    task.status === "rework" ||
    task.status === "start_requested";
  const inQa = task.status === "submitted";
  const done = task.status === "completed";

  return (
    <Shell>
      <Link
        href="/worker"
        className="text-xs font-mono text-muted-foreground hover:text-primary"
      >
        ← Inbox
      </Link>

      <div className="mt-4 flex flex-wrap items-start justify-between gap-4 mb-6">
        <div>
          <p className="text-xs font-mono tracking-widest uppercase text-primary mb-2">
            Job card
          </p>
          <h1 className="text-3xl font-serif font-bold tracking-tight">
            {task.title}
          </h1>
          <p className="text-sm text-muted-foreground mt-2">
            ₹{task.payout_amount.toLocaleString("en-IN")}
            {task.deadline
              ? ` · due ${new Date(task.deadline).toLocaleDateString("en-IN", {
                  month: "short",
                  day: "numeric",
                })}`
              : ""}
          </p>
        </div>
        <span className="text-xs font-mono uppercase tracking-wider border border-border px-2 py-1">
          {taskStatusWorkerLabel[task.status]}
        </span>
      </div>

      {workerStage ? (
        <div className="mb-8 border border-border bg-card p-5">
          <JourneyStepper
            stages={WORKER_JOURNEY_STAGES}
            currentStageId={workerStage}
          />
        </div>
      ) : null}

      {charterLoading || packetLoading ? (
        <p className="mb-4 text-sm text-muted-foreground font-mono">
          Loading charter &amp; packet…
        </p>
      ) : null}

      {/* Stage primary action */}
      {(canAccept || canReady || inQa || done) && (
        <div className="mb-8 bg-highlight text-highlight-foreground px-5 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold">
              {canAccept && "You're invited — accept to claim priority"}
              {canReady && "Priority active — confirm you're ready to start"}
              {inQa && "Submitted — waiting on quality review"}
              {done && "Passed QA — this task is complete"}
            </p>
            <p className="text-sm opacity-80 mt-1">
              {canAccept &&
                "Accepting starts your priority window. Be ready to begin soon after."}
              {canReady &&
                "Mutual start locks the charter. Deliver against the packet checklist."}
              {inQa && "You'll be notified if anything needs rework."}
              {done && "Payout follows the order ledger after client accept."}
            </p>
          </div>
          {canAccept ? (
            <button
              type="button"
              onClick={handleAccept}
              disabled={acceptInterest.isPending}
              className="h-11 px-6 bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50 shrink-0"
            >
              {acceptInterest.isPending ? "Accepting…" : "Accept interest"}
            </button>
          ) : null}
          {canReady ? (
            <button
              type="button"
              onClick={handleReady}
              disabled={readyToStart.isPending}
              className="h-11 px-6 bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50 shrink-0"
            >
              {readyToStart.isPending ? "Starting…" : "Ready to start"}
            </button>
          ) : null}
        </div>
      )}

      {task.status === "rework" ? (
        <div className="mb-8 border border-border bg-card px-5 py-4 space-y-3">
          <p className="text-sm font-semibold">Rework requested</p>
          {qaReview ? (
            <>
              <p className="text-sm leading-relaxed">{qaReview.feedback}</p>
              {qaReview.evidence?.length ? (
                <ul className="space-y-2">
                  {qaReview.evidence.map((e, i) => (
                    <li key={i} className="text-sm border-l-2 border-border pl-3">
                      <span className="font-mono text-xs text-muted-foreground">
                        {e.passed ? "pass" : "fail"} · {e.check_type}
                      </span>
                      <p className="mt-0.5">
                        {e.criterion}
                        {e.detail ? ` — ${e.detail}` : ""}
                      </p>
                    </li>
                  ))}
                </ul>
              ) : null}
            </>
          ) : (
            <p className="text-sm text-muted-foreground">Loading QA feedback…</p>
          )}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <section className="border border-border p-5">
          <p className="text-xs font-mono uppercase tracking-wider text-primary mb-3">
            Charter
          </p>
          {charter ? (
            <>
              <p className="text-sm leading-relaxed mb-4">
                {charter.snapshot.scope}
              </p>
              <h3 className="text-xs font-mono uppercase text-muted-foreground mb-2">
                Deliverables
              </h3>
              <ul className="text-sm space-y-1 mb-4">
                {charter.snapshot.deliverables.map((d, i) => (
                  <li key={i}>
                    {d.name}
                    {d.format ? ` (${d.format})` : ""}
                  </li>
                ))}
              </ul>
              <h3 className="text-xs font-mono uppercase text-muted-foreground mb-2">
                Out of scope
              </h3>
              <ul className="text-sm space-y-1 text-muted-foreground">
                {charter.snapshot.out_of_scope.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              Charter unlocks after mutual start.
            </p>
          )}
        </section>

        <section className="border border-border p-5">
          <p className="text-xs font-mono uppercase tracking-wider text-primary mb-3">
            Task packet
          </p>
          {packet ? (
            <>
              <p className="text-sm leading-relaxed mb-4">{packet.brief}</p>
              <h3 className="text-xs font-mono uppercase text-muted-foreground mb-2">
                Checklist
              </h3>
              <ul className="space-y-2 mb-4">
                {packet.checklist.map((item) => (
                  <li key={item.id} className="flex items-start gap-2 text-sm">
                    <input
                      type="checkbox"
                      className="mt-1"
                      checked={checklistDone[item.id] ?? Boolean(item.done)}
                      onChange={(e) =>
                        setChecklistDone((prev) => ({
                          ...prev,
                          [item.id]: e.target.checked,
                        }))
                      }
                      disabled={!canSubmit}
                    />
                    <span>
                      {item.label}
                      {item.required ? (
                        <span className="text-xs text-muted-foreground">
                          {" "}
                          · required
                        </span>
                      ) : null}
                    </span>
                  </li>
                ))}
              </ul>
              {packet.client_inputs.length > 0 ? (
                <>
                  <h3 className="text-xs font-mono uppercase text-muted-foreground mb-2">
                    Client inputs
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    {packet.client_inputs.join(", ")}
                  </p>
                </>
              ) : null}
            </>
          ) : (
            <p className="text-sm text-muted-foreground">
              Packet not generated yet.
            </p>
          )}
        </section>
      </div>

      {/* Submit */}
      {canSubmit ? (
        <section className="mb-8 border border-border p-5">
          <p className="text-xs font-mono uppercase tracking-wider text-primary mb-2">
            Submit work
          </p>
          <p className="text-sm text-muted-foreground mb-4">
            Check required items, paste asset links, and describe what you
            shipped. Quality review runs next.
          </p>
          <div className="flex flex-col gap-3 max-w-xl">
            <label className="block">
              <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-2 block">
                Notes *
              </span>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="What you delivered, how to review it, any caveats…"
                className="w-full border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:border-primary"
              />
            </label>
            <label className="block">
              <span className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-2 block">
                Asset URLs *
              </span>
              <textarea
                value={assetUrl}
                onChange={(e) => setAssetUrl(e.target.value)}
                rows={2}
                placeholder={"https://figma.com/…\nhttps://yoursite.vercel.app"}
                className="w-full border border-border bg-background px-3 py-2 text-sm font-mono focus:outline-none focus:border-primary"
              />
            </label>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={
                submit.isPending ||
                !notes.trim() ||
                (requiredChecklist.length > 0 && !requiredDone)
              }
              className="h-11 px-6 bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-40 w-fit"
            >
              {submit.isPending
                ? "Submitting…"
                : task.status === "rework"
                  ? "Resubmit work"
                  : "Submit work"}
            </button>
            {requiredChecklist.length > 0 && !requiredDone ? (
              <p className="text-xs text-muted-foreground">
                Complete required checklist items to enable submit.
              </p>
            ) : null}
          </div>
        </section>
      ) : null}

      {error ? (
        <p className="mb-4 text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
      {success ? (
        <p className="mb-4 text-sm text-primary" role="status">
          {success}
        </p>
      ) : null}

      {/* Discussion with composer — unlocked after Accept interest */}
      <section className="border border-border">
        <div className="flex items-center justify-between gap-3 px-5 py-3 border-b border-border">
          <p className="text-xs font-mono uppercase tracking-wider text-primary">
            Discussion
          </p>
          {discussion?.messages?.some((m) => isScopeFlaggedMessage(m)) ? (
            <span className="text-[10px] font-mono uppercase tracking-wide px-2 py-0.5 border border-border bg-highlight text-highlight-foreground">
              Scope note
            </span>
          ) : null}
        </div>
        <div className="px-5 py-4 space-y-3 max-h-64 overflow-y-auto">
          {!canDiscuss ? (
            <p className="text-sm text-muted-foreground">
              Accept interest to message the client about this task.
            </p>
          ) : discussionPending ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : discussionIsError ? (
            <p className="text-sm text-destructive" role="alert">
              {discussionQueryError instanceof Error
                ? discussionQueryError.message
                : "Could not load discussion."}
            </p>
          ) : discussion?.messages?.length ? (
            discussion.messages.map((m) => {
              const flagged = isScopeFlaggedMessage(m);
              return (
                <div
                  key={m.id}
                  className={
                    flagged
                      ? "text-sm border border-border bg-highlight/40 px-3 py-2"
                      : "text-sm"
                  }
                >
                  <span className="font-mono text-xs text-muted-foreground">
                    {m.sender_name}
                    {flagged ? " · Scope" : ""}
                  </span>
                  <p className="mt-1 leading-relaxed">{m.body}</p>
                </div>
              );
            })
          ) : (
            <p className="text-sm text-muted-foreground">
              No messages yet — ask the client if anything is unclear.
            </p>
          )}
        </div>
        <form
          onSubmit={handleChat}
          className="p-3 border-t border-border flex flex-col gap-2"
        >
          <textarea
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            rows={2}
            placeholder={
              canDiscuss
                ? "Message the client about this task…"
                : "Accept interest to unlock chat"
            }
            className="w-full border border-border bg-background px-3 py-2 text-sm resize-none focus:outline-none focus:border-primary disabled:opacity-50"
            disabled={!canDiscuss || postDiscussion.isPending}
          />
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={
                !canDiscuss || !chatInput.trim() || postDiscussion.isPending
              }
              className="h-9 px-4 bg-secondary text-secondary-foreground text-sm font-semibold disabled:opacity-50"
            >
              {postDiscussion.isPending ? "Sending…" : "Send"}
            </button>
            {chatError ? (
              <p className="text-xs text-destructive">{chatError}</p>
            ) : null}
          </div>
        </form>
      </section>
    </Shell>
  );
}

function Shell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main id="main-content" className="flex-1">
        <div className="max-w-5xl mx-auto px-6 lg:px-8 py-12 lg:py-16">
          {children}
        </div>
      </main>
      <Footer />
    </div>
  );
}
