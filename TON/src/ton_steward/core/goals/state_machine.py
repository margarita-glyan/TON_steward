from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GoalState(str, Enum):
    draft = "draft"
    pending_admin_review = "pending_admin_review"
    approved = "approved"
    funding = "funding"
    funded = "funded"
    completed = "completed"
    cancelled = "cancelled"
    rejected = "rejected"


TERMINAL_STATES: frozenset[GoalState] = frozenset({GoalState.completed, GoalState.cancelled, GoalState.rejected})


ALLOWED_TRANSITIONS: dict[GoalState, frozenset[GoalState]] = {
    GoalState.draft: frozenset({GoalState.pending_admin_review}),
    GoalState.pending_admin_review: frozenset({GoalState.approved, GoalState.rejected}),
    GoalState.approved: frozenset({GoalState.funding, GoalState.funded, GoalState.cancelled}),
    GoalState.funding: frozenset({GoalState.funded, GoalState.cancelled}),
    GoalState.funded: frozenset({GoalState.completed}),
    GoalState.completed: frozenset(),
    GoalState.cancelled: frozenset(),
    GoalState.rejected: frozenset(),
}


def can_transition(from_state: GoalState, to_state: GoalState) -> bool:
    if from_state == to_state:
        return True
    return to_state in ALLOWED_TRANSITIONS.get(from_state, frozenset())


def payment_allowed(state: GoalState) -> bool:
    """
    Safety rule: payments are only allowed when goal is user-visible and accepting funds.
    """
    return state in {GoalState.approved, GoalState.funding}


class InvalidGoalTransition(ValueError):
    pass


@dataclass(slots=True)
class GoalLike:
    """
    Minimal shape for transition_or_throw.
    Real DB model can be used as long as it has a mutable `status`/`state` field.
    """

    state: GoalState


def transition_or_throw(goal: GoalLike, new_state: GoalState) -> None:
    current = goal.state
    if not can_transition(current, new_state):
        raise InvalidGoalTransition(f"illegal transition: {current.value} -> {new_state.value}")
    goal.state = new_state

