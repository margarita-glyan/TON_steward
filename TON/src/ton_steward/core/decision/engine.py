from __future__ import annotations

from ton_steward.core.decision.helpers import is_ambiguous_goal_target, select_goal_if_unambiguous
from ton_steward.core.decision.schemas import (
    DecisionAction,
    DecisionActionType,
    DecisionInput,
    DecisionThresholds,
    IntentType,
)


def _threshold_for(intent: IntentType, thresholds: DecisionThresholds) -> float:
    match intent:
        case IntentType.create_goal:
            return thresholds.create_goal
        case IntentType.update_goal:
            return thresholds.update_goal
        case IntentType.close_goal:
            return thresholds.close_goal
        case IntentType.summary_request:
            return thresholds.summary_request
        case IntentType.donate:
            return thresholds.donate
        case _:
            return 1.0


def decide(inp: DecisionInput, *, thresholds: DecisionThresholds | None = None) -> DecisionAction:
    """
    Pure deterministic decision function.
    - Uses AI only as semantic extraction input (intent + confidence + extracted fields).
    - Produces a structured action that the backend execution layer can handle.
    """
    thresholds = thresholds or DecisionThresholds()
    ai = inp.ai

    if ai.intent_type == IntentType.none:
        return DecisionAction(
            action_type=DecisionActionType.ignore,
            reason="intent_none",
            confidence_used=float(ai.confidence),
            requires_admin_review=False,
        )

    min_conf = _threshold_for(ai.intent_type, thresholds)
    if float(ai.confidence) < float(min_conf):
        return DecisionAction(
            action_type=DecisionActionType.ignore,
            reason="low_confidence",
            confidence_used=float(ai.confidence),
            requires_admin_review=False,
            payload={"min_confidence": float(min_conf), "intent_type": ai.intent_type.value},
        )

    # Safe read-only action
    if ai.intent_type == IntentType.summary_request:
        return DecisionAction(
            action_type=DecisionActionType.return_summary,
            reason="summary_request",
            confidence_used=float(ai.confidence),
            requires_admin_review=False,
        )

    # Draft creation only (never active goal)
    if ai.intent_type == IntentType.create_goal:
        if not ai.goal_title or ai.target_amount is None:
            return DecisionAction(
                action_type=DecisionActionType.ignore,
                reason="create_goal_missing_fields",
                confidence_used=float(ai.confidence),
                requires_admin_review=False,
            )
        return DecisionAction(
            action_type=DecisionActionType.create_draft,
            reason="high_confidence_create_goal",
            confidence_used=float(ai.confidence),
            requires_admin_review=True,
            payload={
                "title": ai.goal_title,
                "description": ai.goal_description,
                "target_amount": ai.target_amount,
                "currency": ai.currency or "TON",
                "deadline_iso": ai.deadline_iso,
            },
        )

    # Updates must identify a goal deterministically; never auto-apply state changes.
    if ai.intent_type == IntentType.update_goal:
        if is_ambiguous_goal_target(referenced_goal_id=ai.referenced_goal_id, active_goals=inp.active_goals):
            return DecisionAction(
                action_type=DecisionActionType.reject_update,
                reason="ambiguous_goal_target",
                confidence_used=float(ai.confidence),
                requires_admin_review=True,
            )
        goal_id = select_goal_if_unambiguous(referenced_goal_id=ai.referenced_goal_id, active_goals=inp.active_goals)
        if goal_id is None:
            return DecisionAction(
                action_type=DecisionActionType.no_active_goal,
                reason="no_matching_active_goal",
                confidence_used=float(ai.confidence),
                requires_admin_review=True,
            )
        return DecisionAction(
            action_type=DecisionActionType.request_admin_review,
            reason="update_goal_requires_admin",
            confidence_used=float(ai.confidence),
            requires_admin_review=True,
            relevant_goal_id=goal_id,
            payload={"proposed_update": ai.raw or {}},
        )

    # Close requests must target an existing active goal; always admin-reviewed.
    if ai.intent_type == IntentType.close_goal:
        goal_id = select_goal_if_unambiguous(referenced_goal_id=ai.referenced_goal_id, active_goals=inp.active_goals)
        if goal_id is None:
            return DecisionAction(
                action_type=DecisionActionType.reject_close,
                reason="no_matching_active_goal",
                confidence_used=float(ai.confidence),
                requires_admin_review=True,
            )
        return DecisionAction(
            action_type=DecisionActionType.request_admin_review,
            reason="close_goal_requires_admin",
            confidence_used=float(ai.confidence),
            requires_admin_review=True,
            relevant_goal_id=goal_id,
        )

    # Payment-related: never start payment without explicit goal_id when multiple.
    if ai.intent_type == IntentType.donate:
        goal_id = select_goal_if_unambiguous(referenced_goal_id=ai.referenced_goal_id, active_goals=inp.active_goals)
        if goal_id is None:
            if len(inp.active_goals) == 0:
                return DecisionAction(
                    action_type=DecisionActionType.no_active_goal,
                    reason="no_active_goals_to_donate",
                    confidence_used=float(ai.confidence),
                    requires_admin_review=False,
                )
            return DecisionAction(
                action_type=DecisionActionType.request_goal_selection,
                reason="multiple_active_goals_require_selection",
                confidence_used=float(ai.confidence),
                requires_admin_review=False,
                payload={"active_goal_ids": [g.id for g in inp.active_goals]},
            )
        return DecisionAction(
            action_type=DecisionActionType.request_goal_selection,
            reason="goal_preselected_for_donation",
            confidence_used=float(ai.confidence),
            requires_admin_review=False,
            relevant_goal_id=goal_id,
        )

    return DecisionAction(
        action_type=DecisionActionType.unsupported,
        reason="unsupported_intent_type",
        confidence_used=float(ai.confidence),
        requires_admin_review=False,
        payload={"intent_type": ai.intent_type.value},
    )

