from __future__ import annotations

from dataclasses import replace
from ton_steward.ai_intent.domain.analysis_result import IntentAnalysisResult
from ton_steward.ai_intent.domain.intent_types import IntentType


def validate_analysis_result(res: IntentAnalysisResult) -> IntentAnalysisResult:
    """
    Ensures the result meets structural requirements for its intent type.
    Degrades to intent_type='none' if critical data is missing.
    """
    # 1. Low confidence check
    if res.confidence < 0.3:
        return replace(res, intent_type=IntentType.none)

    # 2. Required fields per intent
    if res.intent_type == IntentType.create_goal:
        # Title is non-negotiable for creation
        if not res.goal_title:
            return replace(res, intent_type=IntentType.none)
            
    if res.intent_type == IntentType.support_goal:
        # If confidence is high but no amount/ref, it's still a support intent 
        # (user might be asking "how to pay"), so we keep it.
        pass

    return res
