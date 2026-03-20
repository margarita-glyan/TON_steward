from __future__ import annotations

from enum import Enum


class GoalDraftStatus(str, Enum):
    """
    Status of a suggested fundraising goal before it is officially approved by an admin.
    """
    draft = "draft"
    pending_admin_review = "pending_admin_review"
    rejected = "rejected"
    approved_converted = "approved_converted"


class GoalState(str, Enum):
    """
    State of an active/official fundraising goal.
    """
    approved = "approved"  # Ready to accept first contribution
    funding = "funding"    # At least one contribution received, but not yet target
    funded = "funded"      # Target amount reached (funding can still happen until completed)
    completed = "completed" # Goal is officially finished and funds are distributed/used
    cancelled = "cancelled" # Goal was aborted by admin


class ContributionStatus(str, Enum):
    """
    Status of an individual payment attempt for a specific goal.
    """
    pending = "pending"
    confirmed = "confirmed"
    failed = "failed"
