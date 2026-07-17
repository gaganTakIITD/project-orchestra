"use client";

import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import Footer from "@/components/footer";
import { ApiError } from "@/lib/api";
import {
  useMe,
  useSaveWorkerProfile,
  useSetRole,
  useSkills,
  useTaskTypes,
  useTools,
  useWorkerProfile,
} from "@/lib/hooks";
import {
  AVAILABILITY_OPTIONS,
  COMMUNITY_OPTIONS,
  PROFILE_LIVE_THRESHOLD,
  PROFICIENCY_OPTIONS,
  computeProfileCompletionPct,
  draftFromProfile,
  draftToSaveInput,
  emptyOnboardingDraft,
  stepErrors,
  type OnboardingDraft,
  type OnboardingStepId,
} from "@/lib/profile-completion";
import type {
  PortfolioItem,
  Proficiency,
  Skill,
  TaskType,
  Tool,
  WorkerSkill,
  WorkerTaskType,
  WorkerTool,
} from "@/lib/types";

const STEPS: {
  id: OnboardingStepId;
  title: string;
  label: string;
}[] = [
  { id: "basics", title: "Identity", label: "Who you are" },
  { id: "capabilities", title: "Capabilities", label: "What you ship" },
  { id: "portfolio", title: "Proof", label: "Show your work" },
  { id: "availability", title: "Capacity", label: "When & how much" },
];

function newPortfolioItem(): PortfolioItem {
  return {
    id: `pf_${crypto.randomUUID().slice(0, 8)}`,
    worker_id: "",
    title: "",
    description: "",
    project_url: "",
    tags: [],
    tools_used: [],
    is_featured: false,
  };
}

export default function OnboardingContent() {
  const router = useRouter();
  const { data: me } = useMe();
  const { data: existing, isLoading: profileLoading } = useWorkerProfile();
  const { data: catalogSkills = [], isLoading: skillsLoading } = useSkills();
  const { data: catalogTools = [], isLoading: toolsLoading } = useTools();
  const { data: catalogTaskTypes = [], isLoading: typesLoading } = useTaskTypes();
  const saveProfile = useSaveWorkerProfile();
  const setRole = useSetRole();

  const [hydrated, setHydrated] = useState(false);
  const [draft, setDraft] = useState<OnboardingDraft>(() => emptyOnboardingDraft());
  const [step, setStep] = useState<OnboardingStepId>("basics");
  const [showErrors, setShowErrors] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const errorBannerRef = useRef<HTMLParagraphElement | null>(null);

  useEffect(() => {
    if (hydrated || profileLoading) return;
    if (existing && (existing.headline || existing.skills.length > 0)) {
      setDraft(draftFromProfile(existing));
    } else {
      setDraft(emptyOnboardingDraft(me?.full_name || existing?.full_name || ""));
    }
    setHydrated(true);
  }, [existing, me?.full_name, profileLoading, hydrated]);

  const completion = useMemo(() => computeProfileCompletionPct(draft), [draft]);
  const canGoLive = completion >= PROFILE_LIVE_THRESHOLD;
  const errors = useMemo(() => stepErrors(step, draft), [step, draft]);
  const stepIndex = STEPS.findIndex((s) => s.id === step);
  const taxonomyLoading = skillsLoading || toolsLoading || typesLoading;

  const patch = (partial: Partial<OnboardingDraft>) => {
    setDraft((prev) => ({ ...prev, ...partial }));
    setShowErrors(false);
    setSaveError(null);
  };

  const goNext = () => {
    const errs = stepErrors(step, draft);
    if (errs.length) {
      setShowErrors(true);
      return;
    }
    if (stepIndex < STEPS.length - 1) {
      setStep(STEPS[stepIndex + 1].id);
      setShowErrors(false);
    }
  };

  const goPrev = () => {
    if (stepIndex > 0) {
      setStep(STEPS[stepIndex - 1].id);
      setShowErrors(false);
    }
  };

  const handleComplete = async () => {
    const allErrors = STEPS.flatMap((s) => stepErrors(s.id, draft));
    if (allErrors.length) {
      setShowErrors(true);
      const firstBroken = STEPS.find((s) => stepErrors(s.id, draft).length > 0);
      if (firstBroken) setStep(firstBroken.id);
      setSaveError(allErrors[0] ?? "Fix the highlighted fields, then try again.");
      requestAnimationFrame(() => {
        errorBannerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      });
      return;
    }
    if (!canGoLive || saveProfile.isPending || setRole.isPending) return;
    setSaveError(null);
    try {
      if (me && me.role !== "worker" && me.role !== "admin") {
        await setRole.mutateAsync("worker");
      }
      const saved = await saveProfile.mutateAsync(draftToSaveInput(draft));
      if (saved.profile_completion_pct < PROFILE_LIVE_THRESHOLD || !saved.is_active) {
        setSaveError(
          `Profile saved at ${saved.profile_completion_pct}% — need ${PROFILE_LIVE_THRESHOLD}% and live status to enter matching.`
        );
        return;
      }
      router.replace("/worker?live=1");
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Could not save profile. Check your connection and try again.";
      setSaveError(message);
      requestAnimationFrame(() => {
        errorBannerRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      });
    }
  };

  const toggleSkill = (skill: Skill) => {
    const exists = draft.skills.some((s) => s.skill_id === skill.id);
    if (exists) {
      patch({ skills: draft.skills.filter((s) => s.skill_id !== skill.id) });
      return;
    }
    const next: WorkerSkill = {
      skill_id: skill.id,
      name: skill.name,
      proficiency: "intermediate",
    };
    patch({ skills: [...draft.skills, next] });
  };

  const toggleTool = (tool: Tool) => {
    const exists = draft.tools.some((t) => t.tool_id === tool.id);
    if (exists) {
      patch({ tools: draft.tools.filter((t) => t.tool_id !== tool.id) });
      return;
    }
    const next: WorkerTool = {
      tool_id: tool.id,
      name: tool.name,
      proficiency: "intermediate",
    };
    patch({ tools: [...draft.tools, next] });
  };

  const toggleTaskType = (tt: TaskType) => {
    const exists = draft.task_types.some((t) => t.task_type_id === tt.id);
    if (exists) {
      patch({ task_types: draft.task_types.filter((t) => t.task_type_id !== tt.id) });
      return;
    }
    const next: WorkerTaskType = {
      task_type_id: tt.id,
      name: tt.name,
      slug: tt.slug,
      proficiency: "intermediate",
    };
    patch({ task_types: [...draft.task_types, next] });
  };

  const setSkillProficiency = (skillId: string, proficiency: Proficiency) => {
    patch({
      skills: draft.skills.map((s) =>
        s.skill_id === skillId ? { ...s, proficiency } : s
      ),
    });
  };

  const updatePortfolio = (id: string, partial: Partial<PortfolioItem>) => {
    patch({
      portfolio: draft.portfolio.map((p) =>
        p.id === id ? { ...p, ...partial } : p
      ),
    });
  };

  if (!hydrated) {
    return (
      <div className="min-h-screen bg-background text-foreground flex items-center justify-center">
        <p className="text-sm font-mono text-muted-foreground">Loading profile…</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main id="main-content" className="flex-1">
        <div className="max-w-3xl mx-auto px-6 lg:px-8 py-12 lg:py-16">
          {/* Header */}
          <header className="mb-10">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-3">
              Talent onboarding
            </p>
            <h1 className="text-3xl sm:text-4xl font-serif font-bold tracking-tight mb-3">
              Build a matchable profile
            </h1>
            <p className="text-sm text-muted-foreground max-w-xl leading-relaxed">
              Clients rank workers from this profile. Complete identity, capabilities,
              proof of work, and capacity —{" "}
              <span className="text-foreground font-medium">
                {PROFILE_LIVE_THRESHOLD}% required to receive invites
              </span>
              .
            </p>

            {existing?.campus_verified ? (
              <p className="mt-4 text-xs font-mono uppercase tracking-wider text-primary">
                Campus verified
              </p>
            ) : (
              <p className="mt-4 text-xs text-muted-foreground">
                Campus verification is reviewed by Orchestra after you go live — not
                required to start onboarding.
              </p>
            )}
          </header>

          {/* Completion meter */}
          <div className="mb-10">
            <div className="flex items-end justify-between gap-4 mb-2">
              <div>
                <p className="text-2xl font-semibold tabular-nums">{completion}%</p>
                <p className="text-xs text-muted-foreground mt-0.5">
                  {canGoLive
                    ? "Ready to go live"
                    : `${PROFILE_LIVE_THRESHOLD - completion}% more to unlock matching`}
                </p>
              </div>
              <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider">
                Step {stepIndex + 1} of {STEPS.length}
              </p>
            </div>
            <div
              className="h-1.5 bg-border overflow-hidden"
              role="progressbar"
              aria-valuenow={completion}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Profile completion"
            >
              <motion.div
                className="h-full bg-primary"
                initial={false}
                animate={{ width: `${completion}%` }}
                transition={{ duration: 0.35 }}
              />
            </div>
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-[11px] font-mono text-muted-foreground uppercase tracking-wider">
              <span>Identity 25</span>
              <span>Skills 15 · Tools 10 · Types 15</span>
              <span>Portfolio 20</span>
              <span>Availability 5 · Range 5 · Links 5</span>
            </div>
          </div>

          {/* Step nav */}
          <nav aria-label="Onboarding steps" className="mb-10 grid grid-cols-2 sm:grid-cols-4 gap-2">
            {STEPS.map((s, idx) => {
              const done = stepErrors(s.id, draft).length === 0;
              const active = s.id === step;
              return (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => {
                    setStep(s.id);
                    setShowErrors(false);
                  }}
                  className={`text-left px-3 py-3 border transition-colors ${
                    active
                      ? "border-primary bg-primary text-primary-foreground"
                      : done
                        ? "border-border bg-card"
                        : "border-border"
                  }`}
                >
                  <p className="text-[10px] font-mono uppercase tracking-widest opacity-70">
                    {String(idx + 1).padStart(2, "0")}
                  </p>
                  <p className="text-sm font-semibold mt-1">{s.title}</p>
                  <p
                    className={`text-xs mt-0.5 ${
                      active ? "text-primary-foreground/80" : "text-muted-foreground"
                    }`}
                  >
                    {s.label}
                  </p>
                </button>
              );
            })}
          </nav>

          {/* Step body */}
          <AnimatePresence mode="wait">
            <motion.section
              key={step}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -6 }}
              transition={{ duration: 0.2 }}
              className="mb-10"
              aria-labelledby={`step-${step}-title`}
            >
              {step === "basics" && (
                <div className="space-y-6">
                  <StepIntro
                    id="step-basics-title"
                    title="Identity"
                    body="Name, craft lane, and a clear headline — this is what clients see first on match cards."
                  />
                  <Field label="Full name" required>
                    <input
                      type="text"
                      value={draft.full_name}
                      onChange={(e) => patch({ full_name: e.target.value })}
                      autoComplete="name"
                      placeholder="Your name"
                      className={inputClass}
                    />
                  </Field>
                  <Field label="Headline" required hint="One line — specialty + strength">
                    <input
                      type="text"
                      value={draft.headline}
                      onChange={(e) => patch({ headline: e.target.value })}
                      maxLength={120}
                      placeholder="Brand designer — systematic identities for startups"
                      className={inputClass}
                    />
                  </Field>
                  <Field
                    label="Bio"
                    required
                    hint="What you ship, domains you know, how you work"
                  >
                    <textarea
                      value={draft.bio}
                      onChange={(e) => patch({ bio: e.target.value })}
                      rows={5}
                      placeholder="IIT Delhi design community. I build brand systems and logos with a focus on clarity and reuse…"
                      className={`${inputClass} py-3 resize-y min-h-[120px]`}
                    />
                  </Field>
                  <Field label="Community" required>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      {COMMUNITY_OPTIONS.map((opt) => (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => patch({ community_type: opt.value })}
                          className={`text-left px-4 py-3 border transition-colors ${
                            draft.community_type === opt.value
                              ? "border-primary bg-primary/5"
                              : "border-border hover:border-primary/40"
                          }`}
                        >
                          <p className="text-sm font-semibold">{opt.label}</p>
                          <p className="text-xs text-muted-foreground mt-1">{opt.hint}</p>
                        </button>
                      ))}
                    </div>
                  </Field>
                </div>
              )}

              {step === "capabilities" && (
                <div className="space-y-8">
                  <StepIntro
                    id="step-capabilities-title"
                    title="Capabilities"
                    body="Pick from Orchestra’s taxonomy so matching stays consistent. Free-text inventing IDs is gone."
                  />
                  {taxonomyLoading ? (
                    <p className="text-sm text-muted-foreground font-mono">Loading catalog…</p>
                  ) : (
                    <>
                      <TaxonomyPicker
                        label="Skills"
                        required
                        hint="At least 3"
                        options={catalogSkills.map((s) => ({
                          id: s.id,
                          name: s.name,
                          meta: s.category,
                        }))}
                        selectedIds={draft.skills.map((s) => s.skill_id)}
                        onToggle={(id) => {
                          const skill = catalogSkills.find((s) => s.id === id);
                          if (skill) toggleSkill(skill);
                        }}
                      />
                      {draft.skills.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
                            Skill proficiency
                          </p>
                          {draft.skills.map((s) => (
                            <div
                              key={s.skill_id}
                              className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border border-border px-3 py-2"
                            >
                              <span className="text-sm font-medium">{s.name}</span>
                              <select
                                value={s.proficiency}
                                onChange={(e) =>
                                  setSkillProficiency(
                                    s.skill_id,
                                    e.target.value as Proficiency
                                  )
                                }
                                className="h-9 border border-border bg-background px-2 text-sm"
                              >
                                {PROFICIENCY_OPTIONS.map((p) => (
                                  <option key={p.value} value={p.value}>
                                    {p.label}
                                  </option>
                                ))}
                              </select>
                            </div>
                          ))}
                        </div>
                      )}
                      <TaxonomyPicker
                        label="Tools"
                        required
                        hint="At least 2"
                        options={catalogTools.map((t) => ({
                          id: t.id,
                          name: t.name,
                          meta: t.category,
                        }))}
                        selectedIds={draft.tools.map((t) => t.tool_id)}
                        onToggle={(id) => {
                          const tool = catalogTools.find((t) => t.id === id);
                          if (tool) toggleTool(tool);
                        }}
                      />
                      <TaxonomyPicker
                        label="Task types you want matched"
                        required
                        hint="At least 1 — this drives invites"
                        options={catalogTaskTypes
                          .filter(
                            (tt) =>
                              draft.community_type === "both" ||
                              tt.community_type === "both" ||
                              tt.community_type === draft.community_type
                          )
                          .map((tt) => ({
                            id: tt.id,
                            name: tt.name,
                            meta: tt.community_type,
                          }))}
                        selectedIds={draft.task_types.map((t) => t.task_type_id)}
                        onToggle={(id) => {
                          const tt = catalogTaskTypes.find((t) => t.id === id);
                          if (tt) toggleTaskType(tt);
                        }}
                      />
                    </>
                  )}
                </div>
              )}

              {step === "portfolio" && (
                <div className="space-y-6">
                  <StepIntro
                    id="step-portfolio-title"
                    title="Proof of work"
                    body="Real project URLs beat adjectives. Add work clients can open — Behance, GitHub, live sites, Figma."
                  />
                  <div className="space-y-4">
                    {draft.portfolio.map((item, idx) => (
                      <div key={item.id} className="border border-border p-4 space-y-3">
                        <div className="flex items-center justify-between">
                          <p className="text-xs font-mono uppercase tracking-widest text-muted-foreground">
                            Project {idx + 1}
                          </p>
                          <button
                            type="button"
                            onClick={() =>
                              patch({
                                portfolio: draft.portfolio.filter((p) => p.id !== item.id),
                              })
                            }
                            className="text-xs text-muted-foreground hover:text-destructive"
                          >
                            Remove
                          </button>
                        </div>
                        <Field label="Title" required>
                          <input
                            type="text"
                            value={item.title}
                            onChange={(e) =>
                              updatePortfolio(item.id, { title: e.target.value })
                            }
                            placeholder="Medlink — clinic brand identity"
                            className={inputClass}
                          />
                        </Field>
                        <Field label="Project URL" required>
                          <input
                            type="url"
                            value={item.project_url || ""}
                            onChange={(e) =>
                              updatePortfolio(item.id, { project_url: e.target.value })
                            }
                            placeholder="https://…"
                            className={inputClass}
                          />
                        </Field>
                        <Field label="Description">
                          <textarea
                            value={item.description || ""}
                            onChange={(e) =>
                              updatePortfolio(item.id, { description: e.target.value })
                            }
                            rows={2}
                            placeholder="What you delivered and why it worked"
                            className={`${inputClass} py-3 resize-y`}
                          />
                        </Field>
                      </div>
                    ))}
                    <button
                      type="button"
                      onClick={() =>
                        patch({ portfolio: [...draft.portfolio, newPortfolioItem()] })
                      }
                      className="h-10 px-4 border border-dashed border-border text-sm font-medium hover:border-primary transition-colors"
                    >
                      + Add project
                    </button>
                  </div>

                  <div className="pt-4 border-t border-border space-y-4">
                    <p className="text-sm font-semibold">Social & craft links</p>
                    <p className="text-xs text-muted-foreground -mt-2">
                      Optional but scored — at least one link adds 5% completion.
                    </p>
                    {(
                      [
                        ["github_url", "GitHub", "https://github.com/…"],
                        ["figma_url", "Figma", "https://figma.com/@…"],
                        ["behance_url", "Behance", "https://behance.net/…"],
                        ["linkedin_url", "LinkedIn", "https://linkedin.com/in/…"],
                      ] as const
                    ).map(([key, label, placeholder]) => (
                      <Field key={key} label={label}>
                        <input
                          type="url"
                          value={draft[key]}
                          onChange={(e) => patch({ [key]: e.target.value })}
                          placeholder={placeholder}
                          className={inputClass}
                        />
                      </Field>
                    ))}
                  </div>
                </div>
              )}

              {step === "availability" && (
                <div className="space-y-6">
                  <StepIntro
                    id="step-availability-title"
                    title="Capacity & payout range"
                    body="Bank and UPI details come later when payments go live. For matching we need your hours, concurrency, and preferred payout band."
                  />
                  <Field label="Availability status" required>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                      {AVAILABILITY_OPTIONS.map((opt) => (
                        <button
                          key={opt.value}
                          type="button"
                          onClick={() => patch({ availability_status: opt.value })}
                          className={`text-left px-4 py-3 border transition-colors ${
                            draft.availability_status === opt.value
                              ? "border-primary bg-primary/5"
                              : "border-border hover:border-primary/40"
                          }`}
                        >
                          <p className="text-sm font-semibold">{opt.label}</p>
                          <p className="text-xs text-muted-foreground mt-1">{opt.hint}</p>
                        </button>
                      ))}
                    </div>
                  </Field>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Field label="Weekly hours" required hint="5–60">
                      <input
                        type="number"
                        min={5}
                        max={60}
                        value={draft.weekly_hours_available}
                        onChange={(e) =>
                          patch({
                            weekly_hours_available: Number(e.target.value) || 0,
                          })
                        }
                        className={inputClass}
                      />
                    </Field>
                    <Field label="Max concurrent tasks" required hint="1–5">
                      <input
                        type="number"
                        min={1}
                        max={5}
                        value={draft.max_concurrent_tasks}
                        onChange={(e) =>
                          patch({
                            max_concurrent_tasks: Number(e.target.value) || 0,
                          })
                        }
                        className={inputClass}
                      />
                    </Field>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Field label="Payout min (₹)" hint="Optional — preferred floor">
                      <input
                        type="number"
                        min={0}
                        step={100}
                        value={draft.payout_min ?? ""}
                        onChange={(e) =>
                          patch({
                            payout_min: e.target.value
                              ? Number(e.target.value)
                              : null,
                          })
                        }
                        placeholder="1500"
                        className={inputClass}
                      />
                    </Field>
                    <Field label="Payout max (₹)" hint="Optional — preferred ceiling">
                      <input
                        type="number"
                        min={0}
                        step={100}
                        value={draft.payout_max ?? ""}
                        onChange={(e) =>
                          patch({
                            payout_max: e.target.value
                              ? Number(e.target.value)
                              : null,
                          })
                        }
                        placeholder="6000"
                        className={inputClass}
                      />
                    </Field>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed border-l-2 border-border pl-3">
                    Payments stay in sandbox ledger until Orchestra enables production
                    Razorpay. No bank or UPI collected here.
                  </p>
                </div>
              )}
            </motion.section>
          </AnimatePresence>

          {showErrors && errors.length > 0 ? (
            <div
              role="alert"
              className="mb-6 border border-destructive/30 bg-destructive/5 px-4 py-3"
            >
              <p className="text-xs font-mono uppercase tracking-widest text-destructive mb-2">
                Fix before continuing
              </p>
              <ul className="space-y-1">
                {errors.map((err) => (
                  <li key={err} className="text-sm text-destructive">
                    {err}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {saveError ? (
            <p
              ref={errorBannerRef}
              className="mb-4 text-sm text-destructive"
              role="alert"
            >
              {saveError}
            </p>
          ) : null}

          {/* Actions */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2 border-t border-border">
            <button
              type="button"
              onClick={goPrev}
              disabled={stepIndex === 0}
              className="h-11 px-5 border border-border text-sm font-semibold hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Back
            </button>

            {stepIndex < STEPS.length - 1 ? (
              <button
                type="button"
                onClick={goNext}
                className="h-11 px-8 bg-secondary text-secondary-foreground text-sm font-semibold hover:opacity-90 transition-opacity"
              >
                Continue
              </button>
            ) : (
              <button
                type="button"
                onClick={() => void handleComplete()}
                disabled={!canGoLive || saveProfile.isPending || setRole.isPending}
                className="h-11 px-8 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
              >
                {saveProfile.isPending || setRole.isPending
                  ? "Going live…"
                  : canGoLive
                    ? "Go live → inbox"
                    : `Reach ${PROFILE_LIVE_THRESHOLD}% to go live`}
              </button>
            )}
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}

const inputClass =
  "w-full h-11 border border-border bg-background px-4 text-sm focus:outline-none focus:border-primary transition-colors";

function StepIntro({
  id,
  title,
  body,
}: {
  id: string;
  title: string;
  body: string;
}) {
  return (
    <div className="mb-2">
      <h2 id={id} className="text-xl font-semibold tracking-tight">
        {title}
      </h2>
      <p className="text-sm text-muted-foreground mt-2 leading-relaxed">{body}</p>
    </div>
  );
}

function Field({
  label,
  hint,
  required,
  children,
}: {
  label: string;
  hint?: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="flex items-baseline justify-between gap-2 mb-2">
        <span className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
          {label}
          {required ? <span className="text-primary"> *</span> : null}
        </span>
        {hint ? (
          <span className="text-[11px] text-muted-foreground">{hint}</span>
        ) : null}
      </span>
      {children}
    </label>
  );
}

function TaxonomyPicker({
  label,
  hint,
  required,
  options,
  selectedIds,
  onToggle,
}: {
  label: string;
  hint?: string;
  required?: boolean;
  options: { id: string; name: string; meta?: string }[];
  selectedIds: string[];
  onToggle: (id: string) => void;
}) {
  return (
    <div>
      <div className="flex items-baseline justify-between gap-2 mb-3">
        <p className="text-xs font-mono tracking-widest uppercase text-muted-foreground">
          {label}
          {required ? <span className="text-primary"> *</span> : null}
        </p>
        {hint ? <p className="text-[11px] text-muted-foreground">{hint}</p> : null}
      </div>
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const selected = selectedIds.includes(opt.id);
          return (
            <button
              key={opt.id}
              type="button"
              onClick={() => onToggle(opt.id)}
              aria-pressed={selected}
              className={`inline-flex items-center gap-2 h-9 px-3 text-sm border transition-colors ${
                selected
                  ? "border-primary bg-primary text-primary-foreground"
                  : "border-border hover:border-primary/50"
              }`}
            >
              {opt.name}
              {opt.meta ? (
                <span
                  className={`text-[10px] font-mono uppercase tracking-wider ${
                    selected ? "opacity-70" : "text-muted-foreground"
                  }`}
                >
                  {opt.meta}
                </span>
              ) : null}
            </button>
          );
        })}
      </div>
      <p className="text-xs text-muted-foreground mt-2">
        {selectedIds.length} selected
      </p>
    </div>
  );
}
