# TON Steward (MVP)

AI-powered Telegram agent for turning group intent into admin-approved fundraising goals, tracking contributions (TON), and enforcing transparency.

## Architecture

- `src/ton_steward/telegram/` Telegram Bot API handling
- `src/ton_steward/ai/` intent detection + structured extraction (LLM behind an interface; MVP stub included)
- `src/ton_steward/core/` business logic (drafts, approvals, multi-goal, contributions)
- `src/ton_steward/payments/` TON integration (MVP mock + verification interface)
- `src/ton_steward/db/` models and repositories
- `src/ton_steward/scheduler/` reminders and periodic jobs
- `src/ton_steward/auth/` admin validation and role mapping

## Quickstart (local)

1) Create a venv and install deps:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Copy env:

```bash
cp .env.example .env
```

3) Run (uses SQLite by default):

```bash
python -m ton_steward
```

## Notes

- MVP uses SQLite by default for convenience; set `DATABASE_URL` to use Postgres.
- TON verification is mocked behind an interface so real on-chain checks can be swapped in.
