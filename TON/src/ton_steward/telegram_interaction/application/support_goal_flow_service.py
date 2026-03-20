from __future__ import annotations

from ton_steward.telegram_interaction.domain.ui_models import InlineKeyboard
from ton_steward.telegram_interaction.infrastructure.keyboard_builder import keyboard


def build_support_keyboard(goal_id: int) -> InlineKeyboard:
    return keyboard(
        [
            [("Support 10 TON", f"support:amount:{goal_id}:10"), ("Support 20 TON", f"support:amount:{goal_id}:20")],
            [("Enter amount", f"support:amount:{goal_id}:0")],
            [("Back", f"goal:view:{goal_id}")],
        ]
    )


def build_goal_selection_keyboard(active_goal_ids: list[int]) -> InlineKeyboard:
    rows = []
    for gid in active_goal_ids[:10]:
        rows.append([(f"Goal #{gid}", f"goal:view:{gid}")])
    return keyboard(rows)

