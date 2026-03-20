from __future__ import annotations

from ton_steward.core.decision.schemas import GoalSnapshot


def active_goal_ids(active_goals: list[GoalSnapshot]) -> set[int]:
    return {g.id for g in active_goals if g.status in {"approved", "funding", "funded"}}


def is_ambiguous_goal_target(*, referenced_goal_id: int | None, active_goals: list[GoalSnapshot]) -> bool:
    """
    Ambiguous when:
    - caller doesn't have a specific goal id, AND
    - multiple active goals exist
    """
    ids = list(active_goal_ids(active_goals))
    if referenced_goal_id is not None:
        return referenced_goal_id not in set(ids)
    return len(ids) != 1


def select_goal_if_unambiguous(*, referenced_goal_id: int | None, active_goals: list[GoalSnapshot]) -> int | None:
    ids = list(active_goal_ids(active_goals))
    if referenced_goal_id is not None:
        return referenced_goal_id if referenced_goal_id in set(ids) else None
    if len(ids) == 1:
        return ids[0]
    return None

