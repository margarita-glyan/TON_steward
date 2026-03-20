from __future__ import annotations

from ton_steward.ai_intent.infrastructure.heuristic_prefilter import prefilter
from ton_steward.ai_intent.dto.responses import RelevancePrefilterResult


def prefilter_message(text: str) -> RelevancePrefilterResult:
    """
    Application-level service for heuristic prefiltering.
    """
    is_relevant, signals = prefilter(text)
    return RelevancePrefilterResult(
        is_relevant=is_relevant,
        matched_signals=signals.matched_signals,
        maybe_intent_candidates=signals.maybe_intent_candidates
    )
