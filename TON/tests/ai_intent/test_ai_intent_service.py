from __future__ import annotations

import json
import pytest
from ton_steward.ai_intent.application.analyze_message_service import AIIntentService
from ton_steward.ai_intent.domain.intent_types import IntentType


class MockLLMClient:
    def __init__(self, response_json: dict | str):
        self.response = response_json if isinstance(response_json, str) else json.dumps(response_json)

    def complete(self, prompt: str, **kwargs) -> str:
        return self.response


def test_service_prefilter_ignores_irrelevant():
    service = AIIntentService(llm_client=MockLLMClient({}))
    res = service.analyze_message("Привет, как дела?")
    assert res.intent_type == IntentType.none
    assert res.is_relevant is False


def test_service_orchestrates_extraction():
    # Relevant message
    mock_llm = MockLLMClient({
        "intent_type": "create_goal",
        "confidence": 0.9,
        "goal_title": "  Party fund  ",
        "target_amount": 100.5
    })
    service = AIIntentService(llm_client=mock_llm)
    
    res = service.analyze_message("Давайте соберем 100.5 TON на вечеринку!")
    
    assert res.is_relevant is True
    assert res.intent_type == IntentType.create_goal
    assert res.goal_title == "Party fund"  # normalized
    assert res.target_amount == 100.5
    assert res.currency.value == "TON"  # normalized/defaulted


def test_service_degrades_on_low_confidence():
    mock_llm = MockLLMClient({
        "intent_type": "create_goal",
        "confidence": 0.2, # too low
        "goal_title": "Maybe a goal?"
    })
    service = AIIntentService(llm_client=mock_llm)
    res = service.analyze_message("соберем?")
    
    assert res.intent_type == IntentType.none


def test_service_fails_safely_on_garbage_json():
    mock_llm = MockLLMClient("not a json")
    service = AIIntentService(llm_client=mock_llm)
    res = service.analyze_message("Давайте соберем 100 TON")
    
    assert res.intent_type == IntentType.none
    assert "Failed to parse" in res.reasoning_summary
