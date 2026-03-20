from __future__ import annotations

import datetime as dt
from decimal import Decimal

from ton_steward.fundraising.domain.enums import ContributionStatus, GoalDraftStatus, GoalState
from ton_steward.fundraising.domain.errors import (
    DraftNotReviewableError,
    DuplicateContributionError,
    GoalAlreadyCancelledError,
    GoalAlreadyCompletedError,
    GoalDraftNotFoundError,
    GoalNotFoundError,
    InvalidContributionError,
    GoalNotPayableError,
    NoPermissionError,
)
from ton_steward.fundraising.domain.models import Contribution, Goal, GoalDraft, GoalSummary, GoalSummaryItem
from ton_steward.fundraising.domain.state_machine import is_payable, transition_or_throw
from ton_steward.fundraising.dto.requests import (
    ApproveGoalDraftRequest,
    CancelGoalRequest,
    CompleteGoalRequest,
    CreateGoalDraftRequest,
    EditGoalDraftRequest,
    RegisterConfirmedContributionRequest,
    RejectGoalDraftRequest,
)
from ton_steward.fundraising.dto.responses import (
    ApproveGoalDraftResponse,
    CancelGoalResponse,
    ChatSummaryResponse,
    CompleteGoalResponse,
    CreateGoalDraftResponse,
    EditGoalDraftResponse,
    RegisterContributionResponse,
    RejectGoalDraftResponse,
)
from ton_steward.fundraising.ports.repositories import (
    AdminChecker,
    AuditLogger,
    ContributionRepository,
    GoalDraftRepository,
    GoalRepository,
)


def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _require_admin(admin_checker: AdminChecker, *, chat_id: int, actor_user_id: int) -> None:
    if not admin_checker.is_admin(chat_id=chat_id, user_id=actor_user_id):
        raise NoPermissionError("only admins can perform this action")


def create_goal_draft(
    req: CreateGoalDraftRequest,
    *,
    drafts: GoalDraftRepository,
    audit: AuditLogger,
) -> CreateGoalDraftResponse:
    now = _now_utc()
    draft_id = drafts.next_id()

    draft = GoalDraft(
        id=draft_id,
        chat_id=req.chat_id,
        created_by_user_id=req.created_by_user_id,
        source_message_id=req.source_message_id,
        title=req.title,
        description=req.description,
        target_amount=req.target_amount,
        currency=req.currency,
        deadline_at=req.deadline_at,
        status=GoalDraftStatus.pending_admin_review,
        created_at=now,
        updated_at=now,
    )
    drafts.save(draft)

    audit.emit(
        entity_type="GoalDraft",
        entity_id=str(draft.id),
        actor_user_id=req.created_by_user_id,
        action_type="create",
        previous_values=None,
        new_values={
            "chat_id": draft.chat_id,
            "title": draft.title,
            "target_amount": str(draft.target_amount) if draft.target_amount is not None else None,
        },
        created_at=now,
    )
    return CreateGoalDraftResponse(draft=draft)


def approve_goal_draft(
    req: ApproveGoalDraftRequest,
    *,
    admin_checker: AdminChecker,
    drafts: GoalDraftRepository,
    goals: GoalRepository,
    audit: AuditLogger,
) -> ApproveGoalDraftResponse:
    _require_admin(admin_checker, chat_id=req.chat_id, actor_user_id=req.actor_user_id)
    
    draft = drafts.find_by_id(req.draft_id)
    if draft is None or draft.chat_id != req.chat_id:
        raise GoalDraftNotFoundError("draft not found")
        
    if draft.status != GoalDraftStatus.pending_admin_review:
        raise DraftNotReviewableError(f"draft is in state {draft.status}")

    # Validation: title and target amount required for approved goal
    if not draft.title:
        raise InvalidContributionError("title is required to approve a goal")
    if draft.target_amount is None or draft.target_amount <= Decimal("0"):
        raise InvalidContributionError("positive target amount is required to approve a goal")
        
    now = _now_utc()
    wallet = req.wallet_address or draft.wallet_address or "TBD" # In MVP we might allow TBD or require it

    draft.status = GoalDraftStatus.approved_converted
    draft.updated_at = now
    drafts.update(draft)

    goal_id = goals.next_id()
    goal = Goal(
        id=goal_id,
        chat_id=draft.chat_id,
        created_from_draft_id=draft.id,
        title=draft.title,
        description=draft.description,
        target_amount=draft.target_amount,
        currency=draft.currency or "TON",
        deadline_at=draft.deadline_at,
        wallet_address=wallet,
        state=GoalState.approved,
        created_by_user_id=draft.created_by_user_id,
        approved_by_user_id=req.actor_user_id,
        approved_at=now,
        created_at=now,
        updated_at=now,
    )
    goals.save(goal)

    audit.emit(
        entity_type="Goal",
        entity_id=str(goal.id),
        actor_user_id=req.actor_user_id,
        action_type="approve_from_draft",
        previous_values=None,
        new_values={"draft_id": draft.id, "state": goal.state.value},
        created_at=now,
    )
    
    return ApproveGoalDraftResponse(draft=draft, goal=goal)


def edit_goal_draft(
    req: EditGoalDraftRequest,
    *,
    admin_checker: AdminChecker,
    drafts: GoalDraftRepository,
    audit: AuditLogger,
) -> EditGoalDraftResponse:
    _require_admin(admin_checker, chat_id=req.chat_id, actor_user_id=req.actor_user_id)
    
    draft = drafts.find_by_id(req.draft_id)
    if draft is None or draft.chat_id != req.chat_id:
        raise GoalDraftNotFoundError()

    now = _now_utc()
    # Logic to update fields if provided
    if req.title: draft.title = req.title
    if req.description: draft.description = req.description
    if req.target_amount: draft.target_amount = req.target_amount
    if req.currency: draft.currency = req.currency
    if req.deadline_at: draft.deadline_at = req.deadline_at
    if req.wallet_address: draft.wallet_address = req.wallet_address

    draft.updated_at = now
    drafts.update(draft)
    
    return EditGoalDraftResponse(draft=draft)


def reject_goal_draft(
    req: RejectGoalDraftRequest,
    *,
    admin_checker: AdminChecker,
    drafts: GoalDraftRepository,
    audit: AuditLogger,
) -> RejectGoalDraftResponse:
    _require_admin(admin_checker, chat_id=req.chat_id, actor_user_id=req.actor_user_id)
    
    draft = drafts.find_by_id(req.draft_id)
    if draft is None or draft.chat_id != req.chat_id:
        raise GoalDraftNotFoundError()

    now = _now_utc()
    draft.status = GoalDraftStatus.rejected
    draft.updated_at = now
    drafts.update(draft)
    
    return RejectGoalDraftResponse(draft=draft)


def register_confirmed_contribution(
    req: RegisterConfirmedContributionRequest,
    *,
    goals: GoalRepository,
    contributions: ContributionRepository,
    audit: AuditLogger,
) -> RegisterContributionResponse:
    goal = goals.find_by_id(req.goal_id)
    if not goal:
        raise GoalNotFoundError()

    if not is_payable(goal.state):
        raise GoalNotPayableError(f"Goal in state {goal.state} cannot accept contributions")

    if contributions.exists_by_tx_hash(req.tx_hash):
        raise DuplicateContributionError(f"tx_hash {req.tx_hash} already exists")

    now = _now_utc()
    contribution = Contribution(
        id=contributions.next_id(),
        goal_id=goal.id,
        user_id=req.user_id,
        payment_session_id=req.payment_session_id,
        amount=req.amount,
        currency=req.currency,
        tx_hash=req.tx_hash,
        status=ContributionStatus.confirmed,
        confirmed_at=req.confirmed_at or now,
        created_at=now,
    )
    contributions.save(contribution)

    # State update logic
    old_state = goal.state
    goal.collected_amount += contribution.amount
    
    transition = None
    if old_state == GoalState.approved:
        transition_or_throw(goal, GoalState.funding)
        transition = (old_state, GoalState.funding)
        
    if goal.collected_amount >= goal.target_amount and goal.state != GoalState.funded:
        prev = goal.state
        transition_or_throw(goal, GoalState.funded)
        transition = (prev, GoalState.funded)

    goal.updated_at = now
    goals.update(goal)

    return RegisterContributionResponse(contribution=contribution, goal=goal, state_transition=transition)


def cancel_goal(
    req: CancelGoalRequest,
    *,
    admin_checker: AdminChecker,
    goals: GoalRepository,
    audit: AuditLogger,
) -> CancelGoalResponse:
    _require_admin(admin_checker, chat_id=req.chat_id, actor_user_id=req.actor_user_id)
    
    goal = goals.find_by_id(req.goal_id)
    if not goal or goal.chat_id != req.chat_id:
        raise GoalNotFoundError()

    transition_or_throw(goal, GoalState.cancelled)
    goal.cancelled_at = _now_utc()
    goals.update(goal)
    
    return CancelGoalResponse(goal=goal)


def complete_goal(
    req: CompleteGoalRequest,
    *,
    admin_checker: AdminChecker,
    goals: GoalRepository,
    audit: AuditLogger,
) -> CompleteGoalResponse:
    _require_admin(admin_checker, chat_id=req.chat_id, actor_user_id=req.actor_user_id)
    
    goal = goals.find_by_id(req.goal_id)
    if not goal or goal.chat_id != req.chat_id:
        raise GoalNotFoundError()

    transition_or_throw(goal, GoalState.completed)
    goal.completed_at = _now_utc()
    goals.update(goal)
    
    return CompleteGoalResponse(goal=goal)


def get_chat_goal_summary(
    chat_id: int,
    *,
    goals: GoalRepository,
    contributions: ContributionRepository,
) -> ChatSummaryResponse:
    all_goals = goals.list_by_chat_id(chat_id)
    now = _now_utc()
    
    items = []
    active_count = 0
    funded_count = 0
    completed_count = 0
    total_target = Decimal("0")
    total_collected = Decimal("0")

    for g in all_goals:
        # Optimization: in real app, contributions might be pre-joined or cached
        # Here we use the repository sum
        collected = contributions.sum_confirmed_by_goal_id(g.id)
        contributors = contributions.count_confirmed_contributors_by_goal_id(g.id)
        
        percent = int((collected / g.target_amount * 100)) if g.target_amount > 0 else 0
        overdue = bool(g.deadline_at and g.deadline_at < now and g.state in {GoalState.approved, GoalState.funding})

        items.append(GoalSummaryItem(
            goal_id=g.id,
            title=g.title,
            state=g.state,
            target_amount=g.target_amount,
            collected_amount=collected,
            currency=g.currency,
            percent_funded=percent,
            deadline_at=g.deadline_at,
            overdue=overdue,
            contributors_count=contributors
        ))
        
        total_target += g.target_amount
        total_collected += collected
        
        if g.state in {GoalState.approved, GoalState.funding, GoalState.funded}: active_count += 1
        if g.state == GoalState.funded: funded_count += 1
        if g.state == GoalState.completed: completed_count += 1

    summary = GoalSummary(
        chat_id=chat_id,
        active_goals_count=active_count,
        funded_goals_count=funded_count,
        completed_goals_count=completed_count,
        total_target_amount=total_target,
        total_collected_amount=total_collected,
        goals=items
    )
    
    return ChatSummaryResponse(summary=summary)
