from __future__ import annotations

import datetime as dt
from decimal import Decimal

from ton_steward.fundraising.domain.models import GoalDraft
from ton_steward.telegram_interaction.infrastructure.markdown_escape import escape_markdown_v2, truncate


def render_draft_review(draft: GoalDraft, *, source_snippet: str | None = None) -> str:
    title = escape_markdown_v2(draft.title or "(no title)")
    desc = escape_markdown_v2(truncate(draft.description or "", 240)) if draft.description else None
    amount = (
        f"{draft.target_amount.normalize()} {escape_markdown_v2(draft.currency or '')}".strip()
        if draft.target_amount is not None
        else None
    )
    deadline = draft.deadline_at.date().isoformat() if draft.deadline_at else None
    wallet = escape_markdown_v2(draft.wallet_address) if draft.wallet_address else None

    lines = [
        "*Draft review*",
        f"*Title*: {title}",
        f"*Status*: {escape_markdown_v2(draft.status.value)}",
    ]
    if desc:
        lines.append(f"*Description*: {desc}")
    if amount:
        lines.append(f"*Target*: {escape_markdown_v2(amount)}")
    if deadline:
        lines.append(f"*Deadline*: {escape_markdown_v2(deadline)}")
    if wallet:
        lines.append(f"*Wallet*: `{wallet}`")
    if source_snippet:
        lines.append(f"*Source*: {escape_markdown_v2(truncate(source_snippet, 180))}")

    lines.append("")
    lines.append("_Admins only: approve, edit, or reject._")
    return "\n".join(lines)

