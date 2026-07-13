"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import Footer from "@/components/footer";
import { useMyTasks, useWorkerProfile } from "@/lib/hooks";
import { taskStatusTone, taskStatusWorkerLabel } from "@/lib/state-labels";
import type { TaskStatus } from "@/lib/types";

type StatusFilter = "all" | TaskStatus;

const TONE_CLASS: Record<string, string> = {
  neutral: "bg-muted text-muted-foreground border-border",
  info: "bg-sky-50 text-sky-800 border-sky-200",
  active: "bg-primary/10 text-primary border-primary/20",
  review: "bg-amber-50 text-amber-800 border-amber-200",
  success: "bg-emerald-50 text-emerald-800 border-emerald-200",
  danger: "bg-destructive/10 text-destructive border-destructive/20",
};

export default function WorkerDashboard() {
  const { data: profile, isLoading: profileLoading } = useWorkerProfile();
  const { data: tasks, isLoading: tasksLoading } = useMyTasks();
  const [filter, setFilter] = useState<StatusFilter>("all");

  const filtered = useMemo(() => {
    if (!tasks) return [];
    if (filter === "all") return tasks;
    return tasks.filter((t) => t.status === filter);
  }, [tasks, filter]);

  const loading = profileLoading || tasksLoading;

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main id="main-content" className="flex-1 border-b border-border">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-16 lg:py-20">
          <p className="text-xs font-mono tracking-widest uppercase text-primary mb-2">
            Worker workspace
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-2">
            {profile?.full_name ? `${profile.full_name.split(" ")[0]}'s inbox` : "Your inbox"}
          </h1>
          <p className="text-sm text-muted-foreground mb-10 max-w-xl">
            {profile?.headline || "Tasks matched to your skills — open a job card to execute."}
          </p>

          {profile ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
              <Stat label="Completed" value={String(profile.stats?.tasks_completed ?? 0)} />
              <Stat label="On-time" value={`${profile.stats?.on_time_pct ?? 0}%`} />
              <Stat label="Rating" value={String(profile.stats?.avg_rating ?? "—")} />
              <Stat
                label="Profile"
                value={`${profile.profile_completion_pct}%`}
              />
            </div>
          ) : null}

          <div className="flex flex-wrap gap-2 mb-6">
            {(["all", "ready", "invited", "in_progress", "submitted", "rework"] as const).map(
              (key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => setFilter(key)}
                  className={
                    filter === key
                      ? "h-8 px-3 text-xs font-mono uppercase tracking-wider bg-primary text-primary-foreground"
                      : "h-8 px-3 text-xs font-mono uppercase tracking-wider border border-border text-muted-foreground"
                  }
                >
                  {key === "all" ? "All" : taskStatusWorkerLabel[key]}
                </button>
              )
            )}
          </div>

          {loading ? (
            <p className="text-sm text-muted-foreground font-mono">Loading tasks…</p>
          ) : filtered.length === 0 ? (
            <div className="border border-border p-10 text-center">
              <p className="text-sm text-muted-foreground mb-4">No tasks in this filter yet.</p>
              <Link href="/worker/onboarding" className="text-sm text-primary font-semibold">
                Complete your profile →
              </Link>
            </div>
          ) : (
            <ul className="flex flex-col border border-border divide-y divide-border">
              {filtered.map((task) => {
                const tone = taskStatusTone[task.status] ?? "neutral";
                return (
                  <li key={task.id}>
                    <Link
                      href={`/worker/tasks/${task.id}`}
                      className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-5 py-4 hover:bg-muted/40 transition-colors"
                    >
                      <div>
                        <p className="text-sm font-semibold">{task.title}</p>
                        <p className="text-xs text-muted-foreground mt-1 font-mono">
                          {task.task_type_slug} · ₹{task.payout_amount.toLocaleString("en-IN")}
                        </p>
                      </div>
                      <div className="flex items-center gap-3">
                        {task.priority_window_ends ? (
                          <span className="text-xs font-mono text-amber-700">
                            Priority until{" "}
                            {new Date(task.priority_window_ends).toLocaleString()}
                          </span>
                        ) : null}
                        <span
                          className={`text-xs font-mono px-2 py-1 border ${TONE_CLASS[tone] ?? TONE_CLASS.neutral}`}
                        >
                          {taskStatusWorkerLabel[task.status]}
                        </span>
                      </div>
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-border px-4 py-3">
      <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="text-xl font-semibold mt-1">{value}</p>
    </div>
  );
}
