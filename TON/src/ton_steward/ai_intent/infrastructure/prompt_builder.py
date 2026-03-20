from __future__ import annotations

import json
from typing import Any

from ton_steward.ai_intent.domain.intent_types import IntentType


def build_intent_extraction_prompt(
    *,
    message_text: str,
    context_messages: list[dict[str, str]] | None = None,
    active_goals_summary: str | None = None,
) -> str:
    """
    Constructs a strict system prompt and user message to extract fundraising intent.
    Forces JSON-only output.
    """
    
    schema = {
        "intent_type": "create_goal | update_goal | close_goal | summary_request | support_goal | none",
        "confidence": "float 0.0 to 1.0",
        "goal_title": "string | null",
        "goal_description": "string | null",
        "target_amount": "number | null",
        "currency": "TON | null",
        "deadline_text": "string (raw deadline from text) | null",
        "deadline_iso": "string (ISO-8601) | null",
        "target_goal_reference": "string (title or ID if mentioned) | null",
        "reasoning_summary": "string (brief explanation of why this intent was chosen) | null"
    }

    instructions = [
        "You are a structured data extraction engine.",
        "Your goal is to identify fundraising intent in Telegram messages.",
        f"Supported intent types: {', '.join([t.value for t in IntentType])}.",
        "Rules:",
        "1. Return ONLY valid JSON. No prose, no markdown fences.",
        "2. If a value is missing or uncertain, use null. DO NOT guess.",
        "3. For 'create_goal', look for titles, amounts, and deadlines.",
        "4. For 'support_goal', look for users wanting to contribute or asking how to pay.",
        "5. For 'summary_request', look for users asking about progress or status.",
        "6. Use 'none' if the message is unrelated to fundraising.",
        "7. confidence should reflect how clearly the intent is expressed."
    ]

    prompt_parts = [
        "\n".join(instructions),
        "\nOutput JSON Schema:",
        json.dumps(schema, indent=2),
    ]

    if active_goals_summary:
        prompt_parts.append(f"\nCurrently active goals in this chat:\n{active_goals_summary}")

    if context_messages:
        prompt_parts.append("\nRecent chat context:")
        for msg in context_messages:
            prompt_parts.append(f"- {msg.get('role', 'user')}: {msg.get('content', '')}")

    prompt_parts.append(f"\nTarget message to analyze:\n{message_text}")

    return "\n".join(prompt_parts)
