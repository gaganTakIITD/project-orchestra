'use client';

import { useAcceptDelivery, useDelivery, useOrder, usePlan } from "@/lib/hooks";
import { taskStatusClientLabel, taskStatusTone } from "@/lib/state-labels";
import Footer from "@/components/footer";
import JourneyStepper from "@/components/journey-stepper";
import { CLIENT_JOURNEY_STAGES, clientStageForOrder } from "@/components/journey";
import Link from "next/link";
import { useState } from "react";

const toneColors: Record<string, string> = {
  neutral: "bg-muted text-muted-foreground",
  info: "bg-secondary/15 text-secondary-foreground",
  active: "bg-primary/10 text-primary",
  review: "bg-amber-100 text-amber-900",
  success: "bg-primary/15 text-primary",
  danger: "bg-destructive/10 text-destructive",
};

export default function OrderTrackerPage({ params }: { params: { orderId: string } }) {
  const orderId = params.orderId;
  const [acceptError, setAcceptError] = useState<string | null>(null);

  const { data: order, isLoading: orderLoading } = useOrder(orderId);
  const { data: plan, isLoading: planLoading } = usePlan(orderId);
  const { data: delivery } = useDelivery(orderId);
  const acceptDelivery = useAcceptDelivery(orderId);

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("en-IN", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      minimumFractionDigits: 0,
    }).format(price);
  };

  if (orderLoading || planLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <main id="main-content" className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">Loading order...</p>
        </main>
        <Footer />
      </div>
    );
  }

  if (!order || !plan) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <main id="main-content" className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">Order not found</p>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <main id="main-content" className="flex-1 border-b border-border">
        <div className="max-w-5xl mx-auto px-6 lg:px-8 py-16 lg:py-24">
          
          {/* Header */}
          <div className="mb-10">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-4">Order tracker</p>
            <h1 className="text-4xl font-bold mb-6 text-balance">HealthTrack — Launch Studio</h1>
            
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
              <div>
                <p className="text-xs text-muted-foreground mb-1">Fixed price</p>
                <p className="text-lg font-semibold">{formatPrice(order.price)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Deadline</p>
                <p className="text-lg font-semibold">{formatDate(order.deadline)}</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Progress</p>
                <p className="text-lg font-semibold">{order.progress_pct}% complete</p>
              </div>
              <div>
                <p className="text-xs text-muted-foreground mb-1">Revisions</p>
                <p className="text-lg font-semibold">{order.revision_limit} rounds available</p>
              </div>
            </div>
          </div>

          {/* Journey stepper */}
          <div className="mb-10 rounded-sm border border-border bg-card p-6 lg:p-8">
            <JourneyStepper
              stages={CLIENT_JOURNEY_STAGES}
              currentStageId={clientStageForOrder(order.status)}
            />
          </div>

          {/* Assemble-team CTA — client staffs the work while team is forming */}
          {order.status === "assembling_team" || order.status === "confirmed" ? (
            <div className="mb-10 flex flex-col gap-4 rounded-sm border border-primary/40 bg-primary/5 p-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-foreground">Assemble your team</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Rank the specialists we shortlisted so we can invite your top choices first.
                </p>
              </div>
              {plan.tasks.length > 0 ? (
                <Link
                  href={`/orders/${orderId}/preferences/${plan.tasks[0].id}`}
                  className="inline-flex h-10 flex-shrink-0 items-center justify-center rounded-sm bg-primary px-5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
                >
                  Assemble team
                </Link>
              ) : null}
            </div>
          ) : null}

          {/* Review-delivery CTA — outcome is ready for the client to accept */}
          {order.status === "delivered" ? (
            <div className="mb-10 flex flex-col gap-4 rounded-sm border border-primary/40 bg-primary/5 p-6 sm:flex-row sm:items-center sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-foreground">Your delivery is ready</p>
                <p className="mt-1 text-sm text-muted-foreground">
                  Review the final deliverables and accept your outcome to close the order.
                </p>
              </div>
              <a
                href="#deliverables"
                className="inline-flex h-10 flex-shrink-0 items-center justify-center rounded-sm bg-primary px-5 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
              >
                Review delivery
              </a>
            </div>
          ) : null}

          {/* Progress bar */}
          <div className="mb-16">
            <div className="flex justify-between items-center mb-2">
              <p className="text-sm font-medium">Overall progress</p>
              <p className="text-sm text-muted-foreground">{order.progress_pct}%</p>
            </div>
            <div className="w-full h-2 bg-border rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${order.progress_pct}%` }}
              />
            </div>
          </div>

          {/* Milestones */}
          <div className="space-y-8">
            {plan.milestones.map((milestone, i) => {
              const milestoneTasks = plan.tasks.filter(t => milestone.task_ids.includes(t.id));
              const allTasksCompleted = milestoneTasks.every(t => t.status === "completed");
              
              return (
                <section key={i} className="border border-border p-8 bg-card">
                  <div className="flex gap-4 mb-6">
                    <div className="flex-shrink-0">
                      <div
                        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                          allTasksCompleted ? "bg-primary text-primary-foreground" : "bg-border text-muted-foreground"
                        }`}
                      >
                        {i + 1}
                      </div>
                    </div>
                    <div className="flex-1">
                      <h2 className="text-lg font-semibold mb-1">{milestone.name}</h2>
                      <p className="text-sm text-muted-foreground">{milestone.client_label}</p>
                    </div>
                    {allTasksCompleted && (
                      <div className="text-xs font-mono tracking-widest uppercase text-green-600 font-semibold self-center">
                        ✓ Done
                      </div>
                    )}
                  </div>

                  {/* Tasks in milestone */}
                  <div className="space-y-3">
                    {milestoneTasks.map((task) => {
                      const tone = taskStatusTone[task.status];
                      const colorClass = toneColors[tone] || toneColors.neutral;
                      const statusLabel = taskStatusClientLabel[task.status];

                      return (
                        <div key={task.id} className="flex gap-4 items-start p-4 border border-border rounded-sm hover:bg-muted/50 transition-colors">
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium">{task.title}</p>
                            {task.description && (
                              <p className="text-xs text-muted-foreground mt-1">{task.description}</p>
                            )}
                          </div>
                          <Link
                            href={`/orders/${orderId}/preferences/${task.id}`}
                            className={`flex-shrink-0 text-xs px-3 py-1 rounded-full whitespace-nowrap font-medium cursor-pointer hover:opacity-80 transition-opacity ${colorClass}`}
                          >
                            {statusLabel}
                          </Link>
                        </div>
                      );
                    })}
                  </div>
                </section>
              );
            })}
          </div>

          {/* Chat & delivery */}
          <div className="mt-16 pt-8 border-t border-border">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <section>
                <h2 className="text-base font-semibold mb-4">Chat with team</h2>
                <div className="border border-border p-6 rounded-sm bg-muted/30 text-center">
                  <p className="text-sm text-muted-foreground">
                    Open a task discussion from the worker job card, or POST
                    /tasks/&#123;id&#125;/discussion
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    Scoped threads persist per task on the real API
                  </p>
                </div>
              </section>

              <section id="deliverables" className="scroll-mt-24">
                <h2 className="text-base font-semibold mb-4">Deliverables</h2>
                {delivery ? (
                  <div className="border border-border p-6 space-y-4">
                    <p className="text-sm text-muted-foreground">{delivery.qa_summary}</p>
                    <ul className="space-y-2">
                      {delivery.assets.map((asset) => (
                        <li key={asset.url} className="text-sm">
                          <a
                            href={asset.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-primary font-medium hover:underline"
                          >
                            {asset.name}
                          </a>
                          <span className="text-xs text-muted-foreground font-mono ml-2">
                            {asset.type}
                          </span>
                        </li>
                      ))}
                    </ul>
                    {order.status === "delivered" || order.status === "closed" ? (
                      <div className="pt-2">
                        {order.status === "closed" || delivery.accepted_at ? (
                          <p className="text-sm text-green-700 font-medium">Outcome accepted</p>
                        ) : (
                          <button
                            type="button"
                            disabled={acceptDelivery.isPending}
                            onClick={async () => {
                              setAcceptError(null);
                              try {
                                await acceptDelivery.mutateAsync();
                              } catch {
                                setAcceptError("Could not accept delivery.");
                              }
                            }}
                            className="h-10 px-5 bg-primary text-primary-foreground text-sm font-semibold disabled:opacity-50"
                          >
                            {acceptDelivery.isPending ? "Accepting…" : "Accept delivery"}
                          </button>
                        )}
                        {acceptError ? (
                          <p className="text-xs text-destructive mt-2">{acceptError}</p>
                        ) : null}
                      </div>
                    ) : (
                      <p className="text-xs text-muted-foreground">
                        Bundle ready when work is submitted and QA advances the order.
                      </p>
                    )}
                  </div>
                ) : (
                  <div className="border border-border p-6 rounded-sm bg-muted/30 text-center">
                    <p className="text-sm text-muted-foreground">Assets appear after submission</p>
                    <p className="text-xs text-muted-foreground mt-2">
                      Final files for review and acceptance
                    </p>
                  </div>
                )}
              </section>
            </div>
          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
}
