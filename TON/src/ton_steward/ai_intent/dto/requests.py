from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class AnalyzeMessageRequest:
    chat_id: int
    message_id: int
    user_id: int
    text: str
    language_hint: str | None = None


@dataclass(frozen=True, slots=True)
class AnalyzeWithContextRequest:
    chat_id: int
    message_id: int
    user_id: int
    text: str

    recent_messages: list[str] = field(default_factory=list)
    active_goals: list[str] = field(default_factory=list)  # titles/aliases only
    language_hint: str | None = None

