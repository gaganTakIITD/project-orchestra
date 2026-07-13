"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  useCandidates,
  useFinalizeMatcherSession,
  useSendChatMessage,
  useSetPreferences,
  useStartMatcherSession,
} from "@/lib/hooks";
import type { ChatSession } from "@/lib/types";
import Header from "@/components/header";
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
    isPending,
    isError,
  } = useCandidates(orderId, taskId);
  const setPreferences = useSetPreferences(orderId, taskId);
  const startMatcher = useStartMatcherSession();
  const finalizeMatcher = useFinalizeMatcherSession();

  const [ranked, setRanked] = useState<string[]>([]);
  const [matcherSession, setMatcherSession] = useState<ChatSession | null>(null);
  const [chatInput, setChatInput] = useState("");
  const [chatError, setChatError] = useState<string | null>(null);
  const chatBottomRef = useRef<HTMLDivElement>(null);

  const sendMessage = useSendChatMessage(matcherSession?.id ?? "");

  // Start Matcher Preference Chat once candidates are available
  useEffect(() => {
    if (!orderId || !taskId || !candidates?.length || matcherSession || startMatcher.isPending) {
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const session = await startMatcher.mutateAsync({ orderId, taskId });
        if (cancelled) return;
        setMatcherSession(session);
        if (session.candidates?.length) {
          setRanked(session.candidates.map((c) => c.worker_id));
        }
      } catch {
        if (!cancelled) setChatError("Matcher chat unavailable — you can still rank manually.");
      }
    })();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- start once when candidates load
  }, [orderId, taskId, candidates?.length]);

  // Sync ranking panel when chat reorders candidates
  useEffect(() => {
    const list = matcherSession?.candidates;
    if (list?.length) {
      setRanked(list.map((c) => c.worker_id));
    }
  }, [matcherSession?.candidates, matcherSession?.spec_version]);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [matcherSession?.messages.length, sendMessage.streamingText]);

  const displayCandidates = matcherSession?.candidates?.length
    ? matcherSession.candidates
    : candidates ?? [];

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

  /** Existing REST path — kept as fallback when Matcher chat is unavailable. */
  const handleSubmitRest = async () => {
    if (ranked.length < 3) {
      alert("Please select at least 3 workers");
      return;
    }
    try {
      await setPreferences.mutateAsync(ranked);
      router.push(`/orders/${orderId}`);
    } catch (error) {
      alert("Failed to save preferences. Please try again.");
      console.error("[v0] Preference save failed:", error);
    }
  };

  /** Chat finalize → PreferenceSet; falls back to REST preferences API. */
  const handleConfirmViaChat = async () => {
    if (ranked.length < 3) {
      alert("Please select at least 3 workers");
      return;
    }
    if (matcherSession) {
      try {
        await finalizeMatcher.mutateAsync({
          sessionId: matcherSession.id,
          ranked_worker_ids: ranked,
        });
        router.push(`/orders/${orderId}`);
        return;
      } catch {
        // fall through to REST
      }
    }
    await handleSubmitRest();
  };

  const handleChatSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!matcherSession || !chatInput.trim() || sendMessage.isPending) return;
    setChatError(null);
    const text = chatInput.trim();
    setChatInput("");
    try {
      const updated = await sendMessage.mutateAsync(text);
      setMatcherSession(updated);
    } catch {
      setChatError("Message failed. Please try again.");
    }
  };

  if (!orderId || !taskId || isPending) {
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

  if (isError) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <div className="text-center space-y-4">
            <p className="text-muted-foreground">Could not load candidates for this task.</p>
            <Link
              href={`/orders/${orderId}`}
              className="inline-flex h-10 px-6 bg-primary text-primary-foreground text-sm font-semibold items-center"
            >
              Back to tracker →
            </Link>
          </div>
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
          <div className="text-center space-y-4">
            <p className="text-muted-foreground">No candidates available for this task yet.</p>
            <Link
              href={`/orders/${orderId}`}
              className="inline-flex h-10 px-6 bg-primary text-primary-foreground text-sm font-semibold items-center"
            >
              Back to tracker →
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  const unranked = displayCandidates.filter((c) => !ranked.includes(c.worker_id));
  const confirming = setPreferences.isPending || finalizeMatcher.isPending;

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          <div className="mb-16">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-4">Select your team</p>
            <h1 className="text-4xl font-bold mb-4">Choose your workers</h1>
            <p className="text-lg text-muted-foreground max-w-2xl">
              Talk with the Matcher agent or rank at least 3 workers manually. We&apos;ll invite them starting with your top choice.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
            <div className="lg:col-span-2 space-y-10">
              <div className="flex flex-col border border-border bg-background min-h-[20rem]">
                <div className="px-5 py-4 border-b border-border flex items-center justify-between gap-4">
                  <div>
                    <p className="text-xs font-mono tracking-widest uppercase text-primary">Matcher</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      Ask why someone ranks #1, reorder with chat, or confirm the shortlist.
                    </p>
                  </div>
                  {matcherSession?.ready_to_confirm ? (
                    <span className="text-xs font-mono text-primary whitespace-nowrap">Ready to confirm</span>
                  ) : null}
                </div>
                <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4 max-h-[22rem]">
                  {!matcherSession && startMatcher.isPending ? (
                    <p className="text-sm text-muted-foreground">Starting Matcher chat…</p>
                  ) : null}
                  {(matcherSession?.messages ?? []).map((m) => (
                    <div
                      key={m.id}
                      className={
                        m.role === "user"
                          ? "ml-8 text-sm leading-relaxed"
                          : "mr-4 text-sm leading-relaxed text-muted-foreground"
                      }
                    >
                      <p className="text-[10px] font-mono uppercase tracking-wider mb-1 text-primary">
                        {m.role === "user" ? "You" : "Matcher"}
                      </p>
                      <p className="whitespace-pre-wrap">{m.body}</p>
                    </div>
                  ))}
                  {sendMessage.streamingText ? (
                    <div className="mr-4 text-sm leading-relaxed text-muted-foreground">
                      <p className="text-[10px] font-mono uppercase tracking-wider mb-1 text-primary">Matcher</p>
                      <p className="whitespace-pre-wrap">{sendMessage.streamingText}</p>
                    </div>
                  ) : null}
                  <div ref={chatBottomRef} />
                </div>
                <form onSubmit={handleChatSend} className="border-t border-border p-4 flex gap-2">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    disabled={!matcherSession || sendMessage.isPending}
                    placeholder={
                      matcherSession
                        ? 'e.g. "Why is Rohan #1?" or "Move Meera to #1"'
                        : "Matcher chat unavailable"
                    }
                    className="flex-1 h-10 px-3 border border-border bg-background text-sm focus:outline-none focus:ring-1 focus:ring-primary disabled:opacity-50"
                  />
                  <button
                    type="submit"
                    disabled={!matcherSession || !chatInput.trim() || sendMessage.isPending}
                    className="h-10 px-4 bg-primary text-primary-foreground text-xs font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
                  >
                    Send
                  </button>
                </form>
                {chatError ? (
                  <p className="px-5 pb-3 text-xs text-red-600">{chatError}</p>
                ) : null}
              </div>

              <div>
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
                      <p className="text-sm text-muted-foreground">All candidates added to your ranking</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="lg:col-span-1">
              <div className="sticky top-24 border-2 border-border p-6 bg-card">
                <h2 className="text-base font-semibold mb-4">Your ranking</h2>

                {ranked.length > 0 ? (
                  <div className="space-y-3 mb-6">
                    {ranked.map((workerId, index) => {
                      const candidate = displayCandidates.find((c) => c.worker_id === workerId);
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
                              type="button"
                              onClick={() => handleMoveUp(index)}
                              disabled={index === 0}
                              className="px-2 py-1 text-xs border border-border hover:bg-muted disabled:opacity-30 transition-opacity"
                              title="Move up"
                            >
                              ↑
                            </button>
                            <button
                              type="button"
                              onClick={() => handleMoveDown(index)}
                              disabled={index === ranked.length - 1}
                              className="px-2 py-1 text-xs border border-border hover:bg-muted disabled:opacity-30 transition-opacity"
                              title="Move down"
                            >
                              ↓
                            </button>
                            <button
                              type="button"
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
                  type="button"
                  onClick={handleConfirmViaChat}
                  disabled={ranked.length < 3 || confirming}
                  className="w-full h-10 bg-primary text-primary-foreground text-xs font-semibold hover:opacity-90 disabled:opacity-50 transition-opacity"
                >
                  {confirming
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
