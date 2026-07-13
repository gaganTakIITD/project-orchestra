"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { User, WorkerProfile } from "@/lib/types";
import { useSetRole } from "@/lib/hooks";

type PortalId = "client" | "worker" | "admin";

type PortalDef = {
  id: PortalId;
  label: string;
  title: string;
  description: string;
  bullets: string[];
  homeHref: string;
  homeLabel: string;
  secondaryHref?: string;
  secondaryLabel?: string;
};

const PORTALS: PortalDef[] = [
  {
    id: "client",
    label: "Client portal",
    title: "Scope & receive outcomes",
    description:
      "Co-create your job description with AI, confirm a fixed quote, and track delivery end to end.",
    bullets: [
      "Scope chat → live OutcomeSpec",
      "Confirm quote → live tracker",
      "Pick talent & accept delivery",
    ],
    homeHref: "/start",
    homeLabel: "Begin an outcome",
  },
  {
    id: "worker",
    label: "Worker portal",
    title: "Build profile & execute tasks",
    description:
      "Complete your talent profile, get matched to verified outcomes, and deliver against a frozen charter.",
    bullets: [
      "Profile wizard (≥70% to go live)",
      "Task inbox & job cards",
      "Submit work → QA → payout",
    ],
    homeHref: "/worker",
    homeLabel: "Open inbox",
    secondaryHref: "/worker/onboarding",
    secondaryLabel: "Complete profile",
  },
  {
    id: "admin",
    label: "Admin console",
    title: "Ops & audit (read-only)",
    description:
      "Inspect order state, event_log timelines, and AI decision audit — founder/ops only.",
    bullets: [
      "Order list + status filter",
      "Per-order event timeline",
      "AI decision log",
    ],
    homeHref: "/admin",
    homeLabel: "Open console",
  },
];

export default function PortalHub({
  user,
  workerProfile,
}: {
  user: User;
  workerProfile?: WorkerProfile | null;
}) {
  const router = useRouter();
  const setRole = useSetRole();
  const activeRole = user.role;
  const visiblePortals = PORTALS.filter((p) => p.id !== "admin" || activeRole === "admin");

  const enterPortal = async (portal: PortalDef) => {
    if (portal.id === "admin") {
      router.push(portal.homeHref);
      return;
    }
    if (portal.id !== activeRole) {
      try {
        await setRole.mutateAsync(portal.id);
      } catch {
        return;
      }
    }
    if (portal.id === "worker") {
      const pct = workerProfile?.profile_completion_pct ?? 0;
      router.push(pct >= 70 ? portal.homeHref : (portal.secondaryHref ?? portal.homeHref));
      return;
    }
    router.push(portal.homeHref);
  };

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground max-w-2xl">
        Orchestra has three portals — same sign-in, different home. Your active role is{" "}
        <span className="font-medium text-foreground capitalize">{activeRole}</span>.
        Switch below to enter the right workspace.
      </p>

      <div className="grid gap-6 lg:grid-cols-3">
        {visiblePortals.map((portal) => {
          const isActive = portal.id === activeRole;
          return (
            <article
              key={portal.id}
              className={`flex flex-col rounded-xl border p-6 lg:p-7 gap-5 ${
                isActive ? "border-primary bg-primary/5" : "border-border"
              }`}
            >
              <div className="space-y-2">
                <p className="text-xs font-mono tracking-widest uppercase text-primary">
                  {portal.label}
                </p>
                <h2 className="text-lg font-semibold tracking-tight">{portal.title}</h2>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {portal.description}
                </p>
              </div>

              <ul className="flex flex-col gap-2 text-sm flex-1">
                {portal.bullets.map((b) => (
                  <li key={b} className="flex items-start gap-2">
                    <span className="w-1.5 h-1.5 bg-primary mt-2 shrink-0" aria-hidden />
                    <span>{b}</span>
                  </li>
                ))}
              </ul>

              {portal.id === "worker" && workerProfile ? (
                <p className="text-xs text-muted-foreground">
                  Profile {workerProfile.profile_completion_pct}% complete
                  {workerProfile.profile_completion_pct < 70 ? " — finish onboarding to go live" : ""}
                </p>
              ) : null}

              <div className="flex flex-col gap-2 pt-1">
                <button
                  type="button"
                  disabled={setRole.isPending}
                  onClick={() => enterPortal(portal)}
                  className={`inline-flex items-center justify-center h-10 px-5 rounded-full text-sm font-semibold transition-opacity ${
                    isActive
                      ? "bg-primary text-primary-foreground hover:opacity-90"
                      : "bg-secondary text-secondary-foreground hover:opacity-85"
                  }`}
                >
                  {isActive ? portal.homeLabel : `Enter as ${portal.id}`}
                </button>
                {portal.secondaryHref && portal.id === "worker" ? (
                  <Link
                    href={portal.secondaryHref}
                    className="text-center text-xs text-muted-foreground hover:text-foreground underline"
                  >
                    {portal.secondaryLabel}
                  </Link>
                ) : null}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
