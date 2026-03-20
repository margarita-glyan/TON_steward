from __future__ import annotations

from typing import Protocol


class LLMClient(Protocol):
    """
    Clean interface for LLM interaction.
    Allows for easy swapping of providers (OpenAI, Anthropic, Stub).
    """
    def complete(self, prompt: str, temperature: float = 0.0, max_tokens: int = 512) -> str:
        """
        Sends a prompt and returns the raw text completion.
        """
        ...
