"use client";

import { useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCandidates, useSetPreferences } from "@/lib/hooks";
import Footer from "@/components/footer";

export default function WorkerPreferencesPage() {
  const router = useRouter();
  const routeParams = useParams<{ orderId: string; taskId: string }>();
  const orderId =
    typeof routeParams.orderId === "string" ? routeParams.orderId : "";
  const taskId =
    typeof routeParams.taskId === "string" ? routeParams.taskId : "";

  const {
    data: candidates,
    isLoading,
    isError,
    error,
    refetch,
  } = useCandidates(orderId, taskId);
  const setPreferences = useSetPreferences(orderId, taskId);

  const [ranked, setRanked] = useState<string[]>([]);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const handleAddCandidate = (workerId: string) => {
    if (!ranked.includes(workerId)) {
      setRanked([...ranked, workerId]);
    }
  };

  const handleRemoveCandidate = (workerId: string) => {
    setRanked(ranked.filter((id) => id !== workerId));
  };

  const handleMoveUp = (index: number) => {
    if (index > 0) {
      const newRanked = [...ranked];
      [newRanked[index - 1], newRanked[index]] = [
        newRanked[index],
        newRanked[index - 1],
      ];
      setRanked(newRanked);
    }
  };

  const handleMoveDown = (index: number) => {
    if (index < ranked.length - 1) {
      const newRanked = [...ranked];
      [newRanked[index], newRanked[index + 1]] = [
        newRanked[index + 1],
        newRanked[index],
      ];
      setRanked(newRanked);
    }
  };

  const handleSubmit = async () => {
    if (ranked.length < 3) {
      setSubmitError("Select at least 3 workers before confirming.");
      return;
    }

    setSubmitError(null);
    try {
      await setPreferences.mutateAsync(ranked);
      router.push(`/orders/${orderId}`);
    } catch (err) {
      setSubmitError(
        err instanceof Error
          ? err.message
          : "Failed to save preferences. Please try again."
      );
    }
  };

  if (!orderId || !taskId) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <main id="main-content" className="flex-1 flex items-center justify-center px-6">
          <p className="text-sm text-muted-foreground">Loading order…</p>
        </main>
        <Footer />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <main id="main-content" className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">Loading candidates...</p>
        </main>
        <Footer />
      </div>
    );
  }

  if (isError) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <main id="main-content" className="flex-1 flex items-center justify-center px-6">
          <div className="max-w-md text-center space-y-4">
            <p className="text-sm text-destructive">
              Could not load candidates
              {error instanceof Error ? `: ${error.message}` : "."}
            </p>
            <div className="flex items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => void refetch()}
                className="h-10 px-5 border border-border text-sm font-semibold"
              >
                Retry
              </button>
              <Link
                href={`/orders/${orderId}`}
                className="h-10 px-5 text-sm font-semibold text-primary underline inline-flex items-center"
              >
                Back to order
              </Link>
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  if (!candidates || candidates.length === 0) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <main id="main-content" className="flex-1 flex items-center justify-center px-6">
          <div className="max-w-lg text-center space-y-4">
            <p className="text-lg font-semibold">No candidates available</p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Matching needs live workers (≥70% profile, available/busy) whose
              skills or task types fit this milestone. Seed campus talent via
              admin verify, or have workers finish onboarding and go live.
            </p>
            <Link
              href={`/orders/${orderId}`}
              className="inline-flex h-10 px-5 text-sm font-semibold text-primary underline"
            >
              Back to order
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const unranked = candidates.filter((c) => !ranked.includes(c.worker_id));

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main id="main-content" className="flex-1 border-b border-border">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          <div className="mb-16">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-4">
              Select your team
            </p>
            <h1 className="text-4xl font-bold mb-4">Choose your workers</h1>
            <p className="text-lg text-muted-foreground max-w-2xl">
              Rank at least 3 workers in order of preference. We&apos;ll invite
              them starting with your top choice.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            <div className="lg:col-span-2">
              <h2 className="text-base font-semibold mb-4">Available workers</h2>
              <div className="space-y-4">
                {unranked.length > 0 ? (
                  unranked.map((candidate) => (
                    <div
                      key={candidate.worker_id}
                      className="border border-border p-6 bg-card hover:bg-muted/30 transition-colors"
                    >
                      <div className="flex gap-4 items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <h3 className="text-base font-semibold mb-1">
                            {candidate.full_name}
                          </h3>
                          <p className="text-sm text-muted-foreground mb-3">
                            {candidate.headline}
                          </p>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                            <div>
                              <p className="text-xs text-muted-foreground">
                                Tasks completed
                              </p>
                              <p className="text-sm font-medium">
                                {candidate.tasks_completed}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">
                                On-time rate
                              </p>
                              <p className="text-sm font-medium">
                                {candidate.on_time_pct}%
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">Level</p>
                              <p className="text-sm font-medium capitalize">
                                {candidate.seller_level}
                              </p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">
                                Availability
                              </p>
                              <p className="text-sm font-medium capitalize">
                                {candidate.availability}
                              </p>
                            </div>
                          </div>

                          <p className="text-sm text-muted-foreground italic border-l-2 border-primary pl-3">
                            &quot;{candidate.rationale}&quot;
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleAddCandidate(candidate.worker_id)}
                          className="flex-shrink-0 h-10 px-4 bg-primary text-primary-foreground text-xs font-semibold hover:opacity-90 transition-opacity self-start"
                        >
                          Add
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="border border-dashed border-border p-8 text-center">
                    <p className="text-sm text-muted-foreground">
                      All candidates added to your ranking
                    </p>
                  </div>
                )}
              </div>
            </div>

            <div className="lg:col-span-1">
              <div className="sticky top-24 border-2 border-border p-6 bg-card">
                <h2 className="text-base font-semibold mb-4">Your ranking</h2>

                {ranked.length > 0 ? (
                  <div className="space-y-3 mb-6">
                    {ranked.map((workerId, index) => {
                      const candidate = candidates.find(
                        (c) => c.worker_id === workerId
                      );
                      if (!candidate) return null;

                      return (
                        <div
                          key={workerId}
                          className="flex gap-3 items-center p-3 border border-border bg-muted/30 rounded-sm"
                        >
                          <div className="flex-shrink-0 w-6 h-6 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-xs font-bold">
                            {index + 1}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium truncate">
                              {candidate.full_name}
                            </p>
                          </div>
                          <div className="flex gap-1">
                            <button
                              type="button"
                              onClick={() => handleMoveUp(index)}
                              disabled={index === 0}
                              className="text-xs px-1 disabled:opacity-30"
                              aria-label="Move up"
                            >
                              ↑
                            </button>
                            <button
                              type="button"
                              onClick={() => handleMoveDown(index)}
                              disabled={index === ranked.length - 1}
                              className="text-xs px-1 disabled:opacity-30"
                              aria-label="Move down"
                            >
                              ↓
                            </button>
                            <button
                              type="button"
                              onClick={() => handleRemoveCandidate(workerId)}
                              className="text-xs px-1 text-destructive"
                              aria-label="Remove"
                            >
                              ×
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground mb-6">
                    Add workers from the left to build your ranking.
                  </p>
                )}

                {submitError ? (
                  <p className="text-xs text-destructive mb-3" role="alert">
                    {submitError}
                  </p>
                ) : null}

                <button
                  type="button"
                  onClick={() => void handleSubmit()}
                  disabled={ranked.length < 3 || setPreferences.isPending}
                  className="w-full h-11 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                >
                  {setPreferences.isPending
                    ? "Saving…"
                    : ranked.length < 3
                      ? `Need ${3 - ranked.length} more`
                      : "Confirm ranking"}
                </button>
                <p className="text-xs text-muted-foreground mt-3 text-center">
                  {ranked.length}/3 minimum selected
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
      <Footer />
    </div>
  );
}
