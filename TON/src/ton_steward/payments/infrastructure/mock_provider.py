from __future__ import annotations

from ton_steward.payments.domain.models import PaymentSession
from ton_steward.payments.ports.interfaces import PaymentProvider


class MockPaymentProvider(PaymentProvider):
    def __init__(self, should_fail: bool = False) -> None:
        self.should_fail = should_fail

    def check_transaction(self, *, tx_hash: str, expected_amount: float, expected_currency: str) -> bool:
        # In mock, any non-empty tx_hash starting with '0x' is valid unless should_fail is True
        if self.should_fail:
            return False
        return bool(tx_hash and tx_hash.startswith("0x"))

    def get_payment_link(self, *, session: PaymentSession) -> str:
        # Mock TON payment link
        return f"ton://transfer/mock_wallet?amount={session.amount}&text=steward_{session.id}"
