from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import Session

from ton_steward.core.audit import AuditWriter
from ton_steward.core.serialize import pick_dict
from ton_steward.db.enums import AuditAction, DraftStatus, GoalStatus
from ton_steward.db.models import AdminRole, Goal, GoalDraft


ReviewAction = Literal["approve", "edit", "reject"]


@dataclass(frozen=True, slots=True)
class ReviewCommand:
    draft_id: int
    admin_user_id: int
    chat_id: int
    action: ReviewAction

    # Optional edits
    title: str | None = None
    description: str | None = None
    target_amount: str | None = None
    deadline: dt.datetime | None = None
    wallet_address: str | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class ReviewResult:
    ok: bool
    error_code: str | None = None
    message: str | None = None
    draft_id: int | None = None
    goal_id: int | None = None


class AdminReviewService:
    def __init__(self, session: Session, audit: AuditWriter):
        self.session = session
        self.audit = audit

    def _is_admin(self, chat_id: int, user_id: int) -> bool:
        stmt = (
            select(AdminRole)
            .where(
                AdminRole.chat_id == chat_id,
                AdminRole.user_id == user_id,
                AdminRole.is_active.is_(True),
            )
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none() is not None

    def handle(self, cmd: ReviewCommand) -> ReviewResult:
        if not self._is_admin(cmd.chat_id, cmd.admin_user_id):
            return ReviewResult(
                ok=False,
                error_code="no_permission",
                message="only admins can review fundraising drafts",
                draft_id=cmd.draft_id,
            )

        draft = self.session.get(GoalDraft, cmd.draft_id)
        if draft is None or draft.chat_id != cmd.chat_id:
            return ReviewResult(
                ok=False,
                error_code="draft_not_found",
                message="draft not found for this chat",
            )

        if draft.status in {DraftStatus.approved, DraftStatus.rejected}:
            return ReviewResult(
                ok=False,
                error_code="draft_terminal",
                message="draft is already in a terminal state",
                draft_id=draft.id,
            )

        match cmd.action:
            case "edit":
                return self._handle_edit(cmd, draft)
            case "approve":
                return self._handle_approve(cmd, draft)
            case "reject":
                return self._handle_reject(cmd, draft)
            case _:
                return ReviewResult(ok=False, error_code="unsupported_action", message="unsupported review action")

    def _handle_edit(self, cmd: ReviewCommand, draft: GoalDraft) -> ReviewResult:
        editable_fields = ["title", "description", "target_amount", "deadline", "wallet_address"]

        previous = pick_dict(draft, editable_fields)
        updated: dict[str, Any] = {}

        if cmd.title is not None:
            draft.title = cmd.title
            updated["title"] = cmd.title
        if cmd.description is not None:
            draft.description = cmd.description
            updated["description"] = cmd.description
        if cmd.target_amount is not None:
            draft.target_amount = cmd.target_amount
            updated["target_amount"] = cmd.target_amount
        if cmd.deadline is not None:
            draft.deadline = cmd.deadline
            updated["deadline"] = cmd.deadline.isoformat()
        if cmd.wallet_address is not None:
            draft.wallet_address = cmd.wallet_address
            updated["wallet_address"] = cmd.wallet_address

        if not updated:
            return ReviewResult(ok=True, draft_id=draft.id, message="no_changes")

        # Keep status as proposed (pending_admin_review semantics).
        self.audit.log(
            chat_id=draft.chat_id,
            actor_user_id=cmd.admin_user_id,
            entity_type="GoalDraft",
            entity_id=str(draft.id),
            action=AuditAction.update,
            old_value=previous,
            new_value=pick_dict(draft, editable_fields),
            reason=cmd.note,
            source="admin_review",
        )
        return ReviewResult(ok=True, draft_id=draft.id, message="draft_edited")

    def _handle_approve(self, cmd: ReviewCommand, draft: GoalDraft) -> ReviewResult:
        # Safety: require wallet address
        wallet_address = cmd.wallet_address or draft.wallet_address
        if not wallet_address:
            return ReviewResult(
                ok=False,
                error_code="wallet_required",
                message="wallet_address must be set before approval",
                draft_id=draft.id,
            )

        draft.status = DraftStatus.approved
        draft.decided_by_admin_user_id = cmd.admin_user_id
        draft.decided_at = dt.datetime.utcnow()
        if cmd.note:
            draft.decision_note = cmd.note

        goal = Goal(
            chat_id=draft.chat_id,
            title=draft.title,
            description=draft.description,
            target_amount=draft.target_amount,
            collected_amount="0",
            deadline=draft.deadline,
            status=GoalStatus.approved,
            created_by_user_id=draft.created_by_user_id,
            approved_by_user_id=cmd.admin_user_id,
            wallet_address=wallet_address,
        )
        self.session.add(goal)
        self.session.flush()

        # Audit draft approval
        self.audit.log(
            chat_id=draft.chat_id,
            actor_user_id=cmd.admin_user_id,
            entity_type="GoalDraft",
            entity_id=str(draft.id),
            action=AuditAction.admin_decision,
            old_value={"status": DraftStatus.proposed.value},
            new_value={"status": DraftStatus.approved.value, "goal_id": goal.id},
            reason=cmd.note or "approve_draft",
            source="admin_review",
        )

        # Audit goal creation
        self.audit.log(
            chat_id=goal.chat_id,
            actor_user_id=cmd.admin_user_id,
            entity_type="Goal",
            entity_id=str(goal.id),
            action=AuditAction.create,
            old_value=None,
            new_value={
                "title": goal.title,
                "target_amount": goal.target_amount,
                "deadline": goal.deadline.isoformat() if goal.deadline else None,
                "wallet_address": goal.wallet_address,
                "status": goal.status.value,
            },
            reason="goal_created_from_draft",
            source="admin_review",
        )

        return ReviewResult(ok=True, draft_id=draft.id, goal_id=goal.id, message="draft_approved")

    def _handle_reject(self, cmd: ReviewCommand, draft: GoalDraft) -> ReviewResult:
        draft.status = DraftStatus.rejected
        draft.decided_by_admin_user_id = cmd.admin_user_id
        draft.decided_at = dt.datetime.utcnow()
        if cmd.note:
            draft.decision_note = cmd.note

        self.audit.log(
            chat_id=draft.chat_id,
            actor_user_id=cmd.admin_user_id,
            entity_type="GoalDraft",
            entity_id=str(draft.id),
            action=AuditAction.admin_decision,
            old_value={"status": DraftStatus.proposed.value},
            new_value={"status": DraftStatus.rejected.value},
            reason=cmd.note or "reject_draft",
            source="admin_review",
        )
        return ReviewResult(ok=True, draft_id=draft.id, message="draft_rejected")

