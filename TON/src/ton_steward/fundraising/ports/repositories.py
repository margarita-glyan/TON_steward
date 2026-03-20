from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Protocol

from ton_steward.fundraising.domain.models import Contribution, Goal, GoalDraft


class GoalDraftRepository(Protocol):
    """
    Port for managing lifecycle of goal suggestions.
    """
    def next_id(self) -> int: ...
    def find_by_id(self, draft_id: int) -> GoalDraft | None: ...
    def save(self, draft: GoalDraft) -> None: ...
    def update(self, draft: GoalDraft) -> None: ...


class GoalRepository(Protocol):
    """
    Port for managing active approved fundraising goals.
    """
    def next_id(self) -> int: ...
    def find_by_id(self, goal_id: int) -> Goal | None: ...
    def save(self, goal: Goal) -> None: ...
    def update(self, goal: Goal) -> None: ...
    def list_by_chat_id(self, chat_id: int) -> list[Goal]: ...
    def list_active_by_chat_id(self, chat_id: int) -> list[Goal]: ...


class ContributionRepository(Protocol):
    """
    Port for managing confirmed financial contributions.
    """
    def next_id(self) -> int: ...
    def exists_by_tx_hash(self, tx_hash: str) -> bool: ...
    def save(self, contribution: Contribution) -> None: ...
    def list_confirmed_by_goal_id(self, goal_id: int) -> list[Contribution]: ...
    def sum_confirmed_by_goal_id(self, goal_id: int) -> Decimal: ...
    def count_confirmed_contributors_by_goal_id(self, goal_id: int) -> int: ...


class AuditLogger(Protocol):
    """
    Port for logging domain events for transparency and history.
    """
    def emit(
        self,
        *,
        entity_type: str,
        entity_id: str,
        actor_user_id: int | None,
        action_type: str,
        previous_values: dict | None,
        new_values: dict | None,
        created_at: dt.datetime,
    ) -> None: ...


class AdminChecker(Protocol):
    """
    Port for verifying admin rights within a specific chat.
    """
    def is_admin(self, *, chat_id: int, user_id: int) -> bool: ...
