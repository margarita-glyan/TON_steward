from __future__ import annotations

from dataclasses import dataclass
from ton_steward.fundraising.domain.enums import GoalState
from ton_steward.fundraising.domain.models import Goal, GoalDraft, GoalSummary, Contribution


@dataclass(frozen=True, slots=True)
class CreateGoalDraftResponse:
    draft: GoalDraft


@dataclass(frozen=True, slots=True)
class ApproveGoalDraftResponse:
    draft: GoalDraft
    goal: Goal


@dataclass(frozen=True, slots=True)
class EditGoalDraftResponse:
    draft: GoalDraft


@dataclass(frozen=True, slots=True)
class RejectGoalDraftResponse:
    draft: GoalDraft


@dataclass(frozen=True, slots=True)
class RegisterContributionResponse:
    contribution: Contribution
    goal: Goal
    state_transition: tuple[GoalState, GoalState] | None = None


@dataclass(frozen=True, slots=True)
class CancelGoalResponse:
    goal: Goal


@dataclass(frozen=True, slots=True)
class CompleteGoalResponse:
    goal: Goal


@dataclass(frozen=True, slots=True)
class ChatSummaryResponse:
    summary: GoalSummary
