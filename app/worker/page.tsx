"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import Footer from "@/components/footer";
import { useMyTasks, useWorkerProfile } from "@/lib/hooks";
import { PROFILE_LIVE_THRESHOLD } from "@/lib/profile-completion";
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

function useCountdown(iso: string | null | undefined): string | null {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!iso) return;
    const id = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(id);
  }, [iso]);
  if (!iso) return null;
  const end = new Date(iso).getTime();
  const ms = end - now;
  if (ms <= 0) return "Expired";
  const h = Math.floor(ms / 3_600_000);
  const m = Math.floor((ms % 3_600_000) / 60_000);
  const s = Math.floor((ms % 60_000) / 1000);
  if (h > 0) return `${h}h ${m}m left`;
  return `${m}m ${s}s left`;
}

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
  const completion = profile?.profile_completion_pct ?? 0;
  const needsProfile = !profile || completion < PROFILE_LIVE_THRESHOLD;
  const isLive = Boolean(profile?.is_active && completion >= PROFILE_LIVE_THRESHOLD);

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main id="main-content" className="flex-1 border-b border-border">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-16 lg:py-20">
          <div className="flex flex-col lg:flex-row lg:items-end lg:justify-between gap-6 mb-10">
            <div>
              <p className="text-xs font-mono tracking-widest uppercase text-primary mb-2">
                Worker workspace
              </p>
              <h1 className="text-3xl sm:text-4xl font-serif font-bold tracking-tight mb-2">
                {profile?.full_name
                  ? `${profile.full_name.split(" ")[0]}'s inbox`
                  : "Your inbox"}
              </h1>
              <p className="text-sm text-muted-foreground max-w-xl">
                {profile?.headline ||
                  "Tasks matched to your skills — open a job card to execute."}
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              {profile?.campus_verified ? (
                <span className="text-xs font-mono uppercase tracking-wider border border-primary/30 text-primary px-2 py-1">
                  Campus verified
                </span>
              ) : (
                <span className="text-xs font-mono uppercase tracking-wider border border-border text-muted-foreground px-2 py-1">
                  Verification pending
                </span>
              )}
              <span
                className={`text-xs font-mono uppercase tracking-wider px-2 py-1 border ${
                  isLive
                    ? "border-emerald-300 text-emerald-800 bg-emerald-50"
                    : "border-amber-300 text-amber-800 bg-amber-50"
                }`}
              >
                {isLive ? "Live · receiving invites" : "Not live yet"}
              </span>
              <Link
                href="/worker/onboarding"
                className="text-sm font-semibold text-primary hover:underline"
              >
                Edit profile →
              </Link>
            </div>
          </div>

          {needsProfile ? (
            <div className="mb-10 border border-amber-300/60 bg-amber-50/50 px-5 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <p className="text-sm font-semibold">
                  Profile {completion}% — need {PROFILE_LIVE_THRESHOLD}% to receive invites
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Finish identity, capabilities, portfolio, and capacity.
                </p>
              </div>
              <Link
                href="/worker/onboarding"
                className="inline-flex h-10 px-5 bg-primary text-primary-foreground text-sm font-semibold items-center justify-center shrink-0"
              >
                Complete profile
              </Link>
            </div>
          ) : null}

          {profile ? (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
              <Stat label="Completed" value={String(profile.stats?.tasks_completed ?? 0)} />
              <Stat label="On-time" value={`${profile.stats?.on_time_pct ?? 0}%`} />
              <Stat label="Rating" value={String(profile.stats?.avg_rating ?? "—")} />
              <Stat label="Profile" value={`${completion}%`} />
            </div>
          ) : null}

          {profile && (profile.skills.length > 0 || profile.task_types.length > 0) ? (
            <div className="mb-10 flex flex-wrap gap-2">
              {profile.task_types.slice(0, 6).map((tt) => (
                <span
                  key={tt.task_type_id}
                  className="text-xs font-mono border border-border px-2 py-1 text-muted-foreground"
                >
                  {tt.name}
                </span>
              ))}
              {profile.availability_status ? (
                <span className="text-xs font-mono border border-border px-2 py-1">
                  {profile.weekly_hours_available}h/wk · {profile.availability_status}
                </span>
              ) : null}
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
            <div className="border border-border px-6 py-12 text-center">
              <p className="text-sm text-muted-foreground mb-2">
                {needsProfile
                  ? "No invites yet — finish your profile to go live."
                  : "No tasks in this filter. New invites show up here."}
              </p>
              {needsProfile ? (
                <Link
                  href="/worker/onboarding"
                  className="text-sm text-primary font-semibold"
                >
                  Complete your profile →
                </Link>
              ) : null}
            </div>
          ) : (
            <ul className="flex flex-col border border-border divide-y divide-border">
              {filtered.map((task) => (
                <TaskRow key={task.id} task={task} />
              ))}
            </ul>
          )}
        </div>
      </main>
      <Footer />
    </div>
  );
}

function TaskRow({
  task,
}: {
  task: {
    id: string;
    title: string;
    status: TaskStatus;
    task_type_slug: string;
    payout_amount: number;
    priority_window_ends?: string | null;
  };
}) {
  const tone = taskStatusTone[task.status] ?? "neutral";
  const countdown = useCountdown(
    task.status === "priority_active" ? task.priority_window_ends : null
  );

  return (
    <li>
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
          {countdown ? (
            <span className="text-xs font-mono text-amber-700 tabular-nums">
              Priority · {countdown}
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
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-border px-4 py-3">
      <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <p className="text-xl font-semibold mt-1 tabular-nums">{value}</p>
    </div>
  );
}
