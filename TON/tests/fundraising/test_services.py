from __future__ import annotations

import pytest
import datetime as dt
from decimal import Decimal
from typing import Dict, List, Any

from ton_steward.fundraising.domain.enums import GoalDraftStatus, GoalState, ContributionStatus
from ton_steward.fundraising.domain.errors import (
    NoPermissionError, DuplicateContributionError, GoalNotPayableError,
    GoalNotFoundError, GoalDraftNotFoundError
)
from ton_steward.fundraising.domain.models import GoalDraft, Goal, Contribution
from ton_steward.fundraising.dto.requests import (
    CreateGoalDraftRequest, ApproveGoalDraftRequest, RejectGoalDraftRequest,
    RegisterConfirmedContributionRequest, CancelGoalRequest, CompleteGoalRequest
)
from ton_steward.fundraising.application.services import (
    create_goal_draft, approve_goal_draft, reject_goal_draft,
    register_confirmed_contribution, cancel_goal, complete_goal,
    get_chat_goal_summary
)

# --- Mocks ---

class MockGoalDraftRepo:
    def __init__(self):
        self.data: Dict[int, GoalDraft] = {}
        self.counter = 1
    def next_id(self) -> int:
        res = self.counter
        self.counter += 1
        return res
    def find_by_id(self, id: int): return self.data.get(id)
    def save(self, d): self.data[d.id] = d
    def update(self, d): self.data[d.id] = d

class MockGoalRepo:
    def __init__(self):
        self.data: Dict[int, Goal] = {}
        self.counter = 1
    def next_id(self) -> int:
        res = self.counter
        self.counter += 1
        return res
    def find_by_id(self, id: int): return self.data.get(id)
    def save(self, g): self.data[g.id] = g
    def update(self, g): self.data[g.id] = g
    def list_by_chat_id(self, chat_id: int):
        return [g for g in self.data.values() if g.chat_id == chat_id]

class MockContributionRepo:
    def __init__(self):
        self.data: List[Contribution] = []
        self.counter = 1
    def next_id(self) -> int:
        res = self.counter
        self.counter += 1
        return res
    def exists_by_tx_hash(self, tx_hash: str):
        return any(c.tx_hash == tx_hash for c in self.data)
    def save(self, c): self.data.append(c)
    def sum_confirmed_by_goal_id(self, goal_id: int):
        return sum((c.amount for c in self.data if c.goal_id == goal_id), Decimal("0"))
    def count_confirmed_contributors_by_goal_id(self, goal_id: int):
        return len(set(c.user_id for c in self.data if c.goal_id == goal_id))

class MockAdminChecker:
    def __init__(self, admins: List[int]): self.admins = admins
    def is_admin(self, chat_id, user_id): return user_id in self.admins

class MockAuditLogger:
    def emit(self, **kwargs): pass

# --- Fixtures ---

@pytest.fixture
def ctx():
    return {
        "drafts": MockGoalDraftRepo(),
        "goals": MockGoalRepo(),
        "contributions": MockContributionRepo(),
        "admin_checker": MockAdminChecker(admins=[100]),
        "audit": MockAuditLogger()
    }

# --- Tests ---

def test_create_draft(ctx):
    req = CreateGoalDraftRequest(chat_id=1, created_by_user_id=1, title="Test Goal", target_amount=Decimal("10"))
    res = create_goal_draft(req, drafts=ctx["drafts"], audit=ctx["audit"])
    
    assert res.draft.title == "Test Goal"
    assert res.draft.status == GoalDraftStatus.pending_admin_review
    assert ctx["drafts"].find_by_id(res.draft.id) is not None

def test_approve_draft_by_admin(ctx):
    draft = GoalDraft(id=1, chat_id=1, created_by_user_id=1, title="Goal", description=None, target_amount=Decimal("100"), status=GoalDraftStatus.pending_admin_review)
    ctx["drafts"].save(draft)
    
    req = ApproveGoalDraftRequest(chat_id=1, draft_id=1, actor_user_id=100, wallet_address="ADDR")
    res = approve_goal_draft(req, admin_checker=ctx["admin_checker"], drafts=ctx["drafts"], goals=ctx["goals"], audit=ctx["audit"])
    
    assert res.goal.title == "Goal"
    assert res.goal.state == GoalState.approved
    assert res.draft.status == GoalDraftStatus.approved_converted

def test_approve_draft_non_admin_fails(ctx):
    draft = GoalDraft(id=1, chat_id=1, created_by_user_id=1, title="Goal", description=None, target_amount=Decimal("100"), status=GoalDraftStatus.pending_admin_review)
    ctx["drafts"].save(draft)
    
    req = ApproveGoalDraftRequest(chat_id=1, draft_id=1, actor_user_id=999)
    with pytest.raises(NoPermissionError):
        approve_goal_draft(req, admin_checker=ctx["admin_checker"], drafts=ctx["drafts"], goals=ctx["goals"], audit=ctx["audit"])

def test_register_contribution_and_state_transition(ctx):
    goal = Goal(id=1, chat_id=1, created_from_draft_id=1, created_by_user_id=1, approved_by_user_id=100, 
                title="Goal", description=None, target_amount=Decimal("100"), 
                collected_amount=Decimal("0"), wallet_address="ADDR", state=GoalState.approved)
    ctx["goals"].save(goal)
    
    # 1. First contribution (Approved -> Funding)
    req1 = RegisterConfirmedContributionRequest(goal_id=1, user_id=2, payment_session_id="S1", amount=Decimal("10"), currency="TON", tx_hash="TX1")
    res1 = register_confirmed_contribution(req1, goals=ctx["goals"], contributions=ctx["contributions"], audit=ctx["audit"])
    
    assert res1.goal.state == GoalState.funding
    assert res1.goal.collected_amount == Decimal("10")
    
    # 2. Reach target (Funding -> Funded)
    req2 = RegisterConfirmedContributionRequest(goal_id=1, user_id=3, payment_session_id="S2", amount=Decimal("90"), currency="TON", tx_hash="TX2")
    res2 = register_confirmed_contribution(req2, goals=ctx["goals"], contributions=ctx["contributions"], audit=ctx["audit"])
    
    assert res2.goal.state == GoalState.funded
    assert res2.goal.collected_amount == Decimal("100")

def test_duplicate_tx_hash_rejected(ctx):
    goal = Goal(id=1, chat_id=1, created_from_draft_id=1, created_by_user_id=1, approved_by_user_id=100, 
                title="Goal", description=None, target_amount=Decimal("100"), 
                collected_amount=Decimal("0"), wallet_address="ADDR", state=GoalState.approved)
    ctx["goals"].save(goal)
    
    req = RegisterConfirmedContributionRequest(goal_id=1, user_id=2, payment_session_id="S1", amount=Decimal("10"), currency="TON", tx_hash="TX1")
    register_confirmed_contribution(req, goals=ctx["goals"], contributions=ctx["contributions"], audit=ctx["audit"])
    
    with pytest.raises(DuplicateContributionError):
        register_confirmed_contribution(req, goals=ctx["goals"], contributions=ctx["contributions"], audit=ctx["audit"])

def test_cancel_goal(ctx):
    goal = Goal(id=1, chat_id=1, created_from_draft_id=1, created_by_user_id=1, approved_by_user_id=100, 
                title="Goal", description=None, target_amount=Decimal("100"), 
                collected_amount=Decimal("0"), wallet_address="ADDR", state=GoalState.approved)
    ctx["goals"].save(goal)
    
    cancel_goal(CancelGoalRequest(chat_id=1, goal_id=1, actor_user_id=100), admin_checker=ctx["admin_checker"], goals=ctx["goals"], audit=ctx["audit"])
    assert ctx["goals"].find_by_id(1).state == GoalState.cancelled

def test_complete_goal(ctx):
    goal = Goal(id=1, chat_id=1, created_from_draft_id=1, created_by_user_id=1, approved_by_user_id=100, 
                title="Goal", description=None, target_amount=Decimal("100"), 
                collected_amount=Decimal("100"), wallet_address="ADDR", state=GoalState.funded)
    ctx["goals"].save(goal)
    
    complete_goal(CompleteGoalRequest(chat_id=1, goal_id=1, actor_user_id=100), admin_checker=ctx["admin_checker"], goals=ctx["goals"], audit=ctx["audit"])
    assert ctx["goals"].find_by_id(1).state == GoalState.completed

def test_summary_generation(ctx):
    goal1 = Goal(id=1, chat_id=1, created_from_draft_id=1, created_by_user_id=1, approved_by_user_id=100, 
                 title="G1", description=None, target_amount=Decimal("100"), 
                 collected_amount=Decimal("0"), wallet_address="A", state=GoalState.approved)
    goal2 = Goal(id=2, chat_id=1, created_from_draft_id=2, created_by_user_id=1, approved_by_user_id=100, 
                 title="G2", description=None, target_amount=Decimal("50"), 
                 collected_amount=Decimal("0"), wallet_address="B", state=GoalState.approved)
    ctx["goals"].save(goal1)
    ctx["goals"].save(goal2)
    
    # Add contribution to G2 to match its 'funded' state
    register_confirmed_contribution(RegisterConfirmedContributionRequest(2, 2, "S2", Decimal("50"), "TON", "TX2"), 
                                    goals=ctx["goals"], contributions=ctx["contributions"], audit=ctx["audit"])
    
    # Add contribution to G1
    register_confirmed_contribution(RegisterConfirmedContributionRequest(1, 2, "S1", Decimal("20"), "TON", "TX1"), 
                                    goals=ctx["goals"], contributions=ctx["contributions"], audit=ctx["audit"])
    
    res = get_chat_goal_summary(chat_id=1, goals=ctx["goals"], contributions=ctx["contributions"])
    
    assert res.summary.active_goals_count == 2
    assert res.summary.goals[0].percent_funded == 20
    assert res.summary.goals[1].percent_funded == 100
