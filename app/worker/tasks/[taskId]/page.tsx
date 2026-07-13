"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import Header from "@/components/header";
import Footer from "@/components/footer";
import {
  useAcceptInterest,
  useCharter,
  useDiscussion,
  useMyTasks,
  useReadyToStart,
  useSubmit,
  useTaskPacket,
} from "@/lib/hooks";
import { taskStatusTone, taskStatusWorkerLabel } from "@/lib/state-labels";

export default function WorkerTaskDetail({ params }: { params: { taskId: string } }) {
  const { taskId } = params;
  const { data: tasks, isLoading: tasksLoading } = useMyTasks();
  const { data: charter, isLoading: charterLoading } = useCharter(taskId);
  const { data: packet, isLoading: packetLoading } = useTaskPacket(taskId);
  const { data: discussion } = useDiscussion(taskId);
  const acceptInterest = useAcceptInterest(taskId);
  const readyToStart = useReadyToStart(taskId);
  const submit = useSubmit(taskId);

  const [notes, setNotes] = useState("");
  const [assetUrl, setAssetUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [checklistDone, setChecklistDone] = useState<Record<string, boolean>>({});

  const task = useMemo(() => tasks?.find((t) => t.id === taskId), [tasks, taskId]);
  const loading = tasksLoading || charterLoading || packetLoading;

  const handleAccept = async () => {
    setError(null);
    try {
      await acceptInterest.mutateAsync();
    } catch {
      setError("Could not accept interest. Try again.");
    }
  };

  const handleReady = async () => {
    setError(null);
    try {
      await readyToStart.mutateAsync();
    } catch {
      setError("Could not start work. Try again.");
    }
  };

  const handleSubmit = async () => {
    setError(null);
    const urls = assetUrl
      .split(/[\n,]/)
      .map((s) => s.trim())
      .filter(Boolean);
    try {
      await submit.mutateAsync({ notes, asset_urls: urls });
    } catch {
      setError("Submit failed. Check notes and asset URLs.");
    }
  };

  if (loading) {
    return (
      <Shell>
        <p className="text-sm text-muted-foreground font-mono">Loading job card…</p>
      </Shell>
    );
  }

  if (!task) {
    return (
      <Shell>
        <h1 className="text-2xl font-bold mb-4">Task not found</h1>
        <Link href="/worker" className="text-sm text-primary font-semibold">
          ← Back to inbox
        </Link>
      </Shell>
    );
  }

  const tone = taskStatusTone[task.status] ?? "neutral";
  const canAccept = task.status === "invited" || task.status === "interest_pool" || task.status === "ready";
  const canReady = task.status === "priority_active";
  const canSubmit =
    task.status === "mutual_start" ||
    task.status === "in_progress" ||
    task.status === "rework" ||
    task.status === "start_requested";

  return (
    <Shell>
      <Link href="/worker" className="text-xs font-mono text-muted-foreground hover:text-primary">
        ← Inbox
      </Link>
      <div className="mt-4 flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <p className="text-xs font-mono tracking-widest uppercase text-primary mb-2">Job card</p>
          <h1 className="text-3xl font-bold tracking-tight">{task.title}</h1>
          <p className="text-sm text-muted-foreground mt-2">
            ₹{task.payout_amount.toLocaleString("en-IN")}
            {task.deadline
              ? ` · due ${new Date(task.deadline).toLocaleDateString()}`
              : ""}
          </p>
        </div>
        <span className="text-xs font-mono px-2 py-1 border border-border">
          {taskStatusWorkerLabel[task.status]} · {tone}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Charter */}
        <section className="border border-border p-5">
          <p className="text-xs font-mono uppercase tracking-wider text-primary mb-3">Charter</p>
          {charter ? (
            <>
              <p className="text-sm leading-relaxed mb-4">{charter.snapshot.scope}</p>
              <h3 className="text-xs font-mono uppercase text-muted-foreground mb-2">Deliverables</h3>
              <ul className="text-sm space-y-1 mb-4">
                {charter.snapshot.deliverables.map((d, i) => (
                  <li key={i}>
                    {d.name}
                    {d.format ? ` (${d.format})` : ""}
                  </li>
                ))}
              </ul>
              <h3 className="text-xs font-mono uppercase text-muted-foreground mb-2">
                Acceptance
              </h3>
              <ul className="text-sm space-y-1 mb-4">
                {charter.snapshot.acceptance_criteria.map((c, i) => (
                  <li key={i}>{c.criterion}</li>
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
            <p className="text-sm text-muted-foreground">Charter not available yet.</p>
          )}
        </section>

        {/* Task packet */}
        <section className="border border-border p-5">
          <p className="text-xs font-mono uppercase tracking-wider text-primary mb-3">
            Task packet
          </p>
          {packet ? (
            <>
              <p className="text-sm leading-relaxed mb-4">{packet.brief}</p>
              {packet.dependencies.length > 0 ? (
                <p className="text-xs text-muted-foreground mb-3">
                  Depends on: {packet.dependencies.join(", ")}
                </p>
              ) : null}
              <h3 className="text-xs font-mono uppercase text-muted-foreground mb-2">Checklist</h3>
              <ul className="space-y-2 mb-4">
                {packet.checklist.map((item) => (
                  <li key={item.id} className="flex items-start gap-2 text-sm">
                    <input
                      type="checkbox"
                      className="mt-1"
                      checked={checklistDone[item.id] ?? Boolean(item.done)}
                      onChange={(e) =>
                        setChecklistDone((prev) => ({ ...prev, [item.id]: e.target.checked }))
                      }
                    />
                    <span>
                      {item.label}
                      {item.required ? (
                        <span className="text-xs text-muted-foreground"> · required</span>
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
            <p className="text-sm text-muted-foreground">Packet not generated yet.</p>
          )}
        </section>
      </div>

      {/* Actions */}
      <section className="mt-8 border border-border p-5">
        <p className="text-xs font-mono uppercase tracking-wider text-primary mb-4">Actions</p>
        <div className="flex flex-wrap gap-3 mb-4">
          {canAccept ? (
            <button
              type="button"
              onClick={handleAccept}
              disabled={acceptInterest.isPending}
              className="h-10 px-5 bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50"
            >
              {acceptInterest.isPending ? "Accepting…" : "Accept interest"}
            </button>
          ) : null}
          {canReady ? (
            <button
              type="button"
              onClick={handleReady}
              disabled={readyToStart.isPending}
              className="h-10 px-5 bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50"
            >
              {readyToStart.isPending ? "Starting…" : "Ready to start"}
            </button>
          ) : null}
        </div>
        {canSubmit ? (
          <div className="flex flex-col gap-3 max-w-xl">
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              placeholder="Submission notes…"
              className="w-full border border-border bg-background px-3 py-2 text-sm"
            />
            <input
              value={assetUrl}
              onChange={(e) => setAssetUrl(e.target.value)}
              placeholder="Asset URLs (comma or newline separated)"
              className="w-full border border-border bg-background px-3 py-2 text-sm"
            />
            <button
              type="button"
              onClick={handleSubmit}
              disabled={submit.isPending || !notes.trim()}
              className="h-10 px-5 border border-primary text-primary text-sm font-semibold disabled:opacity-40 w-fit"
            >
              {submit.isPending ? "Submitting…" : "Submit work"}
            </button>
          </div>
        ) : null}
        {error ? <p className="text-xs text-destructive mt-3">{error}</p> : null}
        {task.status === "rework" ? (
          <p className="text-sm text-amber-800 mt-3">
            Rework requested — fix the checklist items and resubmit.
          </p>
        ) : null}
      </section>

      {/* Discussion */}
      <section className="mt-8 border border-border p-5">
        <p className="text-xs font-mono uppercase tracking-wider text-primary mb-4">Discussion</p>
        {discussion?.messages?.length ? (
          <ul className="space-y-3">
            {discussion.messages.map((m) => (
              <li key={m.id} className="text-sm">
                <span className="font-mono text-xs text-muted-foreground">{m.sender_name}</span>
                <p className="mt-1">{m.body}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">No messages yet.</p>
        )}
      </section>
    </Shell>
  );
}

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main id="main-content" className="flex-1 border-b border-border">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-16 lg:py-20">{children}</div>
      </main>
      <Footer />
    </div>
  );
}
