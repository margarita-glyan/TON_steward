from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class CallbackActionType(str, Enum):
    draft_approve = "draft_approve"
    draft_reject = "draft_reject"
    draft_edit = "draft_edit"
    goal_view = "goal_view"
    goal_support = "goal_support"
    goal_status = "goal_status"
    goals_list = "goals_list"
    support_amount = "support_amount"
    summary_refresh = "summary_refresh"
    unknown = "unknown"


@dataclass(frozen=True, slots=True)
class CallbackAction:
    type: CallbackActionType
    raw: str

    draft_id: int | None = None
    goal_id: int | None = None
    chat_id: int | None = None
    preset_amount: int | None = None

