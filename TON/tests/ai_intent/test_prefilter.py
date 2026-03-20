from __future__ import annotations

import pytest
from ton_steward.ai_intent.infrastructure.heuristic_prefilter import prefilter


def test_prefilter_relevance_detection():
    # Relevant: collective creation
    ok, signals = prefilter("Давайте соберем на подарок!")
    assert ok is True
    assert signals.raw_flags.contains_collective_language is True

    # Relevant: money / support
    ok, signals = prefilter("Закину 10 ton")
    assert ok is True
    assert signals.raw_flags.contains_money_language is True

    # Relevant: progress/summary
    ok, signals = prefilter("какой статус сбора?")
    assert ok is True
    assert signals.raw_flags.contains_progress_language is True
    assert "summary_request" in signals.maybe_intent_candidates

    # Relevant: close
    ok, signals = prefilter("Все, хватит собирать, закрываем.")
    assert ok is True
    assert signals.raw_flags.contains_close_language is True

    # Relevant: update
    ok, signals = prefilter("Надо обновить описание сбора.")
    assert ok is True
    assert signals.raw_flags.contains_update_language is True


def test_prefilter_ignores_casual_chat():
    # Non-relevant
    ok, _ = prefilter("Привет всем, как дела?")
    assert ok is False

    ok, _ = prefilter("Погода сегодня отличная.")
    assert ok is False

    ok, _ = prefilter("")
    assert ok is False


def test_prefilter_intent_candidates():
    _, signals = prefilter("Давайте соберем 50 TON")
    assert "create_goal" in signals.maybe_intent_candidates
    assert "support_goal" in signals.maybe_intent_candidates  # matched 'ton'
    
    _, signals = prefilter("Сколько собрали?")
    assert "summary_request" in signals.maybe_intent_candidates
