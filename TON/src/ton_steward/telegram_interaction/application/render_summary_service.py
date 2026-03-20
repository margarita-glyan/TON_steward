from __future__ import annotations

import datetime as dt
from decimal import Decimal

from ton_steward.fundraising.domain.enums import GoalState
from ton_steward.fundraising.domain.models import GoalSummary
from ton_steward.telegram_interaction.infrastructure.markdown_escape import escape_markdown_v2


def render_chat_summary(summary: GoalSummary, *, now: dt.datetime | None = None) -> str:
    now = now or dt.datetime.now(dt.timezone.utc)

    if summary.active_goals_count == 0 and len(summary.goals) == 0:
        return "No active fundraising goals yet\\.\n\nUse /help for what I can do\\."

    lines = [
        f"*Fundraising summary*",
        f"*Active*: {escape_markdown_v2(str(summary.active_goals_count))}  \\|  *Funded*: {escape_markdown_v2(str(summary.funded_goals_count))}  \\|  *Completed*: {escape_markdown_v2(str(summary.completed_goals_count))}",
        "",
    ]

    for g in summary.goals:
        overdue = " \\(overdue\\)" if g.overdue else ""
        cur = f" {escape_markdown_v2(g.currency)}" if g.currency else ""
        lines.append(
            f"• *{escape_markdown_v2(g.title)}* — {escape_markdown_v2(g.state.value)} — {escape_markdown_v2(str(g.percent_funded))}% "
            f"\\({escape_markdown_v2(str(g.collected_amount.normalize()))}/{escape_markdown_v2(str(g.target_amount.normalize()))}{cur}\\){overdue}"
        )

    lines.append("")
    lines.append(f"_Tip: click a goal to support it\\._")
    return "\n".join(lines)

