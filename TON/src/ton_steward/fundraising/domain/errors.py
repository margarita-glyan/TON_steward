from __future__ import annotations


class FundraisingError(Exception):
    """Base exception for all fundraising domain errors."""
    pass


class GoalNotFoundError(FundraisingError):
    """Raised when a requested goal does not exist."""
    pass


class GoalDraftNotFoundError(FundraisingError):
    """Raised when a requested goal draft does not exist."""
    pass


class NoPermissionError(FundraisingError):
    """Raised when an actor (e.g., non-admin) attempts a restricted action."""
    pass


class InvalidGoalStateTransitionError(FundraisingError):
    """Raised when an illegal state change is attempted (e.g., completed -> cancelled)."""
    pass


class GoalAlreadyCompletedError(FundraisingError):
    """Raised when an action is attempted on a goal that is already completed."""
    pass


class GoalAlreadyCancelledError(FundraisingError):
    """Raised when an action is attempted on a goal that is already cancelled."""
    pass


class DuplicateContributionError(FundraisingError):
    """Raised when a contribution with an already-processed tx_hash is submitted."""
    pass


class InvalidContributionError(FundraisingError):
    """Raised when contribution data is invalid (e.g., amount <= 0)."""
    pass


class DraftNotReviewableError(FundraisingError):
    """Raised when an admin tries to review a draft that is already approved or rejected."""
    pass


class GoalNotPayableError(FundraisingError):
    """Raised when a payment is attempted for a goal that is cancelled or completed."""
    pass
