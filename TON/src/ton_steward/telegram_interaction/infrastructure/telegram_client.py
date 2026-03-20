from __future__ import annotations

from typing import Protocol

from ton_steward.telegram_interaction.domain.ui_models import InlineKeyboard


class TelegramClient(Protocol):
    def send_message(
        self,
        *,
        chat_id: int,
        text: str,
        keyboard: InlineKeyboard | None = None,
        parse_mode: str = "MarkdownV2",
        reply_to_message_id: int | None = None,
    ) -> None: ...

    def edit_message(
        self,
        *,
        chat_id: int,
        message_id: int,
        text: str,
        keyboard: InlineKeyboard | None = None,
        parse_mode: str = "MarkdownV2",
    ) -> None: ...

    def answer_callback_query(self, *, callback_query_id: str, text: str | None = None, show_alert: bool = False) -> None: ...

    def send_private_message(
        self,
        *,
        user_id: int,
        text: str,
        keyboard: InlineKeyboard | None = None,
        parse_mode: str = "MarkdownV2",
    ) -> None: ...

