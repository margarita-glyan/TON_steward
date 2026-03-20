import datetime as dt
import os
import sys
import unittest
from dataclasses import dataclass
from decimal import Decimal

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(REPO_ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from ton_steward.fundraising.application.services import (  # noqa: E402
    approve_goal_draft,
    cancel_goal,
    complete_goal,
    create_goal_draft,
    edit_goal_draft,
    get_chat_goal_summary,
    register_confirmed_contribution,
    reject_goal_draft,
)
from ton_steward.fundraising.domain.enums import GoalDraftStatus, GoalState  # noqa: E402
from ton_steward.fundraising.domain.errors import (  # noqa: E402
    DraftNotReviewableError,
    DuplicateContributionError,
    GoalAlreadyCancelledError,
    GoalAlreadyCompletedError,
    InvalidContributionError,
    InvalidGoalStateTransitionError,
    NoPermissionError,
)
from ton_steward.fundraising.domain.models import Contribution, Goal, GoalDraft  # noqa: E402
from ton_steward.fundraising.dto.requests import (  # noqa: E402
    ApproveGoalDraftRequest,
    CancelGoalRequest,
    CompleteGoalRequest,
    CreateGoalDraftRequest,
    EditGoalDraftRequest,
    RegisterConfirmedContributionRequest,
    RejectGoalDraftRequest,
)


class InMemoryAudit:
    def __init__(self) -> None:
        self.events = []

    def emit(self, **kwargs):  # type: ignore[no-untyped-def]
        self.events.append(kwargs)


class InMemoryAdminChecker:
    def __init__(self, admins: set[tuple[int, int]]):
        self.admins = admins

    def is_admin(self, *, chat_id: int, user_id: int) -> bool:
        return (chat_id, user_id) in self.admins


class InMemoryDraftRepo:
    def __init__(self) -> None:
        self._id = 0
        self.items: dict[int, GoalDraft] = {}

    def next_id(self) -> int:
        self._id += 1
        return self._id

    def find_by_id(self, draft_id: int) -> GoalDraft | None:
        return self.items.get(draft_id)

    def save(self, draft: GoalDraft) -> None:
        self.items[draft.id] = draft

    def update(self, draft: GoalDraft) -> None:
        self.items[draft.id] = draft


class InMemoryGoalRepo:
    def __init__(self) -> None:
        self._id = 0
        self.items: dict[int, Goal] = {}

    def next_id(self) -> int:
        self._id += 1
        return self._id

    def find_by_id(self, goal_id: int) -> Goal | None:
        return self.items.get(goal_id)

    def save(self, goal: Goal) -> None:
        self.items[goal.id] = goal

    def update(self, goal: Goal) -> None:
        self.items[goal.id] = goal

    def list_by_chat_id(self, chat_id: int) -> list[Goal]:
        return [g for g in self.items.values() if g.chat_id == chat_id]

    def list_active_by_chat_id(self, chat_id: int) -> list[Goal]:
        return [g for g in self.items.values() if g.chat_id == chat_id and g.state in {GoalState.approved, GoalState.funding, GoalState.funded}]


class InMemoryContributionRepo:
    def __init__(self) -> None:
        self._id = 0
        self.items: dict[int, Contribution] = {}
        self._tx: set[str] = set()

    def next_id(self) -> int:
        self._id += 1
        return self._id

    def exists_by_tx_hash(self, tx_hash: str) -> bool:
        return tx_hash in self._tx

    def save(self, contribution: Contribution) -> None:
        self.items[contribution.id] = contribution
        self._tx.add(contribution.tx_hash)

    def list_confirmed_by_goal_id(self, goal_id: int) -> list[Contribution]:
        return [c for c in self.items.values() if c.goal_id == goal_id and c.status.value == "confirmed"]

    def sum_confirmed_by_goal_id(self, goal_id: int) -> Decimal:
        total = Decimal("0")
        for c in self.items.values():
            if c.goal_id == goal_id and c.status.value == "confirmed":
                total += c.amount
        return total

    def count_confirmed_contributors_by_goal_id(self, goal_id: int) -> int:
        users = {c.user_id for c in self.items.values() if c.goal_id == goal_id and c.status.value == "confirmed"}
        return len(users)


class TestFundraisingCore(unittest.TestCase):
    def setUp(self) -> None:
        self.audit = InMemoryAudit()
        self.admins = InMemoryAdminChecker(admins={(1, 999)})
        self.drafts = InMemoryDraftRepo()
        self.goals = InMemoryGoalRepo()
        self.contributions = InMemoryContributionRepo()

    def test_create_draft_successfully(self) -> None:
        resp = create_goal_draft(
            CreateGoalDraftRequest(
                chat_id=1,
                created_by_user_id=10,
                source_message_id=123,
                title="Entrance cameras",
                description=None,
                target_amount=Decimal("500"),
                currency="TON",
                deadline_at=None,
            ),
            drafts=self.drafts,
            audit=self.audit,
        )
        self.assertEqual(resp.draft.status, GoalDraftStatus.pending_admin_review)

    def test_non_admin_approval_rejected(self) -> None:
        draft = create_goal_draft(
            CreateGoalDraftRequest(
                chat_id=1,
                created_by_user_id=10,
                source_message_id=1,
                title="X",
                description=None,
                target_amount=Decimal("10"),
                currency="TON",
                deadline_at=None,
            ),
            drafts=self.drafts,
            audit=self.audit,
        ).draft
        with self.assertRaises(NoPermissionError):
            approve_goal_draft(
                ApproveGoalDraftRequest(chat_id=1, actor_user_id=10, draft_id=draft.id, wallet_address="w"),
                admin_checker=self.admins,
                drafts=self.drafts,
                goals=self.goals,
                audit=self.audit,
            )

    def test_approve_draft_successfully(self) -> None:
        draft = create_goal_draft(
            CreateGoalDraftRequest(
                chat_id=1,
                created_by_user_id=10,
                source_message_id=1,
                title="X",
                description=None,
                target_amount=Decimal("10"),
                currency="TON",
                deadline_at=None,
            ),
            drafts=self.drafts,
            audit=self.audit,
        ).draft
        resp = approve_goal_draft(
            ApproveGoalDraftRequest(chat_id=1, actor_user_id=999, draft_id=draft.id, wallet_address="wallet"),
            admin_checker=self.admins,
            drafts=self.drafts,
            goals=self.goals,
            audit=self.audit,
        )
        self.assertEqual(resp.draft.status, GoalDraftStatus.approved_converted)
        self.assertEqual(resp.goal.state, GoalState.approved)

    def test_reject_draft_successfully(self) -> None:
        draft = create_goal_draft(
            CreateGoalDraftRequest(
                chat_id=1,
                created_by_user_id=10,
                source_message_id=1,
                title="X",
                description=None,
                target_amount=Decimal("10"),
                currency="TON",
                deadline_at=None,
            ),
            drafts=self.drafts,
            audit=self.audit,
        ).draft
        resp = reject_goal_draft(
            RejectGoalDraftRequest(chat_id=1, actor_user_id=999, draft_id=draft.id, reason="no"),
            admin_checker=self.admins,
            drafts=self.drafts,
            audit=self.audit,
        )
        self.assertEqual(resp.draft.status, GoalDraftStatus.rejected)

    def test_edit_draft_successfully(self) -> None:
        draft = create_goal_draft(
            CreateGoalDraftRequest(
                chat_id=1,
                created_by_user_id=10,
                source_message_id=1,
                title="X",
                description=None,
                target_amount=Decimal("10"),
                currency="TON",
                deadline_at=None,
            ),
            drafts=self.drafts,
            audit=self.audit,
        ).draft
        resp = edit_goal_draft(
            EditGoalDraftRequest(chat_id=1, actor_user_id=999, draft_id=draft.id, title="Y", wallet_address="w"),
            admin_checker=self.admins,
            drafts=self.drafts,
            audit=self.audit,
        )
        self.assertEqual(resp.draft.title, "Y")
        self.assertEqual(resp.draft.wallet_address, "w")
        self.assertEqual(resp.draft.status, GoalDraftStatus.pending_admin_review)

    def test_approve_rejected_draft_should_fail(self) -> None:
        draft = create_goal_draft(
            CreateGoalDraftRequest(
                chat_id=1,
                created_by_user_id=10,
                source_message_id=1,
                title="X",
                description=None,
                target_amount=Decimal("10"),
                currency="TON",
                deadline_at=None,
            ),
            drafts=self.drafts,
            audit=self.audit,
        ).draft
        reject_goal_draft(
            RejectGoalDraftRequest(chat_id=1, actor_user_id=999, draft_id=draft.id),
            admin_checker=self.admins,
            drafts=self.drafts,
            audit=self.audit,
        )
        with self.assertRaises(DraftNotReviewableError):
            approve_goal_draft(
                ApproveGoalDraftRequest(chat_id=1, actor_user_id=999, draft_id=draft.id, wallet_address="w"),
                admin_checker=self.admins,
                drafts=self.drafts,
                goals=self.goals,
                audit=self.audit,
            )

    def _create_approved_goal(self, *, target: Decimal = Decimal("10")) -> Goal:
        draft = create_goal_draft(
            CreateGoalDraftRequest(
                chat_id=1,
                created_by_user_id=10,
                source_message_id=1,
                title="X",
                description=None,
                target_amount=target,
                currency="TON",
                deadline_at=None,
            ),
            drafts=self.drafts,
            audit=self.audit,
        ).draft
        resp = approve_goal_draft(
            ApproveGoalDraftRequest(chat_id=1, actor_user_id=999, draft_id=draft.id, wallet_address="wallet"),
            admin_checker=self.admins,
            drafts=self.drafts,
            goals=self.goals,
            audit=self.audit,
        )
        return resp.goal

    def test_contribution_to_approved_goal_succeeds(self) -> None:
        goal = self._create_approved_goal(target=Decimal("10"))
        resp = register_confirmed_contribution(
            RegisterConfirmedContributionRequest(
                goal_id=goal.id,
                user_id=50,
                payment_session_id="ps1",
                amount=Decimal("1"),
                currency="TON",
                tx_hash="tx1",
            ),
            goals=self.goals,
            contributions=self.contributions,
            audit=self.audit,
        )
        self.assertEqual(resp.goal.collected_amount, Decimal("1"))

    def test_contribution_to_cancelled_goal_fails(self) -> None:
        goal = self._create_approved_goal(target=Decimal("10"))
        cancel_goal(
            CancelGoalRequest(chat_id=1, actor_user_id=999, goal_id=goal.id),
            admin_checker=self.admins,
            goals=self.goals,
            audit=self.audit,
        )
        with self.assertRaises(GoalAlreadyCancelledError):
            register_confirmed_contribution(
                RegisterConfirmedContributionRequest(
                    goal_id=goal.id,
                    user_id=50,
                    payment_session_id="ps1",
                    amount=Decimal("1"),
                    currency="TON",
                    tx_hash="tx2",
                ),
                goals=self.goals,
                contributions=self.contributions,
                audit=self.audit,
            )

    def test_first_contribution_moves_approved_to_funding(self) -> None:
        goal = self._create_approved_goal(target=Decimal("10"))
        resp = register_confirmed_contribution(
            RegisterConfirmedContributionRequest(
                goal_id=goal.id,
                user_id=50,
                payment_session_id="ps1",
                amount=Decimal("1"),
                currency="TON",
                tx_hash="tx3",
            ),
            goals=self.goals,
            contributions=self.contributions,
            audit=self.audit,
        )
        self.assertEqual(resp.goal.state, GoalState.funding)

    def test_reaching_target_moves_funding_to_funded(self) -> None:
        goal = self._create_approved_goal(target=Decimal("2"))
        register_confirmed_contribution(
            RegisterConfirmedContributionRequest(
                goal_id=goal.id,
                user_id=50,
                payment_session_id="ps1",
                amount=Decimal("1"),
                currency="TON",
                tx_hash="tx4",
            ),
            goals=self.goals,
            contributions=self.contributions,
            audit=self.audit,
        )
        resp = register_confirmed_contribution(
            RegisterConfirmedContributionRequest(
                goal_id=goal.id,
                user_id=51,
                payment_session_id="ps2",
                amount=Decimal("1"),
                currency="TON",
                tx_hash="tx5",
            ),
            goals=self.goals,
            contributions=self.contributions,
            audit=self.audit,
        )
        self.assertEqual(resp.goal.state, GoalState.funded)

    def test_funded_to_completed_succeeds(self) -> None:
        goal = self._create_approved_goal(target=Decimal("1"))
        register_confirmed_contribution(
            RegisterConfirmedContributionRequest(
                goal_id=goal.id,
                user_id=50,
                payment_session_id="ps1",
                amount=Decimal("1"),
                currency="TON",
                tx_hash="tx6",
            ),
            goals=self.goals,
            contributions=self.contributions,
            audit=self.audit,
        )
        # goal should be funded
        goal = self.goals.find_by_id(goal.id)
        self.assertEqual(goal.state, GoalState.funded)
        resp = complete_goal(
            CompleteGoalRequest(chat_id=1, actor_user_id=999, goal_id=goal.id, report={"ok": True}),
            admin_checker=self.admins,
            goals=self.goals,
            audit=self.audit,
        )
        self.assertEqual(resp.goal.state, GoalState.completed)

    def test_completed_goal_rejects_new_contribution(self) -> None:
        goal = self._create_approved_goal(target=Decimal("1"))
        register_confirmed_contribution(
            RegisterConfirmedContributionRequest(
                goal_id=goal.id,
                user_id=50,
                payment_session_id="ps1",
                amount=Decimal("1"),
                currency="TON",
                tx_hash="tx7",
            ),
            goals=self.goals,
            contributions=self.contributions,
            audit=self.audit,
        )
        complete_goal(
            CompleteGoalRequest(chat_id=1, actor_user_id=999, goal_id=goal.id),
            admin_checker=self.admins,
            goals=self.goals,
            audit=self.audit,
        )
        with self.assertRaises(GoalAlreadyCompletedError):
            register_confirmed_contribution(
                RegisterConfirmedContributionRequest(
                    goal_id=goal.id,
                    user_id=50,
                    payment_session_id="ps2",
                    amount=Decimal("1"),
                    currency="TON",
                    tx_hash="tx8",
                ),
                goals=self.goals,
                contributions=self.contributions,
                audit=self.audit,
            )

    def test_cancellation_rules_work(self) -> None:
        goal = self._create_approved_goal(target=Decimal("1"))
        cancel_goal(
            CancelGoalRequest(chat_id=1, actor_user_id=999, goal_id=goal.id),
            admin_checker=self.admins,
            goals=self.goals,
            audit=self.audit,
        )
        goal = self.goals.find_by_id(goal.id)
        self.assertEqual(goal.state, GoalState.cancelled)
        with self.assertRaises(GoalAlreadyCancelledError):
            cancel_goal(
                CancelGoalRequest(chat_id=1, actor_user_id=999, goal_id=goal.id),
                admin_checker=self.admins,
                goals=self.goals,
                audit=self.audit,
            )

    def test_duplicate_tx_hash_rejected(self) -> None:
        goal = self._create_approved_goal(target=Decimal("10"))
        register_confirmed_contribution(
            RegisterConfirmedContributionRequest(
                goal_id=goal.id,
                user_id=50,
                payment_session_id="ps1",
                amount=Decimal("1"),
                currency="TON",
                tx_hash="tx9",
            ),
            goals=self.goals,
            contributions=self.contributions,
            audit=self.audit,
        )
        with self.assertRaises(DuplicateContributionError):
            register_confirmed_contribution(
                RegisterConfirmedContributionRequest(
                    goal_id=goal.id,
                    user_id=51,
                    payment_session_id="ps2",
                    amount=Decimal("1"),
                    currency="TON",
                    tx_hash="tx9",
                ),
                goals=self.goals,
                contributions=self.contributions,
                audit=self.audit,
            )

    def test_summary_returns_multiple_goals_correctly(self) -> None:
        g1 = self._create_approved_goal(target=Decimal("5"))
        g2 = self._create_approved_goal(target=Decimal("10"))
        register_confirmed_contribution(
            RegisterConfirmedContributionRequest(
                goal_id=g1.id,
                user_id=50,
                payment_session_id="ps1",
                amount=Decimal("2"),
                currency="TON",
                tx_hash="tx10",
            ),
            goals=self.goals,
            contributions=self.contributions,
            audit=self.audit,
        )
        summary = get_chat_goal_summary(1, goals=self.goals, contributions=self.contributions).summary
        self.assertEqual(summary.active_goals_count, 2)
        self.assertEqual(len(summary.goals), 2)
        self.assertEqual(summary.total_collected_amount, Decimal("2"))


if __name__ == "__main__":
    unittest.main()

