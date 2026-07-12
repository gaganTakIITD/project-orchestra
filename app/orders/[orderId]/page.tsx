'use client';

import { useState } from 'react';
import { useOrder, usePlan } from "@/lib/hooks";
import { taskStatusClientLabel, taskStatusTone, orderStatusClientLabel } from "@/lib/state-labels";
import Header from "@/components/header";
import Footer from "@/components/footer";
import DiscussionPanel from "@/components/discussion-panel";
import Link from "next/link";

const toneColors: Record<string, string> = {
  neutral: "bg-muted text-muted-foreground",
  info: "bg-blue-100 text-blue-900",
  active: "bg-indigo-100 text-indigo-900",
  review: "bg-amber-100 text-amber-900",
  success: "bg-green-100 text-green-900",
  danger: "bg-red-100 text-red-900",
};

const getTitleForOrder = (plan: any): string => {
  // Try to get title from first milestone name
  if (plan.milestones && plan.milestones.length > 0 && plan.milestones[0].name) {
    return plan.milestones[0].name;
  }
  // Fallback to generic title
  return "Your outcome";
};

export default function OrderTrackerPage({ params }: { params: { orderId: string } }) {
  const orderId = params.orderId;
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  
  const { data: order, isLoading: orderLoading } = useOrder(orderId);
  const { data: plan, isLoading: planLoading } = usePlan(orderId);

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
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">Loading order...</p>
        </main>
        <Footer />
      </div>
    );
  }

  if (!order || !plan) {
    return (
      <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">Order not found</p>
        </main>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">
      <Header />

      <main className="flex-1 border-b border-border">
        <div className="max-w-5xl mx-auto px-6 lg:px-8 py-20 lg:py-28">
          
          {/* Header */}
          <div className="mb-12">
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-4">Order tracker</p>
            <div className="flex items-start justify-between gap-6 mb-6">
              <h1 className="text-4xl font-bold">{getTitleForOrder(plan)}</h1>
              <div className={`px-3 py-1 rounded-full text-xs font-medium whitespace-nowrap ${toneColors[
                order.status === 'confirmed' ? 'info' :
                order.status === 'assembling_team' ? 'active' :
                order.status === 'delivery_active' ? 'active' :
                order.status === 'under_quality_check' ? 'review' :
                order.status === 'delivered' ? 'review' :
                order.status === 'closed' ? 'success' :
                order.status === 'amendment_pending' ? 'review' :
                order.status === 'escalated' ? 'danger' :
                order.status === 'cancelled' ? 'danger' :
                'neutral'
              ]}`}>
                {orderStatusClientLabel[order.status]}
              </div>
            </div>
            
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
                        <div
                          key={task.id}
                          onClick={() => setSelectedTaskId(task.id)}
                          className={`flex gap-4 items-start p-4 border rounded-sm cursor-pointer transition-colors ${
                            selectedTaskId === task.id
                              ? 'border-primary bg-primary/5'
                              : 'border-border hover:bg-muted/50'
                          }`}
                        >
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium">{task.title}</p>
                            {task.description && (
                              <p className="text-xs text-muted-foreground mt-1">{task.description}</p>
                            )}
                          </div>
                          <Link
                            href={`/orders/${orderId}/preferences/${task.id}`}
                            onClick={(e) => e.stopPropagation()}
                            className={`flex-shrink-0 text-xs px-3 py-1 rounded-full whitespace-nowrap font-medium hover:opacity-80 transition-opacity ${colorClass}`}
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

          {/* Chat & Updates section */}
          <div className="mt-16 pt-8 border-t border-border">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <section>
                <h2 className="text-base font-semibold mb-4">Chat with team</h2>
                {selectedTaskId ? (
                  <DiscussionPanel taskId={selectedTaskId} />
                ) : (
                  <div className="border border-border p-6 rounded-sm bg-muted/30 text-center">
                    <p className="text-sm text-muted-foreground">Select a task above to view discussion</p>
                    <p className="text-xs text-muted-foreground mt-2">Click any task to open its thread with your team</p>
                  </div>
                )}
              </section>

              <section>
                <h2 className="text-base font-semibold mb-4">Deliverables</h2>
                <div className="border border-border p-6 rounded-sm bg-muted/30 text-center">
                  <p className="text-sm text-muted-foreground">Assets will appear here</p>
                  <p className="text-xs text-muted-foreground mt-2">Final files for review and acceptance</p>
                </div>
              </section>
            </div>
          </div>

        </div>
      </main>

      <Footer />
    </div>
  );
}
