from __future__ import annotations

from dataclasses import replace

from ton_steward.ai_intent.application.normalize_result_service import normalize_analysis_result
from ton_steward.ai_intent.application.validate_result_service import validate_analysis_result
from ton_steward.ai_intent.domain.analysis_result import IntentAnalysisResult
from ton_steward.ai_intent.domain.intent_types import IntentType
from ton_steward.ai_intent.infrastructure.heuristic_prefilter import prefilter
from ton_steward.ai_intent.infrastructure.llm_client import LLMClient
from ton_steward.ai_intent.infrastructure.prompt_builder import build_intent_extraction_prompt
from ton_steward.ai_intent.infrastructure.response_parser import parse_intent_analysis_result


class AIIntentService:
    def __init__(self, llm_client: LLMClient) -> None:
        self._llm = llm_client

    def analyze_message(
        self, 
        text: str, 
        *, 
        active_goals_summary: str | None = None,
        context: list[dict[str, str]] | None = None
    ) -> IntentAnalysisResult:
        """
        Orchestrates: prefilter -> prompt -> LLM -> parse -> normalize -> validate
        """
        # 1. Prefilter
        is_relevant, signals = prefilter(text)
        if not is_relevant:
            return IntentAnalysisResult(
                intent_type=IntentType.none,
                confidence=1.0,
                is_relevant=False,
                raw_signal_flags=signals.raw_flags,
                reasoning_summary="Prefilter: no relevance detected"
            )

        # 2. LLM Extraction
        prompt = build_intent_extraction_prompt(
            message_text=text,
            context_messages=context,
            active_goals_summary=active_goals_summary
        )
        
        raw_completion = self._llm.complete(prompt)
        
        # 3. Parsing
        res = parse_intent_analysis_result(raw_completion)
        
        # 4. Attach prefilter flags for audit
        res = replace(res, is_relevant=is_relevant, raw_signal_flags=signals.raw_flags)

        # 5. Normalization & Validation
        res = normalize_analysis_result(res)
        res = validate_analysis_result(res)
        
        return res


def analyze_message(
    text: str,
    *,
    llm_client: LLMClient,
    active_goals_summary: str | None = None,
) -> IntentAnalysisResult:
    service = AIIntentService(llm_client)
    return service.analyze_message(text, active_goals_summary=active_goals_summary)


def analyze_with_context(
    text: str,
    *,
    llm_client: LLMClient,
    context: list[dict[str, str]],
    active_goals_summary: str | None = None,
) -> IntentAnalysisResult:
    service = AIIntentService(llm_client)
    return service.analyze_message(text, context=context, active_goals_summary=active_goals_summary)
