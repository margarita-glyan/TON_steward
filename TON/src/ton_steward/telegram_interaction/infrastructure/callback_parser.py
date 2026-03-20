from __future__ import annotations

from ton_steward.telegram_interaction.domain.callback_actions import CallbackAction, CallbackActionType


def parse_callback_data(data: str | None) -> CallbackAction:
    raw = data or ""
    parts = raw.split(":")
    if len(parts) < 2:
        return CallbackAction(type=CallbackActionType.unknown, raw=raw)

    head = parts[0]
    verb = parts[1]

    def _int(x: str) -> int | None:
        try:
            return int(x)
        except Exception:
            return None

    if head == "draft" and len(parts) == 3:
        draft_id = _int(parts[2])
        if verb == "approve":
            return CallbackAction(CallbackActionType.draft_approve, raw=raw, draft_id=draft_id)
        if verb == "reject":
            return CallbackAction(CallbackActionType.draft_reject, raw=raw, draft_id=draft_id)
        if verb == "edit":
            return CallbackAction(CallbackActionType.draft_edit, raw=raw, draft_id=draft_id)

    if head == "goal" and len(parts) == 3:
        goal_id = _int(parts[2])
        if verb == "view":
            return CallbackAction(CallbackActionType.goal_view, raw=raw, goal_id=goal_id)
        if verb == "support":
            return CallbackAction(CallbackActionType.goal_support, raw=raw, goal_id=goal_id)
        if verb == "status":
            return CallbackAction(CallbackActionType.goal_status, raw=raw, goal_id=goal_id)

    if head == "goals" and verb == "list" and len(parts) == 3:
        chat_id = _int(parts[2])
        return CallbackAction(CallbackActionType.goals_list, raw=raw, chat_id=chat_id)

    if head == "support" and verb == "amount" and len(parts) == 4:
        goal_id = _int(parts[2])
        preset = _int(parts[3])
        return CallbackAction(CallbackActionType.support_amount, raw=raw, goal_id=goal_id, preset_amount=preset)

    if head == "summary" and verb == "refresh" and len(parts) == 3:
        chat_id = _int(parts[2])
        return CallbackAction(CallbackActionType.summary_refresh, raw=raw, chat_id=chat_id)

    return CallbackAction(type=CallbackActionType.unknown, raw=raw)

