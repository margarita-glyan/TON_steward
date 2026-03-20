from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CreateGoalDraftRequest:
    chat_id: int
    created_by_user_id: int
    title: str | None = None
    description: str | None = None
    target_amount: Decimal | None = None
    currency: str = "TON"
    deadline_at: dt.datetime | None = None
    source_message_id: int | None = None


@dataclass(frozen=True, slots=True)
class ApproveGoalDraftRequest:
    chat_id: int
    draft_id: int
    actor_user_id: int
    wallet_address: str | None = None  # Admin can provide or override


@dataclass(frozen=True, slots=True)
class EditGoalDraftRequest:
    chat_id: int
    draft_id: int
    actor_user_id: int
    title: str | None = None
    description: str | None = None
    target_amount: Decimal | None = None
    currency: str | None = None
    deadline_at: dt.datetime | None = None
    wallet_address: str | None = None


@dataclass(frozen=True, slots=True)
class RejectGoalDraftRequest:
    chat_id: int
    draft_id: int
    actor_user_id: int
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class RegisterConfirmedContributionRequest:
    goal_id: int
    user_id: int
    payment_session_id: str
    amount: Decimal
    currency: str
    tx_hash: str
    confirmed_at: dt.datetime | None = None


@dataclass(frozen=True, slots=True)
class CancelGoalRequest:
    chat_id: int
    goal_id: int
    actor_user_id: int
    reason: str | None = None


@dataclass(frozen=True, slots=True)
class CompleteGoalRequest:
    chat_id: int
    goal_id: int
    actor_user_id: int
    report: str | None = None
