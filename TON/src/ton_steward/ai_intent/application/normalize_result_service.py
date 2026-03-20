from __future__ import annotations

from ton_steward.ai_intent.domain.analysis_result import IntentAnalysisResult
from ton_steward.ai_intent.domain.intent_types import CurrencyType


def normalize_analysis_result(res: IntentAnalysisResult) -> IntentAnalysisResult:
    """
    Cleans up the raw extraction:
    - Clamps confidence to [0.0, 1.0]
    - Normalizes empty/whitespace strings to None
    - Ensures currency is TON if amount is present and currency is missing
    """
    conf = max(0.0, min(1.0, float(res.confidence or 0.0)))

    def _clean(s: str | None) -> str | None:
        if s is None:
            return None
        stripped = s.strip()
        return stripped if stripped else None

    title = _clean(res.goal_title)
    desc = _clean(res.goal_description)
    deadline_text = _clean(res.deadline_text)
    deadline_iso = _clean(res.deadline_iso)
    ref = _clean(res.target_goal_reference)

    amount = res.target_amount
    if amount is not None and amount < 0:
        amount = None

    currency = res.currency
    if amount is not None and currency is None:
        currency = CurrencyType.TON

    return IntentAnalysisResult(
        intent_type=res.intent_type,
        confidence=conf,
        goal_title=title,
        goal_description=desc,
        target_amount=amount,
        currency=currency,
        deadline_text=deadline_text,
        deadline_iso=deadline_iso,
        target_goal_reference=ref,
        reasoning_summary=res.reasoning_summary,
        raw=res.raw,
    )
