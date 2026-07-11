"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import Header from "@/components/header";
import Footer from "@/components/footer";
import JobDescriptionPanel from "@/components/job-description-panel";
import {
  useFinalizeChatSession,
  useSendChatMessage,
  useChatSession,
} from "@/lib/hooks";
import type { ChatSession } from "@/lib/types";

export default function ScopePage({ params }: { params: { sessionId: string } }) {
  const router = useRouter();
  const [input, setInput] = useState("");
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: session, isLoading, isError } = useChatSession(params.sessionId);
  const sendMessage = useSendChatMessage(session?.id ?? "");
  const finalize = useFinalizeChatSession();

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
      // Session state updated via query invalidation
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

  // Loading state: "Resuming your scope chat…"
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 border-b border-border flex items-center justify-center">
          <div className="max-w-7xl mx-auto px-6 lg:px-8 py-16 lg:py-20 w-full">
            <div className="flex items-center justify-center min-h-[32rem] text-sm text-muted-foreground">
              Resuming your scope chat…
            </div>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  // Error state
  if (isError || !session) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 border-b border-border">
          <div className="max-w-7xl mx-auto px-6 lg:px-8 py-16 lg:py-20">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-6">Error</p>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight leading-none text-balance mb-4">
              Could not resume your scope.
            </h1>
            <p className="text-sm text-muted-foreground leading-relaxed mb-6">
              This scope session may have expired. Start a new one to continue.
            </p>
            <Link
              href="/start"
              className="inline-flex items-center justify-center h-10 px-6 bg-primary text-primary-foreground text-sm font-semibold hover:opacity-90 transition-opacity"
            >
              Start new scope →
            </Link>
          </div>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-7xl mx-auto px-6 lg:px-8 py-16 lg:py-20">
          <p className="text-xs font-mono tracking-widest uppercase text-primary mb-6">Spec Compiler</p>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight leading-none text-balance mb-4">
            Scope your outcome.
          </h1>
          <p className="text-sm text-muted-foreground leading-relaxed mb-10 max-w-2xl">
            Continue refining your job description. We ask only what&apos;s still missing before we quote.
          </p>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-10">
            {/* Conversation */}
            <div className="flex flex-col border border-border bg-background min-h-[32rem]">
              <div className="px-5 py-4 border-b border-border">
                <p className="text-xs font-mono tracking-widest uppercase text-primary">Spec Compiler</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {session.ready_for_quote ? "Ready for quote" : "Extracting into job description…"}
                </p>
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
                {(sendMessage.isPending) && (
                  <p className="text-xs text-muted-foreground font-mono">AI is extracting…</p>
                )}
                <div ref={bottomRef} />
              </div>

              <form onSubmit={handleSend} className="p-4 border-t border-border flex flex-col gap-3">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  rows={3}
                  placeholder="Continue describing your outcome or ask a question…"
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

            {/* Job description panel */}
            <JobDescriptionPanel
              draft={session.spec_draft}
              completenessPct={session.completeness_pct}
              missingFields={session.missing_fields}
              readyForQuote={session.ready_for_quote}
            />
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}
