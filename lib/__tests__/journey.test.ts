import { describe, expect, it } from "vitest";
import {
  CLIENT_JOURNEY_STAGES,
  WORKER_JOURNEY_STAGES,
  clientStageForOrder,
  isOrderCancelled,
  workerStageForTask,
} from "../journey";

describe("clientStageForOrder", () => {
  it("maps delivery milestones to stepper stages", () => {
    expect(clientStageForOrder("confirmed")).toBe("team");
    expect(clientStageForOrder("assembling_team")).toBe("team");
    expect(clientStageForOrder("delivery_active")).toBe("progress");
    expect(clientStageForOrder("delivered")).toBe("delivery");
    expect(clientStageForOrder("closed")).toBe("accepted");
  });

  it("keeps amendment and escalation on progress stage", () => {
    expect(clientStageForOrder("amendment_pending")).toBe("progress");
    expect(clientStageForOrder("escalated")).toBe("progress");
  });
});

describe("isOrderCancelled", () => {
  it("detects cancelled orders", () => {
    expect(isOrderCancelled("cancelled")).toBe(true);
    expect(isOrderCancelled("closed")).toBe(false);
  });
});

describe("workerStageForTask", () => {
  it("maps worker-visible task states to journey stages", () => {
    expect(workerStageForTask("invited")).toBe("invited");
    expect(workerStageForTask("priority_active")).toBe("accepted");
    expect(workerStageForTask("in_progress")).toBe("progress");
    expect(workerStageForTask("submitted")).toBe("qa");
    expect(workerStageForTask("completed")).toBe("completed");
  });

  it("returns null for blocked or cancelled tasks off the journey", () => {
    expect(workerStageForTask("blocked")).toBeNull();
    expect(workerStageForTask("cancelled")).toBeNull();
  });

  it("maps ready tasks to invited stage", () => {
    expect(workerStageForTask("ready")).toBe("invited");
  });
});

describe("journey stage lists", () => {
  it("defines stable client and worker stage ids", () => {
    expect(CLIENT_JOURNEY_STAGES.map((s) => s.id)).toEqual([
      "scope",
      "quote",
      "confirm",
      "team",
      "progress",
      "delivery",
      "accepted",
    ]);
    expect(WORKER_JOURNEY_STAGES.map((s) => s.id)).toEqual([
      "invited",
      "accepted",
      "progress",
      "qa",
      "completed",
    ]);
  });
});
