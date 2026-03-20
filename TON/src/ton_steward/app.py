from __future__ import annotations

import structlog

from ton_steward.config import Settings
from ton_steward.db.engine import create_engine_and_sessionmaker
from ton_steward.db.migrations import create_all
from ton_steward.scheduler.runner import start_scheduler
from ton_steward.telegram.bot import build_application


def main() -> None:
    settings = Settings()
    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(settings.log_level_value),
    )
    log = structlog.get_logger(__name__)

    engine, session_factory = create_engine_and_sessionmaker(settings.database_url)
    create_all(engine)

    scheduler = start_scheduler(settings=settings, session_factory=session_factory)

    app = build_application(settings=settings, session_factory=session_factory, scheduler=scheduler)
    log.info("ton_steward.starting")
    app.run_polling(close_loop=False)
