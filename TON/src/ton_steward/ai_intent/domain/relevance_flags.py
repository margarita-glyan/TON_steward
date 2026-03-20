from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class RawSignalFlags:
    contains_money_language: bool = False
    contains_collective_language: bool = False
    contains_deadline_language: bool = False
    contains_progress_language: bool = False
    contains_close_language: bool = False
    contains_update_language: bool = False


@dataclass(frozen=True, slots=True)
class RelevanceSignals:
    matched_signals: list[str] = field(default_factory=list)
    maybe_intent_candidates: list[str] = field(default_factory=list)
    raw_flags: RawSignalFlags = field(default_factory=RawSignalFlags)

