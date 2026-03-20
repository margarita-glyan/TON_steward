from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TelegramUser:
    id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None


@dataclass(frozen=True, slots=True)
class TelegramChat:
    id: int
    type: str
    title: str | None = None
    username: str | None = None


@dataclass(frozen=True, slots=True)
class TelegramMessage:
    message_id: int
    chat: TelegramChat
    from_user: TelegramUser
    text: str | None = None


@dataclass(frozen=True, slots=True)
class TelegramCallbackQuery:
    id: str
    from_user: TelegramUser
    message: TelegramMessage | None
    data: str | None


@dataclass(frozen=True, slots=True)
class TelegramUpdate:
    update_id: int
    message: TelegramMessage | None = None
    callback_query: TelegramCallbackQuery | None = None
