from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ton_steward.ai_intent.domain.analysis_result import IntentAnalysisResult
from ton_steward.ai_intent.dto.requests import AnalyzeWithContextRequest
from ton_steward.core.decision.schemas import DecisionAction, DecisionInput
from ton_steward.fundraising.dto.requests import (
    ApproveGoalDraftRequest,
    CancelGoalRequest,
    CompleteGoalRequest,
    CreateGoalDraftRequest,
    RegisterConfirmedContributionRequest,
    RejectGoalDraftRequest,
)
from ton_steward.fundraising.dto.responses import (
    ApproveGoalDraftResponse,
    CancelGoalResponse,
    ChatSummaryResponse,
    CompleteGoalResponse,
    CreateGoalDraftResponse,
    RegisterContributionResponse,
    RejectGoalDraftResponse,
)


class AiIntentService(Protocol):
    def analyze_with_context(self, req: AnalyzeWithContextRequest) -> IntentAnalysisResult: ...


class DecisionService(Protocol):
    def decide(self, inp: DecisionInput) -> DecisionAction: ...


class FundraisingCoreFacade(Protocol):
    def create_goal_draft(self, req: CreateGoalDraftRequest) -> CreateGoalDraftResponse: ...
    def approve_goal_draft(self, req: ApproveGoalDraftRequest) -> ApproveGoalDraftResponse: ...
    def reject_goal_draft(self, req: RejectGoalDraftRequest) -> RejectGoalDraftResponse: ...
    def get_chat_goal_summary(self, chat_id: int) -> ChatSummaryResponse: ...


class AdminDirectory(Protocol):
    def list_admin_user_ids(self, *, chat_id: int) -> list[int]: ...
    def is_admin(self, *, chat_id: int, user_id: int) -> bool: ...

