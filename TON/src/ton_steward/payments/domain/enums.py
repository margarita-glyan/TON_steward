from __future__ import annotations

from enum import Enum


class PaymentSessionStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    expired = "expired"
    failed = "failed"
