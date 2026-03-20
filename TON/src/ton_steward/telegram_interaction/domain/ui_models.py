from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class InlineButton:
    text: str
    callback_data: str


@dataclass(frozen=True, slots=True)
class InlineKeyboard:
    rows: list[list[InlineButton]] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SendMessage:
    chat_id: int
    text: str
    keyboard: InlineKeyboard | None = None
    parse_mode: str = "MarkdownV2"
    reply_to_message_id: int | None = None


@dataclass(frozen=True, slots=True)
class EditMessage:
    chat_id: int
    message_id: int
    text: str
    keyboard: InlineKeyboard | None = None
    parse_mode: str = "MarkdownV2"


@dataclass(frozen=True, slots=True)
class AnswerCallback:
    callback_query_id: str
    text: str | None = None
    show_alert: bool = False


TelegramResponse = SendMessage | EditMessage | AnswerCallback

