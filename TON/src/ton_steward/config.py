from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "replace_me")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./ton_steward.db")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    ai_provider: Literal["stub"] = os.getenv("AI_PROVIDER", "stub")  # type: ignore[assignment]
    ton_provider: Literal["mock"] = os.getenv("TON_PROVIDER", "mock")  # type: ignore[assignment]

    @property
    def log_level_value(self) -> int:
        return logging._nameToLevel.get(self.log_level.upper(), logging.INFO)
