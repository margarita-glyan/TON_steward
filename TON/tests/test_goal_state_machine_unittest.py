import os
import sys
import unittest

# Ensure `src/` layout import works under unittest discovery.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(REPO_ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from ton_steward.core.goals.state_machine import (
    GoalLike,
    GoalState,
    InvalidGoalTransition,
    can_transition,
    payment_allowed,
    transition_or_throw,
)


class TestGoalStateMachine(unittest.TestCase):
    def test_valid_transitions(self) -> None:
        valid = [
            (GoalState.draft, GoalState.pending_admin_review),
            (GoalState.pending_admin_review, GoalState.approved),
            (GoalState.pending_admin_review, GoalState.rejected),
            (GoalState.approved, GoalState.funding),
            (GoalState.funding, GoalState.funded),
            (GoalState.approved, GoalState.cancelled),
            (GoalState.funding, GoalState.cancelled),
            (GoalState.funded, GoalState.completed),
            (GoalState.approved, GoalState.funded),  # optional fast-path
        ]
        for frm, to in valid:
            with self.subTest(frm=frm, to=to):
                self.assertTrue(can_transition(frm, to))

    def test_invalid_transitions(self) -> None:
        invalid = [
            (GoalState.rejected, GoalState.approved),
            (GoalState.cancelled, GoalState.funding),
            (GoalState.completed, GoalState.funding),
            (GoalState.funded, GoalState.approved),
            (GoalState.draft, GoalState.funded),
        ]
        for frm, to in invalid:
            with self.subTest(frm=frm, to=to):
                self.assertFalse(can_transition(frm, to))

    def test_terminal_states(self) -> None:
        terminal = [GoalState.completed, GoalState.cancelled, GoalState.rejected]
        for st in terminal:
            with self.subTest(state=st):
                self.assertFalse(can_transition(st, GoalState.funding))
                self.assertFalse(payment_allowed(st))

    def test_payment_eligibility(self) -> None:
        self.assertFalse(payment_allowed(GoalState.draft))
        self.assertFalse(payment_allowed(GoalState.pending_admin_review))
        self.assertTrue(payment_allowed(GoalState.approved))
        self.assertTrue(payment_allowed(GoalState.funding))
        self.assertFalse(payment_allowed(GoalState.funded))

    def test_transition_or_throw(self) -> None:
        goal = GoalLike(state=GoalState.draft)
        transition_or_throw(goal, GoalState.pending_admin_review)
        self.assertEqual(goal.state, GoalState.pending_admin_review)

        with self.assertRaises(InvalidGoalTransition):
            transition_or_throw(goal, GoalState.funded)


if __name__ == "__main__":
    unittest.main()

