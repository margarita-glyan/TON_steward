from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from ton_steward.db.enums import AuditAction
from ton_steward.db.models import AuditLog


class AuditWriter:
    def __init__(self, session: Session):
        self.session = session

    def log(
        self,
        *,
        chat_id: int | None,
        actor_user_id: int | None,
        entity_type: str,
        entity_id: str,
        action: AuditAction,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        reason: str | None = None,
        source: str = "system",
    ) -> None:
        entry = AuditLog(
            chat_id=chat_id,
            actor_user_id=actor_user_id,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            old_value=old_value,
            new_value=new_value,
            reason=reason,
            source=source,
        )
        self.session.add(entry)

