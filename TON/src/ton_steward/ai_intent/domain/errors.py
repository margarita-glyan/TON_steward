from __future__ import annotations


class AiIntentError(Exception):
    pass


class LlmResponseParseError(AiIntentError):
    pass


class InvalidIntentTypeError(AiIntentError):
    pass


class InvalidConfidenceValueError(AiIntentError):
    pass


class InvalidCurrencyError(AiIntentError):
    pass


class InvalidAnalysisResultError(AiIntentError):
    pass

