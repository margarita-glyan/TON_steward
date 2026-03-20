from __future__ import annotations

import datetime as dt
from decimal import Decimal

from ton_steward.fundraising.domain.enums import GoalState
from ton_steward.fundraising.domain.models import Goal
from ton_steward.telegram_interaction.infrastructure.markdown_escape import escape_markdown_v2


def _fmt_amount(x: Decimal, currency: str | None) -> str:
    cur = currency or ""
    return f"{x.normalize()} {escape_markdown_v2(cur)}".strip()


def _fmt_deadline(deadline: dt.datetime | None, *, now: dt.datetime) -> str | None:
    if not deadline:
        return None
    # show date only for compactness
    d = deadline.date().isoformat()
    overdue = deadline < now
    return f"{escape_markdown_v2(d)}{' \\(overdue\\)' if overdue else ''}"


def render_goal_card(goal: Goal, *, now: dt.datetime | None = None, approved_by_label: str | None = None) -> str:
    now = now or dt.datetime.now(dt.timezone.utc)

    title = escape_markdown_v2(goal.title)
    target = _fmt_amount(goal.target_amount, goal.currency)
    collected = _fmt_amount(goal.collected_amount, goal.currency)
    percent = 0
    if goal.target_amount > Decimal("0"):
        percent = int((goal.collected_amount / goal.target_amount) * Decimal("100"))

    lines = [
        f"*Goal*: {title}",
        f"*State*: {escape_markdown_v2(goal.state.value)}",
        f"*Progress*: {escape_markdown_v2(str(percent))}% \\({escape_markdown_v2(collected)} / {escape_markdown_v2(target)}\\)",
    ]

    deadline = _fmt_deadline(goal.deadline_at, now=now)
    if deadline:
        lines.append(f"*Deadline*: {deadline}")

    if approved_by_label:
        lines.append(f"*Approved by*: {escape_markdown_v2(approved_by_label)}")

    return "\n".join(lines)

