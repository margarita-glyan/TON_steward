from ton_steward.core.decision import DecisionInput, DecisionThresholds, IntentType, UserContext
from ton_steward.core.decision.schemas import AIIntent, ChatContext, DecisionActionType, GoalSnapshot
from ton_steward.core.decision.engine import decide


def test_ignore_low_confidence() -> None:
    inp = DecisionInput(
        ai=AIIntent(intent_type=IntentType.create_goal, confidence=0.50, goal_title="X", target_amount=10),
        chat=ChatContext(chat_id=1),
        user=UserContext(user_id=2, is_admin=False),
    )
    out = decide(inp, thresholds=DecisionThresholds(create_goal=0.75))
    assert out.action_type == DecisionActionType.ignore
    assert out.reason == "low_confidence"


def test_create_draft_on_valid_create_goal() -> None:
    inp = DecisionInput(
        ai=AIIntent(
            intent_type=IntentType.create_goal,
            confidence=0.90,
            goal_title="Entrance cameras",
            goal_description="Collect funds for security cameras",
            target_amount=500,
            currency="TON",
            deadline_iso="2026-03-25T00:00:00Z",
        ),
        chat=ChatContext(chat_id=10),
        user=UserContext(user_id=20, is_admin=False),
    )
    out = decide(inp)
    assert out.action_type == DecisionActionType.create_draft
    assert out.requires_admin_review is True
    assert out.payload["title"] == "Entrance cameras"


def test_summary_request_flow() -> None:
    inp = DecisionInput(
        ai=AIIntent(intent_type=IntentType.summary_request, confidence=0.92),
        chat=ChatContext(chat_id=10),
        user=UserContext(user_id=20, is_admin=False),
        active_goals=[
            GoalSnapshot(id=1, status="funding", title="A"),
        ],
    )
    out = decide(inp)
    assert out.action_type == DecisionActionType.return_summary
    assert out.requires_admin_review is False


def test_ambiguous_update_rejection() -> None:
    inp = DecisionInput(
        ai=AIIntent(intent_type=IntentType.update_goal, confidence=0.81, raw={"target_amount": 900}),
        chat=ChatContext(chat_id=10),
        user=UserContext(user_id=20, is_admin=False),
        active_goals=[
            GoalSnapshot(id=1, status="funding", title="A"),
            GoalSnapshot(id=2, status="approved", title="B"),
            GoalSnapshot(id=3, status="funding", title="C"),
        ],
    )
    out = decide(inp)
    assert out.action_type == DecisionActionType.reject_update
    assert out.reason == "ambiguous_goal_target"
    assert out.requires_admin_review is True


def test_close_request_without_target_goal() -> None:
    inp = DecisionInput(
        ai=AIIntent(intent_type=IntentType.close_goal, confidence=0.90),
        chat=ChatContext(chat_id=10),
        user=UserContext(user_id=20, is_admin=False),
        active_goals=[],
    )
    out = decide(inp)
    assert out.action_type == DecisionActionType.reject_close
    assert out.reason == "no_matching_active_goal"


def test_multi_goal_donation_requires_selection() -> None:
    inp = DecisionInput(
        ai=AIIntent(intent_type=IntentType.donate, confidence=0.90),
        chat=ChatContext(chat_id=10),
        user=UserContext(user_id=20, is_admin=False),
        active_goals=[
            GoalSnapshot(id=1, status="funding", title="A"),
            GoalSnapshot(id=2, status="approved", title="B"),
        ],
    )
    out = decide(inp)
    assert out.action_type == DecisionActionType.request_goal_selection
    assert out.reason == "multiple_active_goals_require_selection"
    assert out.relevant_goal_id is None


def test_admin_review_tagging_for_update() -> None:
    inp = DecisionInput(
        ai=AIIntent(intent_type=IntentType.update_goal, confidence=0.95, referenced_goal_id=2, raw={"deadline_iso": "x"}),
        chat=ChatContext(chat_id=10),
        user=UserContext(user_id=20, is_admin=False),
        active_goals=[GoalSnapshot(id=2, status="funding", title="A")],
    )
    out = decide(inp)
    assert out.action_type == DecisionActionType.request_admin_review
    assert out.requires_admin_review is True
    assert out.relevant_goal_id == 2

