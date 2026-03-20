from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal

from ton_steward.payments.domain.enums import PaymentSessionStatus


@dataclass(slots=True)
class PaymentSession:
    id: str  # unique session reference
    goal_id: int
    user_id: int
    chat_id: int
    
    amount: Decimal
    currency: str
    
    status: PaymentSessionStatus
    
    tx_hash: str | None = None
    
    expires_at: dt.datetime | None = None
    confirmed_at: dt.datetime | None = None
    created_at: dt.datetime | None = None
    updated_at: dt.datetime | None = None

    def is_expired(self, now: dt.datetime) -> bool:
        return (
            self.status == PaymentSessionStatus.pending 
            and self.expires_at is not None 
            and self.expires_at < now
        )
