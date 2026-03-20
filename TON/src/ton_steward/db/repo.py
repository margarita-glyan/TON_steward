from __future__ import annotations

from collections.abc import Callable
from contextlib import contextmanager

from sqlalchemy.orm import Session


SessionFactory = Callable[[], Session]


@contextmanager
def session_scope(session_factory: SessionFactory) -> Session:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

