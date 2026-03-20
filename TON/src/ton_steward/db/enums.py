from __future__ import annotations

from enum import Enum


class GoalStatus(str, Enum):
    draft = "draft"
    approved = "approved"
    funding = "funding"
    funded = "funded"
    completed = "completed"
    cancelled = "cancelled"


class DraftStatus(str, Enum):
    proposed = "proposed"
    approved = "approved"
    rejected = "rejected"


class PaymentSessionStatus(str, Enum):
    created = "created"
    awaiting_payment = "awaiting_payment"
    verifying = "verifying"
    succeeded = "succeeded"
    failed = "failed"
    expired = "expired"
    cancelled = "cancelled"


class ReminderJobType(str, Enum):
    goal_deadline = "goal_deadline"
    goal_summary = "goal_summary"
    personal_nudge = "personal_nudge"


class AuditAction(str, Enum):
    create = "create"
    update = "update"
    delete = "delete"
    status_transition = "status_transition"
    admin_decision = "admin_decision"

