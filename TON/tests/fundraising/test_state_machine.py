from __future__ import annotations

import pytest
from dataclasses import dataclass
from ton_steward.fundraising.domain.enums import GoalState
from ton_steward.fundraising.domain.errors import InvalidGoalStateTransitionError
from ton_steward.fundraising.domain.state_machine import (
    can_transition,
    transition_or_throw,
    is_payable
)


@dataclass
class MockGoal:
    state: GoalState


def test_valid_transitions():
    assert can_transition(GoalState.approved, GoalState.funding) is True
    assert can_transition(GoalState.approved, GoalState.funded) is True
    assert can_transition(GoalState.approved, GoalState.cancelled) is True
    assert can_transition(GoalState.funding, GoalState.funded) is True
    assert can_transition(GoalState.funded, GoalState.completed) is True
    # Self-transition is always valid
    assert can_transition(GoalState.funding, GoalState.funding) is True


def test_invalid_transitions():
    assert can_transition(GoalState.approved, GoalState.completed) is False
    assert can_transition(GoalState.funded, GoalState.cancelled) is False
    assert can_transition(GoalState.completed, GoalState.approved) is False
    assert can_transition(GoalState.cancelled, GoalState.funding) is False


def test_transition_or_throw_success():
    goal = MockGoal(state=GoalState.approved)
    transition_or_throw(goal, GoalState.funding)
    assert goal.state == GoalState.funding


def test_transition_or_throw_failure():
    goal = MockGoal(state=GoalState.completed)
    with pytest.raises(InvalidGoalStateTransitionError):
        transition_or_throw(goal, GoalState.approved)


def test_is_payable():
    assert is_payable(GoalState.approved) is True
    assert is_payable(GoalState.funding) is True
    assert is_payable(GoalState.funded) is False
    assert is_payable(GoalState.completed) is False
    assert is_payable(GoalState.cancelled) is False
