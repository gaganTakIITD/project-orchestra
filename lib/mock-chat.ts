/**
 * Mock scope-chat sessions — simulates schema-driven Q&A until backend is live.
 */
import type { ChatMessage, ChatSession, OutcomeSpecDraft } from "./types";

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
    messages: [...session.messages, userMsg, assistantMsg],
  };
  mockSessions.set(sessionId, updated);
  return updated;
}

export function mockFinalizeScopeSession(sessionId: string): {
  intent_id: string;
  quote_id: string;
} {
  const session = mockSessions.get(sessionId);
  if (!session?.ready_for_quote) {
    throw new Error("Job description not complete enough to quote");
  }
  mockSessions.set(sessionId, { ...session, status: "completed" });
  return { intent_id: "int_healthtrack", quote_id: "quote_healthtrack" };
}
