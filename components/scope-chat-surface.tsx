"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import JobDescriptionPanel from "@/components/job-description-panel";
import {
  useFinalizeChatSession,
  useSendChatMessage,
  useStartScopeSession,
} from "@/lib/hooks";
import type { ChatSession } from "@/lib/types";

export default function ScopeChatSurface() {
  const router = useRouter();
  const [session, setSession] = useState<ChatSession | null>(null);
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const startSession = useStartScopeSession();
  const sendMessage = useSendChatMessage(session?.id ?? "");
  const finalize = useFinalizeChatSession();

  useEffect(() => {
    startSession.mutate(undefined, {
      onSuccess: (s) => {
        // Redirect to resumable scope page instead of rendering inline
        router.push(`/scope/${s.id}`);
      },
      onError: () => setError("Could not start scope chat. Please refresh."),
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [session?.messages.length]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!session || !input.trim() || sendMessage.isPending) return;
    setError(null);
    const text = input.trim();
    setInput("");
    try {
      const updated = await sendMessage.mutateAsync(text);
      setSession(updated);
    } catch {
      setError("Message failed. Please try again.");
    }
  };

  const handleQuote = async () => {
    if (!session?.ready_for_quote) return;
    setError(null);
    try {
      const result = await finalize.mutateAsync(session.id);
      sessionStorage.setItem("intent_id", result.intent_id);
      router.push(`/proposal/${result.quote_id}`);
    } catch {
      setError("Complete the job description before requesting a quote.");
    }
  };

  if (!session && startSession.isPending) {
    return (
      <div className="flex items-center justify-center min-h-[24rem] text-sm text-muted-foreground">
        Opening scope chat…
      </div>
    );
  }

  if (!session) {
    return (
      <div className="text-sm text-destructive">{error ?? "Failed to load chat."}</div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-10">
      {/* Conversation */}
      <div className="flex flex-col border border-border bg-background min-h-[32rem]">
        <div className="px-5 py-4 border-b border-border">
          <p className="text-xs font-mono tracking-widest uppercase text-primary">Spec Compiler</p>
          <p className="text-xs text-muted-foreground mt-1">Describe your outcome — we ask only what&apos;s missing</p>
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
          {session.messages.map((msg) => (
            <div
              key={msg.id}
              className={msg.role === "user" ? "flex justify-end" : "flex justify-start"}
            >
              <div
                className={
                  msg.role === "user"
                    ? "max-w-[90%] bg-primary text-primary-foreground px-4 py-3 text-sm leading-relaxed"
                    : "max-w-[90%] border border-border bg-muted/30 px-4 py-3 text-sm leading-relaxed"
                }
              >
                {msg.body}
              </div>
            </div>
          ))}
          {(sendMessage.isPending || startSession.isPending) && (
            <p className="text-xs text-muted-foreground font-mono">Extracting into job description…</p>
          )}
          <div ref={bottomRef} />
        </div>

        <form onSubmit={handleSend} className="p-4 border-t border-border flex flex-col gap-3">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={3}
            placeholder="e.g. HealthTrack helps people manage chronic conditions — I need brand + landing page, trustworthy and modern."
            className="w-full border border-border bg-background px-4 py-3 text-sm resize-none focus:outline-none focus:border-primary"
            disabled={sendMessage.isPending}
          />
          <div className="flex flex-wrap items-center gap-3">
            <button
              type="submit"
              disabled={!input.trim() || sendMessage.isPending}
              className="h-10 px-6 bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50"
            >
              Send
            </button>
            <button
              type="button"
              onClick={handleQuote}
              disabled={!session.ready_for_quote || finalize.isPending}
              className="h-10 px-6 border border-primary text-primary text-sm font-semibold disabled:opacity-40 disabled:border-border disabled:text-muted-foreground"
            >
              {finalize.isPending ? "Preparing quote…" : "Get my quote →"}
            </button>
          </div>
          {error ? <p className="text-xs text-destructive">{error}</p> : null}
        </form>
      </div>

      {/* Job description — same JSON, human render */}
      <JobDescriptionPanel
        draft={session.spec_draft}
        completenessPct={session.completeness_pct}
        missingFields={session.missing_fields}
        readyForQuote={session.ready_for_quote}
      />
    </div>
  );
}
