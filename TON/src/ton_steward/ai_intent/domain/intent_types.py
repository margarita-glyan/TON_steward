from __future__ import annotations

from enum import Enum


class IntentType(str, Enum):
    create_goal = "create_goal"
    update_goal = "update_goal"
    close_goal = "close_goal"
    summary_request = "summary_request"
    support_goal = "support_goal"
    none = "none"


class ParticipantsScope(str, Enum):
    all_chat = "all_chat"
    mentioned_only = "mentioned_only"


class CurrencyType(str, Enum):
    TON = "TON"

