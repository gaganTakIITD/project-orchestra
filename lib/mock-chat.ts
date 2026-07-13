/**
 * Mock chat sessions — Scope (Stage 1) + Pricing (Stage 2) + Matcher (Stage 3).
 */
import { mockCandidates, mockClient, mockQuote, mockSpec } from "./mock-data";
import type {
  ChatMessage,
  ChatSession,
  ChatStreamHandlers,
  FinalizeMatcherSessionResult,
  FinalizePricingSessionResult,
  OutcomeSpec,
  OutcomeSpecDraft,
  Quote,
} from "./types";

const emptyDraft = (): OutcomeSpecDraft => ({
  outcome_statement: "",
  deliverables: [],
  acceptance_criteria: [],
  in_scope: [],
  out_of_scope: [],
  assumptions: [],
  client_inputs_required: [],
  mapped_task_types: [],
  risk_tier: "L1",
  workflow_summary: "",
  version: 0,
});

type ScopeSnapshot = {
  spec_draft: OutcomeSpecDraft;
  completeness_pct: number;
  missing_fields: string[];
  ready_for_quote: boolean;
};

const mockSnapshots = new Map<string, Record<string, ScopeSnapshot>>();

function computeMockCompleteness(draft: OutcomeSpecDraft, userText: string): {
  pct: number;
  missing: string[];
  ready: boolean;
} {
  const missing: string[] = [];
  const t = userText.toLowerCase();

  if (!draft.outcome_statement || draft.outcome_statement.length < 20) {
    missing.push("outcome_statement");
  }
  if (draft.deliverables.length === 0) missing.push("deliverables");
  if (draft.acceptance_criteria.length === 0) missing.push("acceptance_criteria");
  if (draft.in_scope.length === 0) missing.push("in_scope");
  if (draft.out_of_scope.length === 0) missing.push("out_of_scope");
  if (!t.match(/health|fintech|startup|company|product/) && draft.client_inputs_required.length === 0) {
    missing.push("company_context");
  }
  if (!t.match(/tagline|reference|logo file|brand asset/) && !draft.client_inputs_required.includes("tagline")) {
    missing.push("client_inputs");
  }

  const total = 8;
  const filled = total - missing.length;
  const pct = Math.round((filled / total) * 100);
  return { pct, missing, ready: missing.length === 0 && pct >= 85 };
}

function extractMockDraft(prev: OutcomeSpecDraft, userText: string): OutcomeSpecDraft {
  const t = userText.toLowerCase();
  const next = { ...prev, version: prev.version + 1 };

  if (userText.trim().length > 10) {
    next.outcome_statement = userText.trim().slice(0, 500);
  }

  if (t.includes("brand") || t.includes("landing") || t.includes("health")) {
    next.deliverables = [
      { name: "Logo", format: "SVG + PNG", required: true },
      { name: "Brand guide", format: "PDF", required: true },
      { name: "Figma UI", format: "Figma link", required: true },
      { name: "Live landing page", format: "URL", required: true },
    ];
    next.acceptance_criteria = [
      {
        criterion: "Logo delivered in SVG and PNG",
        check_type: "deterministic",
        rule: "files_include_format(['svg','png'])",
      },
      {
        criterion: "Landing page loads under 3s on mobile",
        check_type: "deterministic",
        rule: "lighthouse_performance >= 70",
      },
      {
        criterion: "Visual design matches requested tone",
        check_type: "ai_judged",
        rubric: "Professional, trustworthy, accessible contrast.",
      },
    ];
    next.in_scope = ["Brand identity", "1 landing page", "2 revision rounds"];
    next.out_of_scope = ["CMS", "SEO", "Content writing", "Mobile app"];
    next.assumptions = ["Client provides company name and tagline"];
    next.mapped_task_types = [
      "brand_identity",
      "logo_design",
      "figma_ui_design",
      "landing_page_frontend",
      "deployment_devops",
    ];
    next.workflow_summary =
      "Brand direction → Logo design → UI design in Figma → Build landing page → Deploy to live URL";
  }

  if (t.includes("healthtrack") || t.includes("health track")) {
    next.outcome_statement =
      "Launch-ready brand identity and responsive landing page for HealthTrack — chronic condition tracking with a trustworthy, modern healthcare tone.";
    next.client_inputs_required = ["company_name", "tagline", "reference_sites"];
  }

  if (t.includes("tagline") || t.includes("reference")) {
    if (!next.client_inputs_required.includes("tagline")) {
      next.client_inputs_required = ["company_name", "tagline", "reference_sites"];
    }
  }

  return next;
}

const QUESTIONS: Record<string, string> = {
  outcome_statement:
    "What outcome do you need delivered? Describe the result — e.g. brand + landing page, not individual tasks.",
  deliverables:
    "What should we deliver? For example: logo files, brand guide, Figma designs, live website URL.",
  acceptance_criteria: "How will we know it's done? Any quality bar — mobile speed, formats, tone?",
  in_scope: "What's included in this engagement?",
  out_of_scope: "What should we explicitly exclude?",
  company_context: "What's your company or product name, and what problem does it solve?",
  client_inputs: "What can you provide — tagline, reference sites, existing logo or brand assets?",
};

function nextQuestion(missing: string[]): string {
  const key = missing[0];
  return (
    QUESTIONS[key] ??
    "Tell me a bit more so I can complete your job description before we quote."
  );
}

let mockSessionCounter = 0;

export function createMockScopeSession(): ChatSession {
  mockSessionCounter += 1;
  const id = `chat_mock_${mockSessionCounter}`;
  const opening: ChatMessage = {
    id: `${id}_m0`,
    session_id: id,
    role: "assistant",
    body: "What outcome do you need delivered? Describe the result you want — for example a brand and landing page for your startup.",
    spec_version_after: 0,
    created_at: new Date().toISOString(),
  };
  return {
    id,
    agent_type: "spec_compiler",
    status: "active",
    spec_draft: emptyDraft(),
    spec_version: 0,
    completeness_pct: 0,
    missing_fields: ["outcome_statement"],
    ready_for_quote: false,
    messages: [opening],
    created_at: new Date().toISOString(),
  };
}

const mockSessions = new Map<string, ChatSession>();

export function getOrCreateMockSession(sessionId?: string): ChatSession {
  if (sessionId && mockSessions.has(sessionId)) {
    return mockSessions.get(sessionId)!;
  }
  const s = createMockScopeSession();
  mockSessions.set(s.id, s);
  return s;
}

export function mockSendScopeMessage(
  sessionId: string,
  body: string
): ChatSession {
  const session = mockSessions.get(sessionId) ?? getOrCreateMockSession(sessionId);
  if (session.agent_type === "pricing") {
    return mockPricingReply(session, body);
  }
  if (session.agent_type === "matcher") {
    return mockMatcherReply(session, body);
  }

  const snaps = mockSnapshots.get(sessionId) ?? {};
  snaps[String(session.spec_version)] = {
    spec_draft: { ...session.spec_draft },
    completeness_pct: session.completeness_pct,
    missing_fields: [...session.missing_fields],
    ready_for_quote: session.ready_for_quote,
  };
  mockSnapshots.set(sessionId, snaps);

  const userMsg: ChatMessage = {
    id: `${sessionId}_u_${Date.now()}`,
    session_id: sessionId,
    role: "user",
    body,
    created_at: new Date().toISOString(),
  };

  const draft = extractMockDraft(session.spec_draft, body);
  const { pct, missing, ready } = computeMockCompleteness(draft, body);

  let assistantBody: string;
  if ((body.trim().length < 8 || /create my startup/i.test(body)) && !/brand|landing|health/i.test(body)) {
    assistantBody =
      "I can help with that — but I need more detail before we can build. Are you looking for brand identity, a landing page, or a full launch package? What does your startup do?";
  } else if (!ready) {
    assistantBody = `Thanks — I'm updating your job description (${pct}% complete). ${nextQuestion(missing)}`;
  } else {
    assistantBody =
      "Your job description looks complete enough to quote. Review the panel on the right — when you're happy, click **Get my quote**.";
  }

  const assistantMsg: ChatMessage = {
    id: `${sessionId}_a_${Date.now()}`,
    session_id: sessionId,
    role: "assistant",
    body: assistantBody,
    spec_version_after: draft.version,
    created_at: new Date().toISOString(),
  };

  const updated: ChatSession = {
    ...session,
    spec_draft: draft,
    spec_version: draft.version,
    completeness_pct: pct,
    missing_fields: missing,
    ready_for_quote: ready,
    can_undo: true,
    messages: [...session.messages, userMsg, assistantMsg],
  };
  mockSessions.set(sessionId, updated);
  return updated;
}

function chunkText(text: string, maxChars = 24): string[] {
  const parts = text.split(/(\s+)/);
  const chunks: string[] = [];
  let buf = "";
  for (const part of parts) {
    if (buf.length + part.length > maxChars && buf) {
      chunks.push(buf);
      buf = part;
    } else {
      buf += part;
    }
  }
  if (buf) chunks.push(buf);
  return chunks;
}

/** Mock SSE — routes matcher/pricing sessions to their turn logic. */
export async function mockSendScopeMessageStream(
  sessionId: string,
  body: string,
  handlers: ChatStreamHandlers
): Promise<ChatSession> {
  const existing = mockSessions.get(sessionId);
  if (existing?.agent_type === "matcher") {
    return mockSendMatcherMessageStream(sessionId, body, handlers);
  }
  if (existing?.agent_type === "pricing") {
    return mockSendPricingMessageStream(sessionId, body, handlers);
  }

  const session = existing ?? getOrCreateMockSession(sessionId);

  const snaps = mockSnapshots.get(sessionId) ?? {};
  snaps[String(session.spec_version)] = {
    spec_draft: { ...session.spec_draft },
    completeness_pct: session.completeness_pct,
    missing_fields: [...session.missing_fields],
    ready_for_quote: session.ready_for_quote,
  };
  mockSnapshots.set(sessionId, snaps);

  const userMsg: ChatMessage = {
    id: `${sessionId}_u_${Date.now()}`,
    session_id: sessionId,
    role: "user",
    body,
    created_at: new Date().toISOString(),
  };

  const draft = extractMockDraft(session.spec_draft, body);
  const { pct, missing, ready } = computeMockCompleteness(draft, body);

  let assistantBody: string;
  if ((body.trim().length < 8 || /create my startup/i.test(body)) && !/brand|landing|health/i.test(body)) {
    assistantBody =
      "I can help with that — but I need more detail before we can build. Are you looking for brand identity, a landing page, or a full launch package? What does your startup do?";
  } else if (!ready) {
    assistantBody = `Thanks — I'm updating your job description (${pct}% complete). ${nextQuestion(missing)}`;
  } else {
    assistantBody =
      "Your job description looks complete enough to quote. Review the panel on the right — when you're happy, click **Get my quote**.";
  }

  await new Promise((r) => setTimeout(r, 120));
  handlers.onDraftPatch?.({
    type: "draft_patch",
    spec_draft: draft,
    spec_version: draft.version,
    completeness_pct: pct,
    missing_fields: missing,
    ready_for_quote: ready,
  });

  for (const chunk of chunkText(assistantBody)) {
    handlers.onToken?.(chunk);
    await new Promise((r) => setTimeout(r, 35));
  }

  const assistantMsg: ChatMessage = {
    id: `${sessionId}_a_${Date.now()}`,
    session_id: sessionId,
    role: "assistant",
    body: assistantBody,
    spec_version_after: draft.version,
    created_at: new Date().toISOString(),
  };

  const updated: ChatSession = {
    ...session,
    spec_draft: draft,
    spec_version: draft.version,
    completeness_pct: pct,
    missing_fields: missing,
    ready_for_quote: ready,
    can_undo: true,
    messages: [...session.messages, userMsg, assistantMsg],
  };
  mockSessions.set(sessionId, updated);
  handlers.onTurnComplete?.(updated);
  return updated;
}

/** Session-scoped specs/quotes from finalize — looked up by getMockSpec / getMockQuote. */
const mockMaterializedSpecs = new Map<string, OutcomeSpec>();
const mockMaterializedQuotes = new Map<string, Quote>();

export function getMockSpec(specId: string): OutcomeSpec {
  return mockMaterializedSpecs.get(specId) ?? mockSpec;
}

export function getMockQuote(quoteId: string): Quote {
  return mockMaterializedQuotes.get(quoteId) ?? mockQuote;
}

export function mockFinalizeScopeSession(sessionId: string): {
  intent_id: string;
  quote_id: string;
} {
  const session = mockSessions.get(sessionId);
  if (!session?.ready_for_quote) {
    throw new Error("Job description not complete enough to quote");
  }
  const draft = session.spec_draft;
  const intent_id = `int_${sessionId}`;
  const spec_id = `spec_${sessionId}`;
  const quote_id = `quote_${sessionId}`;
  const now = new Date().toISOString();

  const spec: OutcomeSpec = {
    id: spec_id,
    intent_id,
    sku_id: draft.sku_id ?? "sku_launch_studio",
    outcome_statement: draft.outcome_statement,
    deliverables: draft.deliverables,
    acceptance_criteria: draft.acceptance_criteria,
    in_scope: draft.in_scope,
    out_of_scope: draft.out_of_scope,
    assumptions: draft.assumptions,
    client_inputs_required: draft.client_inputs_required,
    mapped_task_types: draft.mapped_task_types,
    risk_tier: draft.risk_tier,
    workflow_summary: draft.workflow_summary ?? "",
    version: draft.version || 1,
    frozen_at: now,
  };

  const quote: Quote = {
    id: quote_id,
    spec_id,
    client_id: mockClient.id,
    price: mockQuote.price,
    deadline: mockQuote.deadline,
    revision_limit: mockQuote.revision_limit,
    status: "issued",
    valid_until: mockQuote.valid_until,
    ai_confidence: mockQuote.ai_confidence,
    ai_rationale: mockQuote.ai_rationale,
    created_at: now,
  };

  mockMaterializedSpecs.set(spec_id, spec);
  mockMaterializedQuotes.set(quote_id, quote);
  mockSessions.set(sessionId, { ...session, status: "completed" });
  return { intent_id, quote_id };
}

// --- Matcher Preference Chat (Stage 3) ---------------------------------------

export function mockStartMatcherSession(orderId: string, taskId: string): ChatSession {
  const id = `chat_matcher_${Date.now()}`;
  const candidates = mockCandidates.map((c) => ({ ...c }));
  const opening: ChatMessage = {
    id: `msg_${id}_0`,
    session_id: id,
    role: "assistant",
    body:
      `I found ${candidates.length} strong matches. Top pick: ${candidates[0]?.full_name}. ` +
      `Ask why someone ranks where they do, or say "confirm these three."`,
    spec_version_after: 0,
    created_at: new Date().toISOString(),
  };
  const session: ChatSession = {
    id,
    agent_type: "matcher",
    status: "active",
    spec_draft: emptyDraft(),
    spec_version: 0,
    completeness_pct: 75,
    missing_fields: [],
    ready_for_quote: false,
    ref_type: "task",
    ref_id: taskId,
    order_id: orderId,
    candidates,
    ready_to_confirm: candidates.length >= 3,
    messages: [opening],
    created_at: new Date().toISOString(),
  };
  mockSessions.set(id, session);
  return session;
}

function mockMatcherReply(session: ChatSession, userText: string): ChatSession {
  const t = userText.toLowerCase();
  let candidates = [...(session.candidates ?? mockCandidates)];
  let version = session.spec_version + 1;
  let reply = `Here's the shortlist:\n${candidates
    .map((c, i) => `${i + 1}. ${c.full_name} (${c.score})`)
    .join("\n")}`;

  if (/why|explain/.test(t)) {
    const top = candidates[0];
    reply = top
      ? `${top.full_name} is #1 (score ${top.score}). ${top.rationale}`
      : "No candidates yet.";
    version = session.spec_version;
  } else if (/confirm|looks good|these three/.test(t)) {
    reply = "Ranking ready — hit Confirm ranking to submit your PreferenceSet.";
  } else if (/move .+ to #?1|make .+ first/.test(t)) {
    const meera = candidates.find((c) => /meera/i.test(c.full_name));
    if (meera && /meera/.test(t)) {
      candidates = [meera, ...candidates.filter((c) => c.worker_id !== meera.worker_id)];
      reply = `Updated — ${meera.full_name} is now #1.`;
    }
  }

  const userMsg: ChatMessage = {
    id: `msg_${session.id}_u_${Date.now()}`,
    session_id: session.id,
    role: "user",
    body: userText,
    created_at: new Date().toISOString(),
  };
  const assistantMsg: ChatMessage = {
    id: `msg_${session.id}_a_${Date.now()}`,
    session_id: session.id,
    role: "assistant",
    body: reply,
    spec_version_after: version,
    created_at: new Date().toISOString(),
  };
  const updated: ChatSession = {
    ...session,
    candidates,
    spec_version: version,
    ready_to_confirm: candidates.length >= 3,
    messages: [...session.messages, userMsg, assistantMsg],
  };
  mockSessions.set(session.id, updated);
  return updated;
}

/** Route mock stream/send by agent_type so Preference Chat works in USE_MOCKS. */
export async function mockSendMatcherMessageStream(
  sessionId: string,
  body: string,
  handlers: ChatStreamHandlers
): Promise<ChatSession> {
  const session = mockSessions.get(sessionId);
  if (!session || session.agent_type !== "matcher") {
    throw new Error("Matcher session not found");
  }
  const updated = mockMatcherReply(session, body);
  handlers.onArtifactUpdated?.({
    type: "artifact_updated",
    candidates: updated.candidates ?? [],
    version: updated.spec_version,
    ready_to_confirm: Boolean(updated.ready_to_confirm),
  });
  for (const word of (updated.messages.at(-1)?.body ?? "").split(/(\s+)/)) {
    if (word) handlers.onToken?.(word);
  }
  handlers.onTurnComplete?.(updated);
  return updated;
}

export function mockFinalizeMatcherSession(sessionId: string): FinalizeMatcherSessionResult {
  const session = mockSessions.get(sessionId);
  if (!session || session.agent_type !== "matcher") {
    throw new Error("Matcher session not found");
  }
  if ((session.candidates?.length ?? 0) < 3) {
    throw new Error("Need at least 3 ranked workers");
  }
  mockSessions.set(sessionId, { ...session, status: "completed" });
  return {
    preference_set_id: "pref_mock_1",
    order_id: session.order_id ?? "ord_mock",
    task_id: session.ref_id ?? "task_mock",
  };
}

// --- Pricing Reasoner Confirm Chat (Stage 2) ---------------------------------

export function mockStartPricingSession(quoteId: string): ChatSession {
  const id = `chat_pricing_${Date.now()}`;
  const opening: ChatMessage = {
    id: `msg_${id}_0`,
    session_id: id,
    role: "assistant",
    body:
      `Here's your quote (₹${mockQuote.price.toLocaleString("en-IN")}). ` +
      "Ask about price drivers, risk, or deadline — or say confirm when ready to accept.",
    spec_version_after: 0,
    created_at: new Date().toISOString(),
  };
  const session: ChatSession = {
    id,
    agent_type: "pricing",
    status: "active",
    spec_draft: emptyDraft(),
    spec_version: 0,
    completeness_pct: 100,
    missing_fields: [],
    ready_for_quote: false,
    ref_type: "quote",
    ref_id: quoteId,
    ready_to_confirm: true,
    can_undo: false,
    messages: [opening],
    created_at: new Date().toISOString(),
  };
  mockSessions.set(id, session);
  return session;
}

function mockPricingReply(session: ChatSession, userText: string): ChatSession {
  const t = userText.toLowerCase();
  let reply =
    `Quote summary: ₹${mockQuote.price.toLocaleString("en-IN")}. ` +
    "Ask about drivers, risk, or deadline — or say confirm to accept.";
  let version = session.spec_version;
  let ready = Boolean(session.ready_to_confirm);

  if (/confirm|accept|looks good|proceed/.test(t)) {
    reply =
      "Great — you're ready to accept. Hit Confirm & begin (or finalize this chat) to create your order.";
    version = session.spec_version + 1;
    ready = true;
  } else if (/risk|tier|confidence/.test(t)) {
    reply = `Risk for this quote is ${mockSpec.risk_tier}. L1 is standard delivery risk with included revisions.`;
  } else if (/deadline|timeline|days/.test(t)) {
    reply = `The deadline is ${mockQuote.deadline}. It's derived from the SKU typical_days band.`;
  } else if (/why|price|driver|cost|sku/.test(t)) {
    reply =
      `Price drivers: SKU base band, ${mockSpec.deliverables.length} deliverables, ` +
      `${mockQuote.revision_limit} revision rounds. ${mockQuote.ai_rationale ?? ""}`;
  }

  const userMsg: ChatMessage = {
    id: `msg_${session.id}_u_${Date.now()}`,
    session_id: session.id,
    role: "user",
    body: userText,
    created_at: new Date().toISOString(),
  };
  const assistantMsg: ChatMessage = {
    id: `msg_${session.id}_a_${Date.now()}`,
    session_id: session.id,
    role: "assistant",
    body: reply,
    spec_version_after: version,
    created_at: new Date().toISOString(),
  };
  const updated: ChatSession = {
    ...session,
    spec_version: version,
    ready_to_confirm: ready,
    messages: [...session.messages, userMsg, assistantMsg],
  };
  mockSessions.set(session.id, updated);
  return updated;
}

export async function mockSendPricingMessageStream(
  sessionId: string,
  body: string,
  handlers: ChatStreamHandlers
): Promise<ChatSession> {
  const session = mockSessions.get(sessionId);
  if (!session || session.agent_type !== "pricing") {
    throw new Error("Pricing session not found");
  }
  const updated = mockPricingReply(session, body);
  handlers.onArtifactUpdated?.({
    type: "artifact_updated",
    candidates: [],
    version: updated.spec_version,
    ready_to_confirm: Boolean(updated.ready_to_confirm),
  });
  for (const word of (updated.messages.at(-1)?.body ?? "").split(/(\s+)/)) {
    if (word) handlers.onToken?.(word);
  }
  handlers.onTurnComplete?.(updated);
  return updated;
}

export function mockFinalizePricingSession(sessionId: string): FinalizePricingSessionResult {
  const session = mockSessions.get(sessionId);
  if (!session || session.agent_type !== "pricing") {
    throw new Error("Pricing session not found");
  }
  mockSessions.set(sessionId, { ...session, status: "completed" });
  return {
    quote_id: session.ref_id ?? mockQuote.id,
    order_id: "ord_mock_pricing",
  };
}

export function mockUndoScopeSession(sessionId: string): ChatSession {
  const session = mockSessions.get(sessionId);
  if (!session || session.agent_type !== "spec_compiler") {
    throw new Error("Scope session not found");
  }
  const snaps = mockSnapshots.get(sessionId) ?? {};
  const keys = Object.keys(snaps)
    .map(Number)
    .filter((n) => !Number.isNaN(n))
    .sort((a, b) => b - a);
  const target = keys.find((k) => k < session.spec_version) ?? keys[0];
  if (target === undefined) {
    throw new Error("Nothing to undo");
  }
  const snap = snaps[String(target)];
  delete snaps[String(target)];
  mockSnapshots.set(sessionId, snaps);

  let messages = [...session.messages];
  if (
    messages.length >= 2 &&
    messages[messages.length - 1]?.role === "assistant" &&
    messages[messages.length - 2]?.role === "user"
  ) {
    messages = messages.slice(0, -2);
  }

  const updated: ChatSession = {
    ...session,
    spec_draft: snap.spec_draft,
    spec_version: target,
    completeness_pct: snap.completeness_pct,
    missing_fields: snap.missing_fields,
    ready_for_quote: snap.ready_for_quote,
    can_undo: Object.keys(snaps).length > 0,
    messages,
  };
  mockSessions.set(sessionId, updated);
  return updated;
}
