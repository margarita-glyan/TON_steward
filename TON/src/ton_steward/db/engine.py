from __future__ import annotations

from collections.abc import Callable

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


SessionFactory = Callable[[], Session]


def create_engine_and_sessionmaker(database_url: str) -> tuple[Engine, SessionFactory]:
    connect_args: dict[str, object] = {}
    if database_url.startswith("sqlite:"):
        # Needed for SQLite + threads (PTB runs handlers in an event loop)
        connect_args["check_same_thread"] = False

    engine = create_engine(database_url, future=True, connect_args=connect_args)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)
    return engine, factory

