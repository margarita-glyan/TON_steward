from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import Decimal

from ton_steward.fundraising.domain.enums import ContributionStatus, GoalDraftStatus, GoalState


@dataclass(slots=True)
class GoalDraft:
    """
    Initial AI-detected suggestion for a fundraising goal.
    Must be approved by an admin to become an active Goal.
    """
    id: int
    chat_id: int
    created_by_user_id: int
    
    title: str | None
    description: str | None
    target_amount: Decimal | None
    currency: str | None = "TON"
    deadline_at: dt.datetime | None = None
    wallet_address: str | None = None
    
    status: GoalDraftStatus = GoalDraftStatus.draft
    source_message_id: int | None = None
    
    created_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    updated_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))


@dataclass(slots=True)
class Goal:
    """
    An active, admin-approved fundraising goal.
    """
    id: int
    chat_id: int
    created_from_draft_id: int
    created_by_user_id: int
    approved_by_user_id: int
    
    title: str
    description: str | None
    target_amount: Decimal
    wallet_address: str = ""
    collected_amount: Decimal = Decimal("0")
    currency: str = "TON"
    
    deadline_at: dt.datetime | None = None
    
    state: GoalState = GoalState.approved
    
    approved_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    
    completed_at: dt.datetime | None = None
    cancelled_at: dt.datetime | None = None
    
    created_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))
    updated_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))


@dataclass(slots=True)
class Contribution:
    """
    A confirmed financial support attempt by a user.
    """
    id: int
    goal_id: int
    user_id: int
    payment_session_id: str  # Linked to payment module session
    
    amount: Decimal
    currency: str = "TON"
    tx_hash: str = ""  # Unique transaction reference on chain
    status: ContributionStatus = ContributionStatus.pending
    
    confirmed_at: dt.datetime | None = None
    created_at: dt.datetime = field(default_factory=lambda: dt.datetime.now(dt.timezone.utc))


@dataclass(frozen=True, slots=True)
class GoalSummaryItem:
    """
    View model for a single goal in a summary list.
    """
    goal_id: int
    title: str
    state: GoalState
    target_amount: Decimal
    collected_amount: Decimal
    currency: str
    percent_funded: int
    deadline_at: dt.datetime | None
    overdue: bool
    contributors_count: int


@dataclass(frozen=True, slots=True)
class GoalSummary:
    """
    Aggregated summary of all goals in a chat.
    """
    chat_id: int
    active_goals_count: int
    funded_goals_count: int
    completed_goals_count: int
    total_target_amount: Decimal
    total_collected_amount: Decimal
    goals: list[GoalSummaryItem]
