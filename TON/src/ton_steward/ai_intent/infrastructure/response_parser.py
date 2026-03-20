from __future__ import annotations

import json
from typing import Any

from ton_steward.ai_intent.domain.analysis_result import IntentAnalysisResult
from ton_steward.ai_intent.domain.intent_types import IntentType, CurrencyType


def parse_intent_analysis_result(raw_text: str) -> IntentAnalysisResult:
    """
    Parses LLM JSON output into a typed IntentAnalysisResult object.
    Rejects malformed results and fails safely with a 'none' intent.
    """
    try:
        # 1. Clean response (remove possible markdown code fences)
        cleaned = raw_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned.replace("```json", "", 1)
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

        # 2. Parse JSON
        data: dict[str, Any] = json.loads(cleaned)

        # 3. Extract core fields with defaults
        intent_val = data.get("intent_type", "none")
        try:
            intent_type = IntentType(intent_val)
        except ValueError:
            intent_type = IntentType.none

        confidence = float(data.get("confidence", 0.0))
        
        currency_val = data.get("currency")
        currency = None
        if currency_val == "TON":
            currency = CurrencyType.TON

        # 4. Map to IntentAnalysisResult
        return IntentAnalysisResult(
            intent_type=intent_type,
            confidence=confidence,
            goal_title=data.get("goal_title"),
            goal_description=data.get("goal_description"),
            target_amount=float(data["target_amount"]) if data.get("target_amount") is not None else None,
            currency=currency,
            deadline_text=data.get("deadline_text"),
            deadline_iso=data.get("deadline_iso"),
            target_goal_reference=data.get("target_goal_reference"),
            reasoning_summary=data.get("reasoning_summary"),
            raw=data
        )

    except (json.JSONDecodeError, KeyError, ValueError, TypeError):
        # Fail safe on any parsing/validation error
        return IntentAnalysisResult(
            intent_type=IntentType.none,
            confidence=0.0,
            reasoning_summary="Failed to parse LLM response"
        )
