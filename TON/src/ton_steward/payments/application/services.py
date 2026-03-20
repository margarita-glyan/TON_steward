from __future__ import annotations

import datetime as dt
from decimal import Decimal

from ton_steward.fundraising.application.services import register_confirmed_contribution
from ton_steward.fundraising.dto.requests import RegisterConfirmedContributionRequest
from ton_steward.fundraising.ports.repositories import AuditLogger, ContributionRepository, GoalRepository
from ton_steward.payments.domain.enums import PaymentSessionStatus
from ton_steward.payments.domain.models import PaymentSession
from ton_steward.payments.ports.interfaces import PaymentProvider, PaymentRepository


def _now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def create_payment_session(
    *,
    goal_id: int,
    user_id: int,
    chat_id: int,
    amount: Decimal,
    currency: str = "TON",
    ttl_minutes: int = 60,
    repository: PaymentRepository,
    provider: PaymentProvider,
    audit: AuditLogger,
) -> tuple[PaymentSession, str]:
    """
    Returns session and payment link.
    """
    now = _now_utc()
    session_id = repository.next_id()
    expires_at = now + dt.timedelta(minutes=ttl_minutes)
    
    session = PaymentSession(
        id=session_id,
        goal_id=goal_id,
        user_id=user_id,
        chat_id=chat_id,
        amount=amount,
        currency=currency,
        status=PaymentSessionStatus.pending,
        expires_at=expires_at,
        created_at=now,
        updated_at=now,
    )
    repository.save(session)
    
    pay_link = provider.get_payment_link(session=session)
    
    audit.emit(
        entity_type="PaymentSession",
        entity_id=session.id,
        actor_user_id=user_id,
        action_type="create_session",
        previous_values=None,
        new_values={
            "goal_id": goal_id,
            "amount": str(amount),
            "expires_at": expires_at.isoformat(),
        },
        created_at=now,
    )
    
    return session, pay_link


def confirm_payment(
    *,
    session_id: str,
    tx_hash: str,
    repository: PaymentRepository,
    provider: PaymentProvider,
    # Fundraising Core dependencies to handoff
    goals: GoalRepository,
    contributions: ContributionRepository,
    audit: AuditLogger,
) -> PaymentSession:
    now = _now_utc()
    session = repository.find_by_id(session_id)
    if not session:
        raise ValueError("session not found")
        
    if session.status != PaymentSessionStatus.pending:
        raise ValueError(f"session is already {session.status.value}")
        
    if session.is_expired(now):
        session.status = PaymentSessionStatus.expired
        session.updated_at = now
        repository.update(session)
        raise ValueError("session expired")

    # Verify on-chain (or mock)
    is_valid = provider.check_transaction(
        tx_hash=tx_hash,
        expected_amount=float(session.amount),
        expected_currency=session.currency
    )
    
    if not is_valid:
        raise ValueError("transaction verification failed")

    # Update session
    session.status = PaymentSessionStatus.confirmed
    session.tx_hash = tx_hash
    session.confirmed_at = now
    session.updated_at = now
    repository.update(session)
    
    # Handoff to Fundraising Core
    register_confirmed_contribution(
        RegisterConfirmedContributionRequest(
            goal_id=session.goal_id,
            user_id=session.user_id,
            payment_session_id=session.id,
            amount=session.amount,
            currency=session.currency,
            tx_hash=tx_hash,
            confirmed_at=now
        ),
        goals=goals,
        contributions=contributions,
        audit=audit
    )
    
    audit.emit(
        entity_type="PaymentSession",
        entity_id=session.id,
        actor_user_id=None,
        action_type="confirm_payment",
        previous_values={"status": "pending"},
        new_values={"status": "confirmed", "tx_hash": tx_hash},
        created_at=now,
    )
    
    return session


def expire_old_sessions(
    *,
    repository: PaymentRepository,
    audit: AuditLogger,
) -> int:
    now = _now_utc()
    expired = repository.list_expired(now)
    count = 0
    for s in expired:
        s.status = PaymentSessionStatus.expired
        s.updated_at = now
        repository.update(s)
        count += 1
        audit.emit(
            entity_type="PaymentSession",
            entity_id=s.id,
            actor_user_id=None,
            action_type="expire_session",
            previous_values={"status": "pending"},
            new_values={"status": "expired"},
            created_at=now,
        )
    return count
