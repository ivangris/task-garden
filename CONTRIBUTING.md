# Contributing

Thanks for contributing to Task Garden.

## Before opening a change

- Read `AGENTS.md` and the relevant docs in `docs/`
- Keep changes small and phase-scoped
- Preserve local-first behavior
- Do not introduce required cloud dependencies

## Development

- Web: `npm install` then `npm run dev:web`
- API: `cd apps/api`, create `.venv`, `pip install -e .`, then `uvicorn app.main:app --reload`
- Migrations: `cd apps/api` then `alembic upgrade head`

## Pull requests

- Explain the user-facing goal briefly
- Note any docs updated
- Mention manual test steps
- Keep architecture boundaries intact: routers thin, persistence behind repositories, providers isolated

## Do not commit

- Secrets or real credentials
- Local database files
- Generated logs or audio/transcript artifacts
- Machine-specific config

