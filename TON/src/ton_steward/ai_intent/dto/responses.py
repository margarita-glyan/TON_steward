from __future__ import annotations

from dataclasses import dataclass

from ton_steward.ai_intent.domain.analysis_result import IntentAnalysisResult
from ton_steward.ai_intent.domain.relevance_flags import RelevanceSignals


@dataclass(frozen=True, slots=True)
class RelevancePrefilterResult:
    is_potentially_relevant: bool
    signals: RelevanceSignals


IntentAnalysisResultDTO = IntentAnalysisResult

