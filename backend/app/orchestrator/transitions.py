"""Legal state transitions — Technical Spec §5.1 and §5.2."""


class IllegalTransitionError(Exception):
    def __init__(self, aggregate: str, from_status: str, event: str):
        super().__init__(f"{aggregate}: illegal transition {from_status!r} --[{event}]-->")
        self.aggregate = aggregate
        self.from_status = from_status
        self.event = event


# (from_status, event) -> to_status
ORDER_TRANSITIONS: dict[tuple[str, str], str] = {
    ("confirmed", "plan_and_preferences_set"): "assembling_team",
    ("confirmed", "first_mutual_start"): "delivery_active",  # stage path without prefs
    ("confirmed", "cancel"): "cancelled",
    ("assembling_team", "first_mutual_start"): "delivery_active",
    ("delivery_active", "all_tasks_submitted"): "under_quality_check",
    ("delivery_active", "amendment_requested"): "amendment_pending",
    ("delivery_active", "escalate"): "escalated",
    ("amendment_pending", "amendment_approved"): "delivery_active",
    ("escalated", "resolve"): "delivery_active",
    ("escalated", "cancel"): "cancelled",
    ("under_quality_check", "bundle_ready"): "delivered",
    ("delivered", "client_accept"): "closed",
    ("delivered", "auto_accept"): "closed",
}

TASK_TRANSITIONS: dict[tuple[str, str], str] = {
    ("blocked", "dependencies_met"): "ready",
    ("ready", "preferences_set"): "invited",
    ("ready", "interest_accepted"): "interest_pool",  # open pool accept before prefs
    ("invited", "interest_accepted"): "interest_pool",
    ("interest_pool", "priority_granted"): "priority_active",
    ("priority_active", "ready_to_start"): "start_requested",
    ("priority_active", "priority_expired"): "priority_active",  # promote backup, stay in state
    ("priority_active", "preferences_exhausted"): "invited",
    ("start_requested", "mutual_start_confirmed"): "mutual_start",
    ("mutual_start", "work_started"): "in_progress",
    ("in_progress", "submitted"): "submitted",
    ("submitted", "qa_pass"): "completed",
    ("submitted", "qa_fail"): "rework",
    ("rework", "resubmitted"): "submitted",
    ("invited", "cancel"): "cancelled",
    ("priority_active", "backup_released"): "released",
}


def resolve_transition(
    aggregate: str,
    transitions: dict[tuple[str, str], str],
    from_status: str,
    event: str,
) -> str:
    key = (from_status, event)
    if key not in transitions:
        raise IllegalTransitionError(aggregate, from_status, event)
    return transitions[key]
