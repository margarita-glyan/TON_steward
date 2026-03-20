from __future__ import annotations

from ton_steward.fundraising.dto.requests import ApproveGoalDraftRequest, RejectGoalDraftRequest
from ton_steward.telegram_interaction.application.ports import AdminDirectory, FundraisingCoreFacade
from ton_steward.telegram_interaction.application.render_goal_card_service import render_goal_card
from ton_steward.telegram_interaction.domain.callback_actions import CallbackActionType
from ton_steward.telegram_interaction.domain.telegram_update import TelegramCallbackQuery
from ton_steward.telegram_interaction.domain.ui_models import (
    AnswerCallback,
    EditMessage,
    InlineButton,
    InlineKeyboard,
    SendMessage,
    TelegramResponse,
)
from ton_steward.telegram_interaction.infrastructure.callback_parser import parse_callback_data


class RouteCallbackService:
    def __init__(
        self,
        fundraising_core: FundraisingCoreFacade,
        admin_directory: AdminDirectory,
    ) -> None:
        self._fundraising_core = fundraising_core
        self._admin_directory = admin_directory

    def route_callback(self, cbq: TelegramCallbackQuery) -> list[TelegramResponse]:
        action = parse_callback_data(cbq.data)

        if action.type == CallbackActionType.unknown:
            return [AnswerCallback(callback_query_id=cbq.id, text="Unknown action")]

        # Admin-only actions
        admin_actions = {
            CallbackActionType.draft_approve,
            CallbackActionType.draft_reject,
            CallbackActionType.draft_edit,
        }

        if action.type in admin_actions:
            if not cbq.message:
                return [AnswerCallback(callback_query_id=cbq.id, text="Message context lost")]
            
            is_admin = self._admin_directory.is_admin(
                chat_id=cbq.message.chat.id,
                user_id=cbq.from_user.id
            )
            if not is_admin:
                return [AnswerCallback(callback_query_id=cbq.id, text="Admins only", show_alert=True)]

        if action.type == CallbackActionType.draft_approve:
            return self._handle_draft_approve(cbq, action.draft_id)
        if action.type == CallbackActionType.draft_reject:
            return self._handle_draft_reject(cbq, action.draft_id)
        if action.type == CallbackActionType.goal_support:
            return self._handle_goal_support(cbq, action.goal_id)

        return [AnswerCallback(callback_query_id=cbq.id, text="Not implemented yet")]

    def _handle_draft_approve(self, cbq: TelegramCallbackQuery, draft_id: int | None) -> list[TelegramResponse]:
        if draft_id is None:
            return [AnswerCallback(callback_query_id=cbq.id, text="Invalid draft ID")]

        res = self._fundraising_core.approve_goal_draft(ApproveGoalDraftRequest(
            draft_id=draft_id,
            admin_id=cbq.from_user.id
        ))

        if not res.goal:
            return [AnswerCallback(callback_query_id=cbq.id, text="Failed to approve")]

        # 1. Answer callback
        # 2. Edit original message to show "Approved" (to remove buttons)
        # 3. Send new Goal Card to group
        
        admin_name = cbq.from_user.username or cbq.from_user.first_name or "Admin"
        card_text = render_goal_card(res.goal, approved_by_label=admin_name)
        
        kb = InlineKeyboard(rows=[
            [InlineButton(text="💎 Support Goal", callback_data=f"goal:support:{res.goal.id}")],
            [InlineButton(text="📊 Status", callback_data=f"goal:status:{res.goal.id}")],
        ])

        responses = [
            AnswerCallback(callback_query_id=cbq.id, text="Goal approved!"),
            EditMessage(
                chat_id=cbq.message.chat.id,
                message_id=cbq.message.message_id,
                text=f"✅ Goal approved by {admin_name}",
                keyboard=None
            ),
            SendMessage(
                chat_id=cbq.message.chat.id,
                text=card_text,
                keyboard=kb
            )
        ]
        return responses

    def _handle_draft_reject(self, cbq: TelegramCallbackQuery, draft_id: int | None) -> list[TelegramResponse]:
        if draft_id is None:
            return [AnswerCallback(callback_query_id=cbq.id, text="Invalid draft ID")]

        self._fundraising_core.reject_goal_draft(RejectGoalDraftRequest(
            draft_id=draft_id,
            admin_id=cbq.from_user.id
        ))

        admin_name = cbq.from_user.username or cbq.from_user.first_name or "Admin"
        
        return [
            AnswerCallback(callback_query_id=cbq.id, text="Draft rejected"),
            EditMessage(
                chat_id=cbq.message.chat.id,
                message_id=cbq.message.message_id,
                text=f"❌ Draft rejected by {admin_name}",
                keyboard=None
            )
        ]

    def _handle_goal_support(self, cbq: TelegramCallbackQuery, goal_id: int | None) -> list[TelegramResponse]:
        if goal_id is None:
            return [AnswerCallback(callback_query_id=cbq.id, text="Invalid goal ID")]
        
        # In a real app, we might check if goal is active
        # For MVP, show support options
        kb = InlineKeyboard(rows=[
            [
                InlineButton(text="5 TON", callback_data=f"support:amount:{goal_id}:5"),
                InlineButton(text="10 TON", callback_data=f"support:amount:{goal_id}:10"),
                InlineButton(text="25 TON", callback_data=f"support:amount:{goal_id}:25"),
            ],
            [InlineButton(text="⌨️ Enter Custom Amount", callback_data=f"support:amount:{goal_id}:0")],
        ])
        
        return [
            AnswerCallback(callback_query_id=cbq.id),
            SendMessage(
                chat_id=cbq.from_user.id, # Send to private chat
                text=f"Select amount to support goal #{goal_id}:",
                keyboard=kb
            )
        ]
