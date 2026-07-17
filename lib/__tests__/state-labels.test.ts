import { describe, expect, it } from "vitest";
import {
  orderStatusClientLabel,
  taskStatusClientLabel,
  taskStatusWorkerLabel,
} from "../state-labels";
import type { OrderStatus, TaskStatus } from "../types";

const ALL_TASK_STATUSES: TaskStatus[] = [
  "blocked",
  "ready",
  "invited",
  "interest_pool",
  "priority_active",
  "start_requested",
  "mutual_start",
  "in_progress",
  "submitted",
  "rework",
  "completed",
  "cancelled",
  "released",
];

const ALL_ORDER_STATUSES: OrderStatus[] = [
  "confirmed",
  "assembling_team",
  "delivery_active",
  "under_quality_check",
  "delivered",
  "closed",
  "amendment_pending",
  "escalated",
  "cancelled",
];

describe("taskStatusClientLabel", () => {
  it("covers every TaskStatus", () => {
    for (const status of ALL_TASK_STATUSES) {
      expect(taskStatusClientLabel[status]).toBeTruthy();
    }
  });

  it("hides rework from clients (reads as in progress)", () => {
    expect(taskStatusClientLabel.rework).toBe("In progress");
    expect(taskStatusWorkerLabel.rework).toBe("Fix checklist");
  });

  it("never exposes internal failure language to clients", () => {
    expect(taskStatusClientLabel.rework).not.toMatch(/rework|fail|qa/i);
  });
});

describe("orderStatusClientLabel", () => {
  it("covers every OrderStatus", () => {
    for (const status of ALL_ORDER_STATUSES) {
      expect(orderStatusClientLabel[status]).toBeTruthy();
    }
  });
});
