from __future__ import annotations


class TelegramInteractionError(Exception):
    pass


class UpdateParseError(TelegramInteractionError):
    pass


class CallbackParseError(TelegramInteractionError):
    pass

