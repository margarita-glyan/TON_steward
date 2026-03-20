from __future__ import annotations

from typing import Protocol
from ton_steward.fundraising.domain.enums import GoalState
from ton_steward.fundraising.domain.errors import InvalidGoalStateTransitionError

# Terminal states: once reached, no further transitions are allowed.
TERMINAL_STATES: frozenset[GoalState] = frozenset({
    GoalState.completed, 
    GoalState.cancelled
})

# Allowed state transitions.
# approved -> funding (first contribution)
# approved -> funded (first contribution meets/exceeds target)
# approved -> cancelled (admin aborts)
# funding  -> funded (contributions meet/exceed target)
# funding  -> cancelled (admin aborts)
# funded   -> completed (admin confirms distribution)
ALLOWED_TRANSITIONS: dict[GoalState, frozenset[GoalState]] = {
    GoalState.approved: frozenset({GoalState.funding, GoalState.funded, GoalState.cancelled}),
    GoalState.funding: frozenset({GoalState.funded, GoalState.cancelled}),
    GoalState.funded: frozenset({GoalState.completed}),
    GoalState.completed: frozenset(),
    GoalState.cancelled: frozenset(),
}

class GoalLike(Protocol):
    """Protocol for any object that has a state property of type GoalState."""
    state: GoalState

def can_transition(from_state: GoalState, to_state: GoalState) -> bool:
    """Checks if a transition from one state to another is allowed."""
    if from_state == to_state:
        return True
    return to_state in ALLOWED_TRANSITIONS.get(from_state, frozenset())

def transition_or_throw(goal: GoalLike, to_state: GoalState) -> None:
    """Performs state transition or raises InvalidGoalStateTransitionError."""
    if not can_transition(goal.state, to_state):
        raise InvalidGoalStateTransitionError(
            f"Illegal state transition from {goal.state.value} to {to_state.value}"
        )
    goal.state = to_state

def is_payable(state: GoalState) -> bool:
    """Returns True if the goal can still accept contributions in this state."""
    return state in {GoalState.approved, GoalState.funding}
