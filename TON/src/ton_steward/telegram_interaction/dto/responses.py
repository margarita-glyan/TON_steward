from __future__ import annotations

from dataclasses import dataclass, field

from ton_steward.telegram_interaction.domain.ui_models import TelegramResponse


@dataclass(frozen=True, slots=True)
class ProcessUpdateResponse:
    responses: list[TelegramResponse] = field(default_factory=list)

