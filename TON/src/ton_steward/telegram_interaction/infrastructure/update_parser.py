from __future__ import annotations

from typing import Any

from ton_steward.telegram_interaction.domain.errors import UpdateParseError
from ton_steward.telegram_interaction.domain.telegram_update import (
    TelegramCallbackQuery,
    TelegramChat,
    TelegramMessage,
    TelegramUpdate,
    TelegramUser,
)


def _get(d: dict[str, Any], key: str, default: Any = None) -> Any:
    return d.get(key, default) if isinstance(d, dict) else default


def parse_update(raw: dict[str, Any]) -> TelegramUpdate:
    if not isinstance(raw, dict):
        raise UpdateParseError("update must be a dict")
    update_id = _get(raw, "update_id")
    if not isinstance(update_id, int):
        raise UpdateParseError("missing update_id")

    msg = None
    if isinstance(_get(raw, "message"), dict):
        msg = _parse_message(_get(raw, "message"))

    cbq = None
    if isinstance(_get(raw, "callback_query"), dict):
        cbq = _parse_callback_query(_get(raw, "callback_query"))

    return TelegramUpdate(update_id=update_id, message=msg, callback_query=cbq)


def _parse_user(u: dict[str, Any]) -> TelegramUser:
    uid = _get(u, "id")
    if not isinstance(uid, int):
        raise UpdateParseError("missing user.id")
    return TelegramUser(
        id=uid,
        username=_get(u, "username"),
        first_name=_get(u, "first_name"),
        last_name=_get(u, "last_name"),
    )


def _parse_chat(c: dict[str, Any]) -> TelegramChat:
    cid = _get(c, "id")
    ctype = _get(c, "type")
    if not isinstance(cid, int) or not isinstance(ctype, str):
        raise UpdateParseError("missing chat.id/type")
    return TelegramChat(id=cid, type=ctype, title=_get(c, "title"), username=_get(c, "username"))


def _parse_message(m: dict[str, Any]) -> TelegramMessage:
    mid = _get(m, "message_id")
    if not isinstance(mid, int):
        raise UpdateParseError("missing message_id")
    chat = _parse_chat(_get(m, "chat", {}))
    from_user = _parse_user(_get(m, "from", {}))
    text = _get(m, "text")
    if text is not None and not isinstance(text, str):
        text = None
    return TelegramMessage(message_id=mid, chat=chat, from_user=from_user, text=text)


def _parse_callback_query(cq: dict[str, Any]) -> TelegramCallbackQuery:
    cid = _get(cq, "id")
    if not isinstance(cid, str):
        raise UpdateParseError("missing callback_query.id")
    from_user = _parse_user(_get(cq, "from", {}))
    data = _get(cq, "data")
    if data is not None and not isinstance(data, str):
        data = None
    message = None
    if isinstance(_get(cq, "message"), dict):
        message = _parse_message(_get(cq, "message"))
    return TelegramCallbackQuery(id=cid, from_user=from_user, message=message, data=data)

