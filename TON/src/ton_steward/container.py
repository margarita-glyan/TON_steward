# src/ton_steward/container.py

from dependency_injector import containers, providers
from dependency_injector.wiring import inject, Provide

# Assuming Config is correctly implemented and available in config.py
from .config import Config 

# Assuming DB components are correctly implemented in db
from .db.engine import create_db_engine, DatabaseEngine
from .db.repo import SQLAlchemyFundraisingRepository, FundraisingRepository

# Core modules (including assumed Decision Layer, Audit, Goals)
from .core.decision.services import DecisionService
from .core.audit.services import AuditService
from .core.goals.services import GoalsService

# Fundraising module
from .fundraising.application.services import FundraisingService
from .fundraising.domain.services import FundraisingDomainService

# Payments module
from .payments.application.services import PaymentsService

# AI Intent module
from .ai_intent.application.services import AIIntentService

# Telegram Interaction module
from .telegram_interaction.application.services import TelegramInteractionService

class Container(containers.DeclarativeContainer):
    # --- Configuration ---
    # Assuming Config class can be instantiated without arguments, or with a path to config file if needed.
    # For now, assuming it's a simple singleton.
    config = providers.Singleton(Config)

    # --- Database ---
    # Assuming create_db_engine uses config.db_url
    db_engine: providers.Provider[DatabaseEngine] = providers.Singleton(
        create_db_engine,
        db_url=config.provided.db_url, # Accessing db_url from the provided config instance
    )
    
    # --- Repositories ---
    # Factory for repositories that might need a new session per use
    fundraising_repo: providers.Provider[FundraisingRepository] = providers.Factory(
        SQLAlchemyFundraisingRepository,
        session_factory=db_engine.provided.session_factory, # Assuming db_engine provides a session_factory
    )

    # --- Domain Services ---
    # These services encapsulate core business logic and depend on repositories
    fundraising_domain_service = providers.Factory(
        FundraisingDomainService,
        repo=fundraising_repo,
    )

    # --- Core Services ---
    # Wiring assumed services from core directory
    decision_service = providers.Factory(
        DecisionService,
        fundraising_repo=fundraising_repo, # Example: Decision service might need repo access
        fundraising_domain_service=fundraising_domain_service, # Example: Depends on fundraising domain logic
    )
    audit_service = providers.Factory(AuditService) # Assuming AuditService has no external dependencies for now
    goals_service = providers.Factory(GoalsService)   # Assuming GoalsService has no external dependencies for now

    # --- Application Services ---
    # These services orchestrate domain logic and interact with other application services
    fundraising_service = providers.Factory(
        FundraisingService,
        fundraising_repo=fundraising_repo,
        fundraising_domain_service=fundraising_domain_service,
        decision_service=decision_service,
        audit_service=audit_service,
        goals_service=goals_service,
        config=config, # Application services often need configuration
    )

    payments_service = providers.Factory(
        PaymentsService,
        fundraising_repo=fundraising_repo, # Payments might need to record transactions in the DB
        # Add specific payment-related dependencies here as they are defined
        config=config,
    )

    ai_intent_service = providers.Factory(
        AIIntentService,
        # Add AI-specific dependencies here (e.g., LLM client, API keys from config)
        config=config,
    )

    telegram_interaction_service = providers.Factory(
        TelegramInteractionService,
        # Telegram bot will interact with other services
        fundraising_service=fundraising_service,
        payments_service=payments_service,
        ai_intent_service=ai_intent_service,
        decision_service=decision_service, # Bot commands might trigger decisions
        config=config,
    )

# To use this container, you would typically wire it in your application's entry point (e.g., app.py or __main__.py)
# Example wiring in __main__.py or app.py:
#
# from .container import Container
#
# container = Container()
#
# # Wire the container to the modules that will use dependency injection
# # The 'modules' parameter should contain the modules where @inject decorators are used.
# # For example, if your bot handlers are in ton_steward.telegram_interaction.application.handlers,
# # you would include that module here.
# container.wire(modules=[
#     __name__, # For the main entry point if it uses injection
#     # Add other modules that use @inject, e.g.:
#     # "ton_steward.telegram_interaction.application.handlers", 
#     # "ton_steward.fundraising.application.handlers",
# ])
#
# # Then, you can inject services into functions or classes like this:
# @inject
# def main_application(
#     telegram_service: TelegramInteractionService = Provide[Container.telegram_interaction_service]
# ):
#     # Now you can use telegram_service
#     telegram_service.run_bot()
#
# if __name__ == "__main__":
#     main_application()
