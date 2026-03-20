from __future__ import annotations

from sqlalchemy.engine import Engine

from ton_steward.db.base import Base
from ton_steward.db import models  # noqa: F401


def create_all(engine: Engine) -> None:
    Base.metadata.create_all(engine)

