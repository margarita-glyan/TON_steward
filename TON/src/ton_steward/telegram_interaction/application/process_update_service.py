from __future__ import annotations

from ton_steward.telegram_interaction.application.route_callback_service import RouteCallbackService
from ton_steward.telegram_interaction.application.route_message_service import RouteMessageService
from ton_steward.telegram_interaction.dto.requests import ProcessUpdateRequest
from ton_steward.telegram_interaction.dto.responses import ProcessUpdateResponse
from ton_steward.telegram_interaction.infrastructure.update_parser import parse_update


class ProcessUpdateService:
    def __init__(
        self,
        route_message_service: RouteMessageService,
        route_callback_service: RouteCallbackService,
    ) -> None:
        self._route_message_service = route_message_service
        self._route_callback_service = route_callback_service

    def process_update(self, req: ProcessUpdateRequest) -> ProcessUpdateResponse:
        try:
            update = parse_update(req.raw_update)
        except Exception:
            # In production, log the error
            return ProcessUpdateResponse(responses=[])

        responses = []

        if update.message:
            res = self._route_message_service.route_message(update.message)
            responses.extend(res)

        if update.callback_query:
            res = self._route_callback_service.route_callback(update.callback_query)
            responses.extend(res)

        return ProcessUpdateResponse(responses=responses)
