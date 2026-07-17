/**
 * Worker profile completion — mirrors backend `compute_profile_completion_pct`
 * so the onboarding wizard can show a live meter that matches the server gate.
 *
 * Backend: `backend/app/schemas/worker.py` · Threshold: 70% to go live.
 */
import type {
  AvailabilityStatus,
  CommunityType,
  PortfolioItem,
  Proficiency,
  WorkerProfile,
  WorkerProfileSaveInput,
  WorkerSkill,
  WorkerTaskType,
  WorkerTool,
} from "./types";

export const PROFILE_LIVE_THRESHOLD = 70;

export type OnboardingStepId =
  | "basics"
  | "capabilities"
  | "portfolio"
  | "availability";

export interface OnboardingDraft {
  full_name: string;
  headline: string;
  bio: string;
  community_type: CommunityType;
  skills: WorkerSkill[];
  tools: WorkerTool[];
  task_types: WorkerTaskType[];
  portfolio: PortfolioItem[];
  github_url: string;
  figma_url: string;
  behance_url: string;
  linkedin_url: string;
  availability_status: AvailabilityStatus;
  weekly_hours_available: number;
  max_concurrent_tasks: number;
  payout_min: number | null;
  payout_max: number | null;
}

export function emptyOnboardingDraft(fullName = ""): OnboardingDraft {
  return {
    full_name: fullName,
    headline: "",
    bio: "",
    community_type: "both",
    skills: [],
    tools: [],
    task_types: [],
    portfolio: [],
    github_url: "",
    figma_url: "",
    behance_url: "",
    linkedin_url: "",
    availability_status: "available",
    weekly_hours_available: 15,
    max_concurrent_tasks: 2,
    payout_min: null,
    payout_max: null,
  };
}

export function draftFromProfile(profile: WorkerProfile): OnboardingDraft {
  return {
    full_name: profile.full_name || "",
    headline: profile.headline || "",
    bio: profile.bio || "",
    community_type: profile.community_type || "both",
    skills: profile.skills ?? [],
    tools: profile.tools ?? [],
    task_types: profile.task_types ?? [],
    portfolio: profile.portfolio ?? [],
    github_url: profile.github_url || "",
    figma_url: profile.figma_url || "",
    behance_url: profile.behance_url || "",
    linkedin_url: profile.linkedin_url || "",
    availability_status: profile.availability_status || "available",
    weekly_hours_available: profile.weekly_hours_available || 15,
    max_concurrent_tasks: profile.max_concurrent_tasks || 2,
    payout_min: profile.payout_min ?? null,
    payout_max: profile.payout_max ?? null,
  };
}

/** Same weights as `compute_profile_completion_pct` on the backend. */
export function computeProfileCompletionPct(draft: OnboardingDraft): number {
  let points = 0;
  const hasHeadline = Boolean(draft.headline.trim());
  const hasBio = Boolean(draft.bio.trim());
  if (hasHeadline && hasBio) points += 25;
  else if (hasHeadline || hasBio) points += 12;

  points += (Math.min(draft.skills.length, 3) / 3) * 15;
  points += (Math.min(draft.tools.length, 2) / 2) * 10;
  if (draft.task_types.length > 0) points += 15;
  if (draft.portfolio.length > 0) points += 20;
  if (draft.availability_status) points += 5;
  if (draft.payout_min != null || draft.payout_max != null) points += 5;
  if (
    draft.github_url.trim() ||
    draft.figma_url.trim() ||
    draft.behance_url.trim() ||
    draft.linkedin_url.trim()
  ) {
    points += 5;
  }
  return Math.min(100, Math.round(points));
}

export function isValidHttpUrl(value: string): boolean {
  if (!value.trim()) return false;
  try {
    const u = new URL(value.trim());
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

export function stepErrors(
  step: OnboardingStepId,
  draft: OnboardingDraft
): string[] {
  const errors: string[] = [];
  switch (step) {
    case "basics":
      if (draft.full_name.trim().length < 2) errors.push("Enter your full name.");
      if (draft.headline.trim().length < 12)
        errors.push("Headline should be at least 12 characters.");
      if (draft.bio.trim().length < 40)
        errors.push("Bio should be at least 40 characters — tell clients what you ship.");
      break;
    case "capabilities":
      if (draft.skills.length < 3) errors.push("Select at least 3 skills.");
      if (draft.tools.length < 2) errors.push("Select at least 2 tools.");
      if (draft.task_types.length < 1)
        errors.push("Pick at least one task type you want to be matched on.");
      break;
    case "portfolio":
      if (draft.portfolio.length < 1)
        errors.push("Add at least one portfolio project with a title and URL.");
      for (const item of draft.portfolio) {
        if (!item.title.trim()) errors.push("Every portfolio item needs a title.");
        if (!item.project_url || !isValidHttpUrl(item.project_url))
          errors.push(`“${item.title || "Project"}” needs a valid http(s) URL.`);
      }
      for (const [label, url] of [
        ["GitHub", draft.github_url],
        ["Figma", draft.figma_url],
        ["Behance", draft.behance_url],
        ["LinkedIn", draft.linkedin_url],
      ] as const) {
        if (url.trim() && !isValidHttpUrl(url))
          errors.push(`${label} URL must be a valid http(s) link.`);
      }
      break;
    case "availability":
      if (draft.weekly_hours_available < 5 || draft.weekly_hours_available > 60)
        errors.push("Weekly hours should be between 5 and 60.");
      if (draft.max_concurrent_tasks < 1 || draft.max_concurrent_tasks > 5)
        errors.push("Concurrent tasks should be between 1 and 5.");
      if (
        draft.payout_min != null &&
        draft.payout_max != null &&
        draft.payout_min > draft.payout_max
      ) {
        errors.push("Minimum payout cannot exceed maximum.");
      }
      break;
  }
  return errors;
}

export function draftToSaveInput(draft: OnboardingDraft): WorkerProfileSaveInput {
  const blankToNull = (v: string) => (v.trim() ? v.trim() : null);
  return {
    full_name: draft.full_name.trim(),
    community_type: draft.community_type,
    headline: draft.headline.trim(),
    bio: draft.bio.trim(),
    availability_status: draft.availability_status,
    weekly_hours_available: draft.weekly_hours_available,
    max_concurrent_tasks: draft.max_concurrent_tasks,
    payout_min: draft.payout_min,
    payout_max: draft.payout_max,
    github_url: blankToNull(draft.github_url),
    figma_url: blankToNull(draft.figma_url),
    behance_url: blankToNull(draft.behance_url),
    linkedin_url: blankToNull(draft.linkedin_url),
    skills: draft.skills,
    tools: draft.tools,
    task_types: draft.task_types,
    portfolio: draft.portfolio.map((p) => ({
      ...p,
      title: p.title.trim(),
      project_url: p.project_url?.trim() || null,
      description: p.description?.trim() || undefined,
    })),
    is_active: true,
  };
}

export const PROFICIENCY_OPTIONS: { value: Proficiency; label: string }[] = [
  { value: "beginner", label: "Beginner" },
  { value: "intermediate", label: "Intermediate" },
  { value: "advanced", label: "Advanced" },
  { value: "expert", label: "Expert" },
];

export const COMMUNITY_OPTIONS: { value: CommunityType; label: string; hint: string }[] = [
  { value: "design", label: "Design", hint: "Brand, UI, visual systems" },
  { value: "tech", label: "Tech", hint: "Frontend, backend, deploy" },
  { value: "both", label: "Both", hint: "Full-stack product craft" },
];

export const AVAILABILITY_OPTIONS: {
  value: AvailabilityStatus;
  label: string;
  hint: string;
}[] = [
  { value: "available", label: "Available", hint: "Ready for new invites" },
  { value: "busy", label: "Busy", hint: "Limited capacity this week" },
  { value: "unavailable", label: "Unavailable", hint: "Pause matching for now" },
];
