"use client";

import type { OutcomeSpecDraft } from "@/lib/types";

interface JobDescriptionPanelProps {
  draft: OutcomeSpecDraft;
  completenessPct: number;
  missingFields: string[];
  readyForQuote: boolean;
}

const MISSING_LABELS: Record<string, string> = {
  outcome_statement: "Clear outcome statement",
  deliverables: "Deliverables list",
  acceptance_criteria: "Done-when criteria",
  in_scope: "In-scope items",
  out_of_scope: "Out-of-scope boundaries",
  company_context: "Company / product context",
  client_inputs: "Materials from you",
  workflow_summary: "Workflow steps",
};

export default function JobDescriptionPanel({
  draft,
  completenessPct,
  missingFields,
  readyForQuote,
}: JobDescriptionPanelProps) {
  const empty = !draft.outcome_statement && draft.deliverables.length === 0;

  return (
    <div className="border border-border bg-card flex flex-col h-full min-h-[32rem]">
      <div className="px-5 py-4 border-b border-border flex items-center justify-between gap-4">
        <div>
          <p className="text-xs font-mono tracking-widest uppercase text-primary">Job description</p>
          <p className="text-xs text-muted-foreground mt-1">Built from your conversation — this is what we will deliver</p>
        </div>
        <div className="text-right shrink-0">
          <p className="text-sm font-semibold tabular-nums">{completenessPct}%</p>
          <p className="text-xs text-muted-foreground">complete</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-5 py-6 space-y-8">
        {empty ? (
          <p className="text-sm text-muted-foreground leading-relaxed">
            Start describing your outcome in the chat. As we extract details, your job description will appear here —
            deliverables, how we verify done, scope, and workflow.
          </p>
        ) : (
          <>
            {draft.outcome_statement ? (
              <section>
                <h3 className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">
                  What we&apos;re building
                </h3>
                <p className="text-sm leading-relaxed">{draft.outcome_statement}</p>
              </section>
            ) : null}

            {draft.workflow_summary ? (
              <section>
                <h3 className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">Workflow</h3>
                <p className="text-sm leading-relaxed">{draft.workflow_summary}</p>
              </section>
            ) : null}

            {draft.deliverables.length > 0 ? (
              <section>
                <h3 className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">Deliverables</h3>
                <ul className="space-y-2">
                  {draft.deliverables.map((d) => (
                    <li key={d.name} className="text-sm flex justify-between gap-2 border-b border-border pb-2">
                      <span>{d.name}</span>
                      <span className="text-muted-foreground shrink-0">{d.format}</span>
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {draft.acceptance_criteria.length > 0 ? (
              <section>
                <h3 className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">
                  How we verify done
                </h3>
                <ul className="space-y-2">
                  {draft.acceptance_criteria.map((c) => (
                    <li key={c.criterion} className="text-sm leading-relaxed">
                      <span className="inline-block text-[10px] font-mono uppercase tracking-wide bg-muted px-1.5 py-0.5 mr-2">
                        {c.check_type.replace("_", " ")}
                      </span>
                      {c.criterion}
                    </li>
                  ))}
                </ul>
              </section>
            ) : null}

            {draft.in_scope.length > 0 ? (
              <section>
                <h3 className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">In scope</h3>
                <ul className="text-sm list-disc pl-5 space-y-1">
                  {draft.in_scope.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>
            ) : null}

            {draft.out_of_scope.length > 0 ? (
              <section>
                <h3 className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">Out of scope</h3>
                <ul className="text-sm list-disc pl-5 space-y-1 text-muted-foreground">
                  {draft.out_of_scope.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </section>
            ) : null}

            {draft.client_inputs_required.length > 0 ? (
              <section>
                <h3 className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">We need from you</h3>
                <ul className="text-sm list-disc pl-5 space-y-1">
                  {draft.client_inputs_required.map((item) => (
                    <li key={item}>{item.replace(/_/g, " ")}</li>
                  ))}
                </ul>
              </section>
            ) : null}
          </>
        )}

        {missingFields.length > 0 && !readyForQuote ? (
          <section className="border border-dashed border-border p-4 bg-muted/20">
            <h3 className="text-xs font-mono tracking-widest uppercase text-muted-foreground mb-2">Still needed</h3>
            <ul className="text-sm space-y-1 text-muted-foreground">
              {missingFields.map((f) => (
                <li key={f}>· {MISSING_LABELS[f] ?? f.replace(/_/g, " ")}</li>
              ))}
            </ul>
          </section>
        ) : null}
      </div>

      {readyForQuote ? (
        <div className="px-5 py-3 border-t border-border bg-primary/5">
          <p className="text-xs text-primary font-medium">Ready to quote — review and continue below.</p>
        </div>
      ) : null}
    </div>
  );
}
