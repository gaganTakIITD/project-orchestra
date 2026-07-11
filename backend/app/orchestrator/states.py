"""Domain status enums — mirror lib/types.ts and Technical Spec §5."""

from enum import StrEnum


class OrderStatus(StrEnum):
    CONFIRMED = "confirmed"
    ASSEMBLING_TEAM = "assembling_team"
    DELIVERY_ACTIVE = "delivery_active"
    UNDER_QUALITY_CHECK = "under_quality_check"
    DELIVERED = "delivered"
    CLOSED = "closed"
    AMENDMENT_PENDING = "amendment_pending"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    BLOCKED = "blocked"
    READY = "ready"
    INVITED = "invited"
    INTEREST_POOL = "interest_pool"
    PRIORITY_ACTIVE = "priority_active"
    START_REQUESTED = "start_requested"
    MUTUAL_START = "mutual_start"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    REWORK = "rework"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RELEASED = "released"


class ActorType(StrEnum):
    CLIENT = "client"
    WORKER = "worker"
    SYSTEM = "system"
    AI = "ai"
    ADMIN = "admin"
