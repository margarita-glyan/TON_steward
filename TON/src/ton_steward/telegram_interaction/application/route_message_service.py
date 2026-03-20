from __future__ import annotations

from typing import Any

from ton_steward.ai_intent.dto.requests import AnalyzeWithContextRequest
from ton_steward.core.decision.schemas import DecisionInput
from ton_steward.fundraising.dto.requests import CreateGoalDraftRequest
from ton_steward.telegram_interaction.application.ports import (
    AdminDirectory,
    AiIntentService,
    DecisionService,
    FundraisingCoreFacade,
)
from ton_steward.telegram_interaction.application.render_admin_review_service import render_draft_review
from ton_steward.telegram_interaction.application.render_summary_service import render_chat_summary
from ton_steward.telegram_interaction.domain.telegram_update import TelegramMessage
from ton_steward.telegram_interaction.domain.ui_models import (
    InlineButton,
    InlineKeyboard,
    SendMessage,
    TelegramResponse,
)
from ton_steward.telegram_interaction.infrastructure.markdown_escape import escape_markdown_v2


class RouteMessageService:
    def __init__(
        self,
        ai_intent_service: AiIntentService,
        decision_service: DecisionService,
        fundraising_core: FundraisingCoreFacade,
        admin_directory: AdminDirectory,
    ) -> None:
        self._ai_intent_service = ai_intent_service
        self._decision_service = decision_service
        self._fundraising_core = fundraising_core
        self._admin_directory = admin_directory

    def route_message(self, message: TelegramMessage) -> list[TelegramResponse]:
        if not message.text:
            return []

        text = message.text.strip()

        if text.startswith("/"):
            return self._handle_command(message, text)

        return self._handle_group_message(message)

    def _handle_command(self, message: TelegramMessage, text: str) -> list[TelegramResponse]:
        cmd = text.split("@")[0].split(" ")[0].lower()

        if cmd == "/summary" or cmd == "/goals":
            return self._handle_summary_command(message)
        if cmd == "/help":
            return self._handle_help_command(message)

        return []

    def _handle_summary_command(self, message: TelegramMessage) -> list[TelegramResponse]:
        summary_res = self._fundraising_core.get_chat_goal_summary(message.chat.id)
        text = render_chat_summary(summary_res.summary)
        return [SendMessage(chat_id=message.chat.id, text=text)]

    def _handle_help_command(self, message: TelegramMessage) -> list[TelegramResponse]:
        help_text = (
            "*TON Steward Help*\n\n"
            "I help manage fundraising in this group using AI and TON\\.\n\n"
            "*Commands*:\n"
            "/summary — Show all active goals\n"
            "/goals — List goals\n"
            "/help — Show this help message\n\n"
            "Just talk naturally and I will detect fundraising intents\\!"
        )
        return [SendMessage(chat_id=message.chat.id, text=help_text)]

    def _handle_group_message(self, message: TelegramMessage) -> list[TelegramResponse]:
        # 1. AI Analysis
        ai_req = AnalyzeWithContextRequest(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            message_text=message.text or "",
            context=[], # MVP: no context for now
        )
        analysis = self._ai_intent_service.analyze_with_context(ai_req)

        # 2. Decision Layer
        decision_input = DecisionInput(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            intent=analysis,
        )
        action = self._decision_service.decide(decision_input)

        # 3. Route Action
        if action.type == "create_draft" and action.draft_params:
            return self._handle_create_draft(message, action.draft_params)
        if action.type == "return_summary":
            return self._handle_summary_command(message)

        return []

    def _handle_create_draft(self, message: TelegramMessage, params: dict[str, Any]) -> list[TelegramResponse]:
        # Create draft in core
        req = CreateGoalDraftRequest(
            chat_id=message.chat.id,
            creator_id=message.from_user.id,
            title=params.get("title"),
            description=params.get("description"),
            target_amount=params.get("target_amount"),
            currency=params.get("currency", "TON"),
            deadline_at=params.get("deadline_at"),
        )
        res = self._fundraising_core.create_goal_draft(req)

        if not res.draft:
            return []

        # Render admin review
        text = render_draft_review(res.draft, source_snippet=message.text)
        
        # Build keyboard
        kb = InlineKeyboard(rows=[
            [
                InlineButton(text="✅ Approve", callback_data=f"draft:approve:{res.draft.id}"),
                InlineButton(text="❌ Reject", callback_data=f"draft:reject:{res.draft.id}"),
            ],
            [
                InlineButton(text="📝 Edit", callback_data=f"draft:edit:{res.draft.id}"),
            ]
        ])

        # Send to group (Admins only will be checked in callback)
        # Or ideally send to a private admin chat if we had the logic.
        # For MVP we send to group, but only admins can press buttons.
        return [SendMessage(chat_id=message.chat.id, text=text, keyboard=kb, reply_to_message_id=message.message_id)]
