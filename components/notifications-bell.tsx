"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNotifications } from "@/lib/hooks";
import { notificationsApi } from "@/lib/api";
import type { AppNotification } from "@/lib/types";

function hrefFor(n: AppNotification): string | null {
  if (n.ref_type === "order" && n.ref_id) return `/orders/${n.ref_id}`;
  if (n.ref_type === "task" && n.ref_id) return `/worker/tasks/${n.ref_id}`;
  return null;
}

export default function NotificationsBell() {
  const { data } = useNotifications();
  const items = (data as AppNotification[] | undefined) ?? [];
  const unread = items.filter((n) => !n.read).length;
  const [open, setOpen] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);
  const qc = useQueryClient();

  const markRead = useMutation({
    mutationFn: (id: string) => notificationsApi.markRead(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, [open]);

  return (
    <div className="relative" ref={panelRef}>
      <button
        type="button"
        aria-label={unread ? `${unread} unread notifications` : "Notifications"}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="relative flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
      >
        <svg
          aria-hidden="true"
          viewBox="0 0 24 24"
          className="h-5 w-5"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0"
          />
        </svg>
        {unread > 0 ? (
          <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-semibold text-primary-foreground">
            {unread > 9 ? "9+" : unread}
          </span>
        ) : null}
      </button>

      {open ? (
        <div
          role="dialog"
          aria-label="Notifications"
          className="absolute right-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-md border border-border bg-background shadow-lg sm:w-96"
        >
          <div className="border-b border-border px-4 py-3">
            <p className="text-sm font-semibold text-foreground">Notifications</p>
            <p className="text-xs text-muted-foreground">
              {unread ? `${unread} unread` : "You're caught up"}
            </p>
          </div>
          <ul className="max-h-80 overflow-y-auto">
            {items.length === 0 ? (
              <li className="px-4 py-8 text-center text-sm text-muted-foreground">
                No notifications yet
              </li>
            ) : (
              items.slice(0, 20).map((n) => {
                const href = hrefFor(n);
                const body = (
                  <div className="min-w-0 flex-1">
                    <p
                      className={
                        "text-sm " +
                        (n.read ? "font-normal text-muted-foreground" : "font-medium text-foreground")
                      }
                    >
                      {n.title}
                    </p>
                    <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{n.body}</p>
                  </div>
                );
                return (
                  <li
                    key={n.id}
                    className={
                      "border-b border-border last:border-0 " +
                      (n.read ? "bg-background" : "bg-secondary/40")
                    }
                  >
                    {href ? (
                      <Link
                        href={href}
                        className="flex gap-3 px-4 py-3 transition-colors hover:bg-secondary/60"
                        onClick={() => {
                          if (!n.read) markRead.mutate(n.id);
                          setOpen(false);
                        }}
                      >
                        {body}
                      </Link>
                    ) : (
                      <button
                        type="button"
                        className="flex w-full gap-3 px-4 py-3 text-left transition-colors hover:bg-secondary/60"
                        onClick={() => {
                          if (!n.read) markRead.mutate(n.id);
                        }}
                      >
                        {body}
                      </button>
                    )}
                  </li>
                );
              })
            )}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
