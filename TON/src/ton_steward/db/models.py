from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ton_steward.db.base import Base
from ton_steward.db.enums import AuditAction, DraftStatus, GoalStatus, PaymentSessionStatus, ReminderJobType


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram chat_id
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # group/supergroup/private/channel
    title: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255))

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    goals: Mapped[list["Goal"]] = relationship(back_populates="chat")
    drafts: Mapped[list["GoalDraft"]] = relationship(back_populates="chat")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram user_id
    is_bot: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    username: Mapped[str | None] = mapped_column(String(255))
    language_code: Mapped[str | None] = mapped_column(String(16))

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class AdminRole(Base):
    """
    Role mapping. Admin status is scoped per chat and should be synced from Telegram.
    """

    __tablename__ = "admin_roles"

    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    role: Mapped[str] = mapped_column(String(32), nullable=False, default="admin")  # admin/creator
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    granted_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    chat: Mapped["Chat"] = relationship()
    user: Mapped["User"] = relationship()


class GoalDraft(Base):
    __tablename__ = "goal_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    source_message_id: Mapped[int | None] = mapped_column(Integer)  # Telegram message_id
    source_text: Mapped[str] = mapped_column(Text, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    target_amount: Mapped[str] = mapped_column(String(64), nullable=False)  # store as string in TON units for MVP
    deadline: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    wallet_address: Mapped[str | None] = mapped_column(String(128))

    ai_confidence: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0)  # 0..1
    ai_raw: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    status: Mapped[DraftStatus] = mapped_column(Enum(DraftStatus), nullable=False, default=DraftStatus.proposed)
    decided_by_admin_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    decided_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))
    decision_note: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    chat: Mapped["Chat"] = relationship(back_populates="drafts")
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_user_id])
    decided_by: Mapped["User | None"] = relationship(foreign_keys=[decided_by_admin_user_id])

    __table_args__ = (
        CheckConstraint("ai_confidence >= 0 AND ai_confidence <= 1", name="ck_goal_drafts_ai_confidence"),
    )


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    target_amount: Mapped[str] = mapped_column(String(64), nullable=False)
    collected_amount: Mapped[str] = mapped_column(String(64), nullable=False, default="0")
    deadline: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

    status: Mapped[GoalStatus] = mapped_column(Enum(GoalStatus), nullable=False, default=GoalStatus.approved)
    created_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    approved_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    wallet_address: Mapped[str] = mapped_column(String(128), nullable=False)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    chat: Mapped["Chat"] = relationship(back_populates="goals")
    created_by: Mapped["User"] = relationship(foreign_keys=[created_by_user_id])
    approved_by: Mapped["User"] = relationship(foreign_keys=[approved_by_user_id])

    participants: Mapped[list["GoalParticipant"]] = relationship(back_populates="goal", cascade="all, delete-orphan")
    contributions: Mapped[list["Contribution"]] = relationship(back_populates="goal")

    __table_args__ = (
        Index("ix_goals_chat_status", "chat_id", "status"),
    )


class GoalParticipant(Base):
    __tablename__ = "goal_participants"

    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)

    role: Mapped[str] = mapped_column(String(32), nullable=False, default="supporter")
    joined_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    goal: Mapped["Goal"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship()


class Contribution(Base):
    __tablename__ = "contributions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    amount: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="TON")

    ton_tx_hash: Mapped[str | None] = mapped_column(String(128), unique=True)
    ton_from_address: Mapped[str | None] = mapped_column(String(128))
    ton_to_address: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    goal: Mapped["Goal"] = relationship(back_populates="contributions")
    user: Mapped["User"] = relationship()
    chat: Mapped["Chat"] = relationship()


class PaymentSession(Base):
    __tablename__ = "payment_sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # deterministic external id (uuid/nonce)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)

    amount: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(16), nullable=False, default="TON")

    status: Mapped[PaymentSessionStatus] = mapped_column(
        Enum(PaymentSessionStatus), nullable=False, default=PaymentSessionStatus.created
    )
    expires_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    ton_to_address: Mapped[str] = mapped_column(String(128), nullable=False)
    ton_payload: Mapped[str | None] = mapped_column(String(255))  # comment/memo for matching, if used
    ton_expected_tx_hash: Mapped[str | None] = mapped_column(String(128))
    ton_observed_tx_hash: Mapped[str | None] = mapped_column(String(128))

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_payment_sessions_user_status", "user_id", "status"),
    )


class ReminderJob(Base):
    __tablename__ = "reminder_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False, index=True)
    goal_id: Mapped[int | None] = mapped_column(ForeignKey("goals.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    type: Mapped[ReminderJobType] = mapped_column(Enum(ReminderJobType), nullable=False)
    run_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    payload: Mapped[dict[str, Any] | None] = mapped_column(JSON)

    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled")  # scheduled/running/done/failed
    last_error: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        Index("ix_reminder_jobs_status_run_at", "status", "run_at"),
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int | None] = mapped_column(ForeignKey("chats.id", ondelete="SET NULL"), index=True)
    actor_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction), nullable=False)

    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    reason: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="system")  # telegram/scheduler/api/system

    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
    )

