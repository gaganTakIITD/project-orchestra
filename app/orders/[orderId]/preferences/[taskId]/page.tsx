'use client';

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCandidates, useSetPreferences } from "@/lib/hooks";
import Header from "@/components/header";
import Footer from "@/components/footer";

export default function WorkerPreferencesPage({
  params,
}: {
  params: { orderId: string; taskId: string };
}) {
  const router = useRouter();
  const { orderId, taskId } = params;

  const { data: candidates, isLoading } = useCandidates(orderId, taskId);
  const setPreferences = useSetPreferences(orderId, taskId);

  const [ranked, setRanked] = useState<string[]>([]);

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
      [newRanked[index - 1], newRanked[index]] = [newRanked[index], newRanked[index - 1]];
      setRanked(newRanked);
    }
  };

  const handleMoveDown = (index: number) => {
    if (index < ranked.length - 1) {
      const newRanked = [...ranked];
      [newRanked[index], newRanked[index + 1]] = [newRanked[index + 1], newRanked[index]];
      setRanked(newRanked);
    }
  };

  const handleSubmit = async () => {
    if (ranked.length < 3) {
      alert("Please select at least 3 workers");
      return;
    }

    try {
      await setPreferences.mutateAsync(ranked);
      router.back();
    } catch (error) {
      alert("Failed to save preferences. Please try again.");
      console.error("[v0] Preference save failed:", error);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">Loading candidates...</p>
        </main>
        <Footer />
      </div>
    );
  }

  if (!candidates || candidates.length === 0) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">No candidates available</p>
        </main>
        <Footer />
      </div>
    );
  }

  const unranked = candidates.filter((c) => !ranked.includes(c.worker_id));

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          
          {/* Header */}
          <div className="mb-16">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-4">Select your team</p>
            <h1 className="text-4xl font-bold mb-4">Choose your workers</h1>
            <p className="text-lg text-muted-foreground max-w-2xl">
              Rank at least 3 workers in order of preference. We&apos;ll invite them starting with your top choice.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            
            {/* Available candidates */}
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
                          <h3 className="text-base font-semibold mb-1">{candidate.full_name}</h3>
                          <p className="text-sm text-muted-foreground mb-3">{candidate.headline}</p>

                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                            <div>
                              <p className="text-xs text-muted-foreground">Tasks completed</p>
                              <p className="text-sm font-medium">{candidate.tasks_completed}</p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">On-time rate</p>
                              <p className="text-sm font-medium">{candidate.on_time_pct}%</p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">Level</p>
                              <p className="text-sm font-medium capitalize">{candidate.seller_level}</p>
                            </div>
                            <div>
                              <p className="text-xs text-muted-foreground">Availability</p>
                              <p className="text-sm font-medium capitalize">{candidate.availability}</p>
                            </div>
                          </div>

                          <p className="text-sm text-muted-foreground italic border-l-2 border-primary pl-3">
                            &quot;{candidate.rationale}&quot;
                          </p>
                        </div>
                        <button
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
                    <p className="text-sm text-muted-foreground">All candidates added to your ranking</p>
                  </div>
                )}
              </div>
            </div>

            {/* Ranking */}
            <div className="lg:col-span-1">
              <div className="sticky top-24 border-2 border-border p-6 bg-card">
                <h2 className="text-base font-semibold mb-4">Your ranking</h2>
                
                {ranked.length > 0 ? (
                  <div className="space-y-3 mb-6">
                    {ranked.map((workerId, index) => {
                      const candidate = candidates.find((c) => c.worker_id === workerId);
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
                            <p className="text-xs font-medium truncate">{candidate.full_name}</p>
                          </div>
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleMoveUp(index)}
                              disabled={index === 0}
                              className="px-2 py-1 text-xs border border-border hover:bg-muted disabled:opacity-30 transition-opacity"
                              title="Move up"
                            >
                              ↑
                            </button>
                            <button
                              onClick={() => handleMoveDown(index)}
                              disabled={index === ranked.length - 1}
                              className="px-2 py-1 text-xs border border-border hover:bg-muted disabled:opacity-30 transition-opacity"
                              title="Move down"
                            >
                              ↓
                            </button>
                            <button
                              onClick={() => handleRemoveCandidate(workerId)}
                              className="px-2 py-1 text-xs border border-border text-red-600 hover:bg-red-50 transition-colors"
                              title="Remove"
                            >
                              ✕
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="text-center py-6 mb-6">
                    <p className="text-xs text-muted-foreground">No workers selected yet</p>
                  </div>
                )}

                <button
                  onClick={handleSubmit}
                  disabled={ranked.length < 3 || setPreferences.isPending}
                  className="w-full h-10 bg-primary text-primary-foreground text-xs font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
                >
                  {setPreferences.isPending
                    ? "Saving..."
                    : ranked.length < 3
                    ? `Select ${3 - ranked.length} more`
                    : "Confirm ranking"}
                </button>

                <p className="text-xs text-muted-foreground text-center mt-3">
                  {ranked.length}/3+ selected
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
