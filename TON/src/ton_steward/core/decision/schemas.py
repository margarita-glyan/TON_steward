from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal


class IntentType(str, Enum):
    none = "none"
    create_goal = "create_goal"
    update_goal = "update_goal"
    close_goal = "close_goal"
    summary_request = "summary_request"
    donate = "donate"


class DecisionActionType(str, Enum):
    ignore = "ignore"
    create_draft = "create_draft"
    request_admin_review = "request_admin_review"
    return_summary = "return_summary"
    request_goal_selection = "request_goal_selection"
    reject_update = "reject_update"
    reject_close = "reject_close"
    no_active_goal = "no_active_goal"
    no_permission = "no_permission"
    unsupported = "unsupported"


@dataclass(frozen=True, slots=True)
class DecisionThresholds:
    create_goal: float = 0.75
    update_goal: float = 0.80
    close_goal: float = 0.85
    summary_request: float = 0.65
    donate: float = 0.70


@dataclass(frozen=True, slots=True)
class AIIntent:
    intent_type: IntentType
    confidence: float

    goal_title: str | None = None
    goal_description: str | None = None
    target_amount: float | None = None
    currency: str | None = "TON"
    deadline_iso: str | None = None

    # For updates/close/donate: optionally extracted target goal reference
    referenced_goal_id: int | None = None

    raw: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not (0.0 <= float(self.confidence) <= 1.0):
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class GoalSnapshot:
    id: int
    status: Literal["draft", "approved", "funding", "funded", "completed", "cancelled"]
    title: str


@dataclass(frozen=True, slots=True)
class ChatContext:
    chat_id: int


@dataclass(frozen=True, slots=True)
class UserContext:
    user_id: int
    is_admin: bool = False


@dataclass(frozen=True, slots=True)
class DecisionInput:
    ai: AIIntent
    chat: ChatContext
    user: UserContext

    # Goals currently relevant/visible for decisions (fetched from DB by caller).
    active_goals: list[GoalSnapshot] = field(default_factory=list)
    draft_goals: list[GoalSnapshot] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class DecisionAction:
    action_type: DecisionActionType
    reason: str
    confidence_used: float
    requires_admin_review: bool

    relevant_goal_id: int | None = None
    payload: dict[str, Any] = field(default_factory=dict)

