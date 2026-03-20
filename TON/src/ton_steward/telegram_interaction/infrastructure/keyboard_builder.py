from __future__ import annotations

from ton_steward.telegram_interaction.domain.ui_models import InlineButton, InlineKeyboard


def keyboard(rows: list[list[tuple[str, str]]]) -> InlineKeyboard:
    return InlineKeyboard(
        rows=[
            [InlineButton(text=t, callback_data=d) for (t, d) in row]
            for row in rows
        ]
    )

