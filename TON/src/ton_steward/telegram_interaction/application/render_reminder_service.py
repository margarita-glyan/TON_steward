from __future__ import annotations

import datetime as dt

from ton_steward.fundraising.domain.models import Goal
from ton_steward.telegram_interaction.infrastructure.markdown_escape import escape_markdown_v2


def render_reminder(goal: Goal, *, now: dt.datetime | None = None, kind: str = "reminder") -> str:
    now = now or dt.datetime.now(dt.timezone.utc)
    title = escape_markdown_v2(goal.title)

    if goal.deadline_at:
        delta = goal.deadline_at - now
        if delta.total_seconds() < 0:
            time_left = "overdue"
        else:
            days = int(delta.total_seconds() // 86400)
            time_left = f"{days}d left" if days > 0 else "today"
        time_left = escape_markdown_v2(time_left)
        return f"*Reminder*: {title}\n*Deadline*: {escape_markdown_v2(goal.deadline_at.date().isoformat())} \\({time_left}\\)"

    return f"*Reminder*: {title}"

