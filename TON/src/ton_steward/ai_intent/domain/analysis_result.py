from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ton_steward.ai_intent.domain.intent_types import CurrencyType, IntentType, ParticipantsScope
from ton_steward.ai_intent.domain.relevance_flags import RawSignalFlags


@dataclass(frozen=True, slots=True)
class IntentAnalysisResult:
    intent_type: IntentType
    confidence: float

    goal_title: str | None = None
    goal_description: str | None = None
    target_amount: float | None = None
    currency: CurrencyType | None = None

    deadline_text: str | None = None
    deadline_iso: str | None = None

    target_goal_reference: str | None = None
    participants_scope: ParticipantsScope = ParticipantsScope.all_chat
    mentioned_users: list[int] = field(default_factory=list)

    is_relevant: bool = False
    raw_signal_flags: RawSignalFlags = field(default_factory=RawSignalFlags)
    reasoning_summary: str | None = None

    raw: dict[str, Any] = field(default_factory=dict)

