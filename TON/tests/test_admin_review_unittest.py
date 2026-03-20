import os
import sys
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(REPO_ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from ton_steward.core.admin_review.service import AdminReviewService, ReviewCommand  # noqa: E402
from ton_steward.core.audit import AuditWriter  # noqa: E402
from ton_steward.db import AdminRole, AuditLog, Base, Chat, Goal, GoalDraft, User  # noqa: E402
from ton_steward.db.enums import DraftStatus  # noqa: E402


class TestAdminReview(unittest.TestCase):
    def setUp(self) -> None:
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(engine)
        self.SessionLocal = sessionmaker(bind=engine, future=True)

        self.session: Session = self.SessionLocal()
        self.audit = AuditWriter(self.session)
        self.service = AdminReviewService(self.session, self.audit)

        # Seed chat, users, admin role, and draft
        self.chat = Chat(id=1, type="group", title="Test", username=None)
        self.admin_user = User(id=100, is_bot=False, first_name="Admin")
        self.normal_user = User(id=200, is_bot=False, first_name="User")
        self.session.add_all([self.chat, self.admin_user, self.normal_user])
        self.session.flush()

        self.session.add(AdminRole(chat_id=self.chat.id, user_id=self.admin_user.id, is_active=True))

        self.draft = GoalDraft(
            chat_id=self.chat.id,
            created_by_user_id=self.normal_user.id,
            source_message_id=10,
            source_text="Let's fund cameras",
            title="Entrance cameras",
            description="Collect funds for security cameras",
            target_amount="500",
            deadline=None,
            ai_confidence=0.9,
        )
        self.session.add(self.draft)
        self.session.commit()

    def tearDown(self) -> None:
        self.session.close()

    def test_non_admin_cannot_review(self) -> None:
        cmd = ReviewCommand(
            draft_id=self.draft.id,
            admin_user_id=self.normal_user.id,
            chat_id=self.chat.id,
            action="approve",
            wallet_address="wallet",
        )
        result = self.service.handle(cmd)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "no_permission")

    def test_admin_can_edit_draft(self) -> None:
        cmd = ReviewCommand(
            draft_id=self.draft.id,
            admin_user_id=self.admin_user.id,
            chat_id=self.chat.id,
            action="edit",
            title="Updated title",
            wallet_address="wallet123",
        )
        result = self.service.handle(cmd)
        self.assertTrue(result.ok)
        self.session.refresh(self.draft)
        self.assertEqual(self.draft.title, "Updated title")
        self.assertEqual(self.draft.wallet_address, "wallet123")

        # Audit record created
        audit_entries = self.session.query(AuditLog).all()
        self.assertGreaterEqual(len(audit_entries), 1)

    def test_approve_creates_goal_and_audit(self) -> None:
        # Set wallet on draft first
        self.draft.wallet_address = "wallet123"
        self.session.commit()

        cmd = ReviewCommand(
            draft_id=self.draft.id,
            admin_user_id=self.admin_user.id,
            chat_id=self.chat.id,
            action="approve",
        )
        result = self.service.handle(cmd)
        self.assertTrue(result.ok)
        self.assertIsNotNone(result.goal_id)

        goal = self.session.query(Goal).filter_by(id=result.goal_id).one()
        self.assertEqual(goal.wallet_address, "wallet123")

        # Draft moved to approved
        self.session.refresh(self.draft)
        self.assertEqual(self.draft.status, DraftStatus.approved)

        # Audit logs for draft + goal
        entries = self.session.query(AuditLog).all()
        self.assertGreaterEqual(len(entries), 2)

    def test_reject_marks_draft_rejected(self) -> None:
        cmd = ReviewCommand(
            draft_id=self.draft.id,
            admin_user_id=self.admin_user.id,
            chat_id=self.chat.id,
            action="reject",
            note="not appropriate",
        )
        result = self.service.handle(cmd)
        self.assertTrue(result.ok)
        self.session.refresh(self.draft)
        self.assertEqual(self.draft.status, DraftStatus.rejected)

    def test_cannot_approve_rejected_draft(self) -> None:
        # First reject
        self.draft.status = DraftStatus.rejected
        self.session.commit()

        cmd = ReviewCommand(
            draft_id=self.draft.id,
            admin_user_id=self.admin_user.id,
            chat_id=self.chat.id,
            action="approve",
            wallet_address="wallet",
        )
        result = self.service.handle(cmd)
        self.assertFalse(result.ok)
        self.assertEqual(result.error_code, "draft_terminal")


if __name__ == "__main__":
    unittest.main()

