import os
import sys
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(REPO_ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from ton_steward.ai_intent.application.analyze_message_service import analyze_with_context  # noqa: E402
from ton_steward.ai_intent.application.normalize_result_service import normalize_analysis_result  # noqa: E402
from ton_steward.ai_intent.application.prefilter_service import prefilter_message  # noqa: E402
from ton_steward.ai_intent.application.validate_result_service import validate_analysis_result  # noqa: E402
from ton_steward.ai_intent.domain.intent_types import CurrencyType, IntentType  # noqa: E402
from ton_steward.ai_intent.dto.requests import AnalyzeWithContextRequest  # noqa: E402
from ton_steward.ai_intent.infrastructure.llm_client import StubLlmClient  # noqa: E402
from ton_steward.ai_intent.infrastructure.response_parser import parse_llm_json  # noqa: E402


class TestPrefilter(unittest.TestCase):
    def test_relevant_create_goal_text(self) -> None:
        r = prefilter_message("давайте скинемся на камеры")
        self.assertTrue(r.is_potentially_relevant)
        self.assertTrue(r.signals.raw_flags.contains_collective_language)

    def test_relevant_summary_request_text(self) -> None:
        r = prefilter_message("что по сборам?")
        self.assertTrue(r.is_potentially_relevant)
        self.assertTrue(r.signals.raw_flags.contains_progress_language)

    def test_irrelevant_casual_text(self) -> None:
        r = prefilter_message("привет как дела")
        self.assertFalse(r.is_potentially_relevant)

    def test_ambiguous_text(self) -> None:
        r = prefilter_message("давайте сделаем")
        # "давайте" alone is weak but still a signal; we keep it relevant to allow context/LLM
        self.assertTrue(r.is_potentially_relevant)


class TestParsingNormalization(unittest.TestCase):
    def test_valid_json(self) -> None:
        obj = parse_llm_json('{"intent_type":"create_goal","confidence":0.9}')
        self.assertEqual(obj["intent_type"], "create_goal")

    def test_malformed_json(self) -> None:
        with self.assertRaises(Exception):
            parse_llm_json("{not json")

    def test_invalid_intent_type(self) -> None:
        with self.assertRaises(Exception):
            parse_llm_json('{"intent_type":"hack","confidence":0.9}')

    def test_empty_fields_normalize_to_null(self) -> None:
        res = normalize_analysis_result(
            {"intent_type": "create_goal", "confidence": 0.9, "goal_title": "   ", "currency": "TON"},
            default_relevant=True,
            raw_flags=prefilter_message("соберем на что-то").signals.raw_flags,
        )
        self.assertIsNone(res.goal_title)
        self.assertEqual(res.currency, CurrencyType.TON)

    def test_invalid_confidence_clamped(self) -> None:
        res = normalize_analysis_result(
            {"intent_type": "create_goal", "confidence": 99},
            default_relevant=True,
            raw_flags=prefilter_message("соберем").signals.raw_flags,
        )
        self.assertEqual(res.confidence, 1.0)


class TestIntentBehavior(unittest.TestCase):
    def test_create_goal_with_amount(self) -> None:
        llm = StubLlmClient(
            '{"intent_type":"create_goal","confidence":0.91,"goal_title":"Камеры","target_amount":500,"currency":"TON","deadline_text":"до пятницы","deadline_iso":null,"participants_scope":"all_chat","mentioned_users":[],"reasoning_summary":"создать сбор"}'
        )
        out = analyze_with_context(
            AnalyzeWithContextRequest(chat_id=1, message_id=2, user_id=3, text="нужно собрать 500 TON на камеры"),
            llm=llm,
        )
        self.assertEqual(out.intent_type, IntentType.create_goal)
        self.assertEqual(out.target_amount, 500.0)

    def test_create_goal_without_amount(self) -> None:
        llm = StubLlmClient(
            '{"intent_type":"create_goal","confidence":0.82,"goal_title":"Камеры","target_amount":null,"currency":null,"deadline_text":null,"deadline_iso":null,"participants_scope":"all_chat","mentioned_users":[],"reasoning_summary":"предлагает сбор"}'
        )
        out = analyze_with_context(
            AnalyzeWithContextRequest(chat_id=1, message_id=2, user_id=3, text="давайте скинемся на камеры"),
            llm=llm,
        )
        self.assertEqual(out.intent_type, IntentType.create_goal)
        self.assertIsNone(out.target_amount)

    def test_update_goal_ambiguous_reference_reduces_confidence(self) -> None:
        llm = StubLlmClient(
            '{"intent_type":"update_goal","confidence":0.93,"target_goal_reference":null,"reasoning_summary":"предлагает перенести дедлайн"}'
        )
        out = analyze_with_context(
            AnalyzeWithContextRequest(chat_id=1, message_id=2, user_id=3, text="перенесем дедлайн на пятницу"),
            llm=llm,
        )
        self.assertEqual(out.intent_type, IntentType.update_goal)
        self.assertLessEqual(out.confidence, 0.75)

    def test_close_goal(self) -> None:
        llm = StubLlmClient('{"intent_type":"close_goal","confidence":0.9,"reasoning_summary":"закрыть сбор"}')
        out = analyze_with_context(
            AnalyzeWithContextRequest(chat_id=1, message_id=2, user_id=3, text="закрываем сбор"),
            llm=llm,
        )
        self.assertEqual(out.intent_type, IntentType.close_goal)

    def test_summary_request(self) -> None:
        llm = StubLlmClient('{"intent_type":"summary_request","confidence":0.92,"reasoning_summary":"спрашивает прогресс"}')
        out = analyze_with_context(
            AnalyzeWithContextRequest(chat_id=1, message_id=2, user_id=3, text="что по сборам?"),
            llm=llm,
        )
        self.assertEqual(out.intent_type, IntentType.summary_request)

    def test_support_goal(self) -> None:
        llm = StubLlmClient('{"intent_type":"support_goal","confidence":0.88,"target_amount":20,"currency":"TON","reasoning_summary":"хочет донатить"}')
        out = analyze_with_context(
            AnalyzeWithContextRequest(chat_id=1, message_id=2, user_id=3, text="я закину 20 TON"),
            llm=llm,
        )
        self.assertEqual(out.intent_type, IntentType.support_goal)
        self.assertEqual(out.target_amount, 20.0)

    def test_none(self) -> None:
        # Prefilter will likely mark as irrelevant and skip LLM
        out = analyze_with_context(
            AnalyzeWithContextRequest(chat_id=1, message_id=2, user_id=3, text="привет"),
            llm=StubLlmClient('{"intent_type":"create_goal","confidence":0.9}'),
        )
        self.assertEqual(out.intent_type, IntentType.none)


class TestContextBehavior(unittest.TestCase):
    def test_vague_message_becomes_create_goal_with_context(self) -> None:
        llm = StubLlmClient(
            '{"intent_type":"create_goal","confidence":0.76,"goal_title":"Камеры","target_amount":null,"currency":null,"reasoning_summary":"контекст про камеры"}'
        )
        out = analyze_with_context(
            AnalyzeWithContextRequest(
                chat_id=1,
                message_id=2,
                user_id=3,
                text="давайте делаем",
                recent_messages=["в подъезде темно", "может поставить камеры"],
                active_goals=[],
            ),
            llm=llm,
        )
        self.assertEqual(out.intent_type, IntentType.create_goal)

    def test_vague_message_stays_none_without_llm(self) -> None:
        out = analyze_with_context(
            AnalyzeWithContextRequest(chat_id=1, message_id=2, user_id=3, text="давайте делаем"),
            llm=None,
        )
        self.assertEqual(out.intent_type, IntentType.none)
        self.assertGreater(out.confidence, 0.0)

    def test_target_reference_suggestion_with_active_goals(self) -> None:
        llm = StubLlmClient(
            '{"intent_type":"support_goal","confidence":0.82,"target_goal_reference":"Entrance cameras","reasoning_summary":"ссылается на камеры"}'
        )
        out = analyze_with_context(
            AnalyzeWithContextRequest(
                chat_id=1,
                message_id=2,
                user_id=3,
                text="давайте добьем камеры",
                active_goals=["Entrance cameras", "Door mat"],
            ),
            llm=llm,
        )
        self.assertEqual(out.target_goal_reference, "Entrance cameras")

    def test_unsupported_currency_is_nulled(self) -> None:
        raw = {
            "intent_type": "support_goal",
            "confidence": 0.9,
            "currency": "USD",
            "target_amount": 10,
        }
        res = normalize_analysis_result(raw, default_relevant=True, raw_flags=prefilter_message("донат").signals.raw_flags)
        self.assertIsNone(res.currency)

    def test_low_confidence_degrades_to_none(self) -> None:
        llm = StubLlmClient('{"intent_type":"create_goal","confidence":0.4,"goal_title":"X"}')
        out = analyze_with_context(
            AnalyzeWithContextRequest(chat_id=1, message_id=2, user_id=3, text="давайте скинемся"),
            llm=llm,
        )
        # Validation should degrade low confidence to none
        self.assertEqual(out.intent_type, IntentType.none)


if __name__ == "__main__":
    unittest.main()

