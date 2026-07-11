from datetime import timedelta

from app.orchestrator.timers import InMemoryTimerQueue, TimerKind


def test_schedule_and_fire_timer():
    queue = InMemoryTimerQueue()
    timer = queue.schedule(
        TimerKind.PRIORITY_WINDOW,
        aggregate_id="task-123",
        delay=timedelta(hours=-1),  # already due
        payload={"worker_id": "w1"},
    )
    assert timer.kind == TimerKind.PRIORITY_WINDOW
    due = queue.due()
    assert len(due) == 1
    assert due[0].aggregate_id == "task-123"
