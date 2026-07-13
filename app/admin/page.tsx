"use client";

import { useState } from "react";

import Footer from "@/components/footer";
import {
  useAdminAiDecisions,
  useAdminOrderEvents,
  useAdminOrders,
} from "@/lib/admin-hooks";

export default function AdminPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);

  const { data: ordersData, isLoading: ordersLoading, error: ordersError } =
    useAdminOrders(statusFilter || undefined);
  const { data: eventsData, isLoading: eventsLoading } =
    useAdminOrderEvents(selectedOrderId);
  const { data: aiData, isLoading: aiLoading } = useAdminAiDecisions(50);

  const orders = ordersData?.orders ?? [];
  const events = eventsData?.events ?? [];
  const decisions = aiData?.decisions ?? [];

  return (
    <div className="min-h-screen bg-background text-foreground font-sans flex flex-col">

      <main className="flex-1 border-b border-border">
        <div className="max-w-6xl mx-auto px-6 lg:px-8 py-16 lg:py-20 space-y-14">
          <div>
            <p className="text-xs font-mono tracking-widest uppercase text-primary mb-2">
              Admin ┬╖ read-only
            </p>
            <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-2">
              Ops console
            </h1>
            <p className="text-sm text-muted-foreground max-w-xl">
              Inspect order state, event_log timeline, and AI decision audit ΓÇö
              no writes.
            </p>
          </div>

          {/* Orders */}
          <section>
            <div className="flex flex-wrap items-end justify-between gap-4 mb-4">
              <h2 className="text-lg font-semibold tracking-tight">Orders</h2>
              <label className="text-xs font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-2">
                Status
                <input
                  type="text"
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value.trim())}
                  placeholder="e.g. delivery_active"
                  className="h-8 w-48 px-2 border border-border bg-background text-sm font-sans normal-case tracking-normal"
                />
              </label>
            </div>
            {ordersError ? (
              <p className="text-sm text-destructive">
                Failed to load orders ({String(ordersError)})
              </p>
            ) : ordersLoading ? (
              <p className="text-sm text-muted-foreground">LoadingΓÇª</p>
            ) : orders.length === 0 ? (
              <p className="text-sm text-muted-foreground">No orders.</p>
            ) : (
              <div className="overflow-x-auto border border-border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs font-mono uppercase tracking-wider text-muted-foreground">
                      <th className="px-3 py-2 font-medium">ID</th>
                      <th className="px-3 py-2 font-medium">Status</th>
                      <th className="px-3 py-2 font-medium">Progress</th>
                      <th className="px-3 py-2 font-medium">Price</th>
                      <th className="px-3 py-2 font-medium">Updated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {orders.map((o) => (
                      <tr
                        key={o.id}
                        onClick={() => setSelectedOrderId(o.id)}
                        className={
                          selectedOrderId === o.id
                            ? "bg-primary/5 cursor-pointer"
                            : "hover:bg-muted/40 cursor-pointer"
                        }
                      >
                        <td className="px-3 py-2 font-mono text-xs truncate max-w-[12rem]">
                          {o.id}
                        </td>
                        <td className="px-3 py-2">{o.status}</td>
                        <td className="px-3 py-2">{o.progress_pct}%</td>
                        <td className="px-3 py-2">{o.price}</td>
                        <td className="px-3 py-2 text-muted-foreground text-xs">
                          {new Date(o.updated_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          {/* Event timeline */}
          <section>
            <h2 className="text-lg font-semibold tracking-tight mb-4">
              Event timeline
              {selectedOrderId ? (
                <span className="ml-2 text-xs font-mono font-normal text-muted-foreground">
                  {selectedOrderId}
                </span>
              ) : null}
            </h2>
            {!selectedOrderId ? (
              <p className="text-sm text-muted-foreground">
                Select an order to load event_log (order + child tasks).
              </p>
            ) : eventsLoading ? (
              <p className="text-sm text-muted-foreground">LoadingΓÇª</p>
            ) : events.length === 0 ? (
              <p className="text-sm text-muted-foreground">No events.</p>
            ) : (
              <ol className="space-y-3 border-l border-border pl-4">
                {events.map((e) => (
                  <li key={e.id} className="relative">
                    <span className="absolute -left-[1.15rem] top-1.5 h-2 w-2 rounded-full bg-primary" />
                    <p className="text-sm font-medium">
                      {e.event_type}{" "}
                      <span className="text-xs font-mono text-muted-foreground">
                        {e.aggregate_type}:{e.aggregate_id.slice(0, 8)}
                      </span>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(e.created_at).toLocaleString()}
                      {e.actor_type ? ` ┬╖ ${e.actor_type}` : ""}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </section>

          {/* AI decisions */}
          <section>
            <h2 className="text-lg font-semibold tracking-tight mb-4">
              AI decisions
            </h2>
            {aiLoading ? (
              <p className="text-sm text-muted-foreground">LoadingΓÇª</p>
            ) : decisions.length === 0 ? (
              <p className="text-sm text-muted-foreground">No AI decisions logged.</p>
            ) : (
              <div className="overflow-x-auto border border-border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-left text-xs font-mono uppercase tracking-wider text-muted-foreground">
                      <th className="px-3 py-2 font-medium">When</th>
                      <th className="px-3 py-2 font-medium">Agent</th>
                      <th className="px-3 py-2 font-medium">Source</th>
                      <th className="px-3 py-2 font-medium">Model</th>
                      <th className="px-3 py-2 font-medium">Reply / error</th>
                    </tr>
                  </thead>
                  <tbody>
                    {decisions.map((d) => (
                      <tr key={d.id} className="border-t border-border">
                        <td className="px-3 py-2 text-xs text-muted-foreground whitespace-nowrap">
                          {new Date(d.created_at).toLocaleString()}
                        </td>
                        <td className="px-3 py-2 font-mono text-xs">{d.agent_type}</td>
                        <td className="px-3 py-2">{d.source}</td>
                        <td className="px-3 py-2 text-xs">{d.model ?? "ΓÇö"}</td>
                        <td className="px-3 py-2 text-xs max-w-md truncate">
                          {d.error ? (
                            <span className="text-destructive">{d.error}</span>
                          ) : (
                            d.reply ?? "ΓÇö"
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </div>
      </main>
      <Footer />
    </div>
  );
}
