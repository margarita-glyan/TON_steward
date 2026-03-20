from __future__ import annotations

import re

from ton_steward.ai_intent.domain.relevance_flags import RawSignalFlags, RelevanceSignals


def prefilter(text: str) -> tuple[bool, RelevanceSignals]:
    t = (text or "").lower().strip()
    if not t:
        return False, RelevanceSignals()

    # Using \b correctly requires UNICODE flag and specific regex patterns
    # In Python 3, \b matches boundary between \w and non-\w. \w includes Cyrillic.
    def _match(pattern: str, text: str) -> bool:
        return bool(re.search(pattern, text, flags=re.IGNORECASE | re.UNICODE))

    # Patterns with word boundaries
    p_money = r"\b(ton|₽|руб|донат|оплат|взнос|скину|закин)\b"
    p_collective = r"\b(скинем|собер|сбор|давайте|куп|участву)\b"
    p_deadline = r"\b(дедлайн|срок|до|к)\b"
    p_progress = r"\b(статус|прогресс|собрали)\b|что по"
    p_close = r"\b(закрыва|хватит|стоп)\b"
    p_update = r"\b(обнов|добав|измен|кошел)\b"

    has_money = _match(p_money, t)
    has_collective = _match(p_collective, t)
    has_deadline = _match(p_deadline, t)
    has_progress = _match(p_progress, t)
    has_close = _match(p_close, t)
    has_update = _match(p_update, t)

    is_relevant = has_money or has_collective or has_deadline or has_progress or has_close or has_update

    flags = RawSignalFlags(
        contains_money_language=has_money,
        contains_collective_language=has_collective,
        contains_deadline_language=has_deadline,
        contains_progress_language=has_progress,
        contains_close_language=has_close,
        contains_update_language=has_update,
    )

    candidates = []
    if has_progress: candidates.append("summary_request")
    if has_close: candidates.append("close_goal")
    if has_update: candidates.append("update_goal")
    if has_collective: candidates.append("create_goal")
    if has_money and not (has_progress or has_close or has_update):
        candidates.append("support_goal")

    return is_relevant, RelevanceSignals(
        matched_signals=[],
        maybe_intent_candidates=candidates,
        raw_flags=flags
    )
