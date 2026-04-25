# Deployment Readiness

## Current Baseline

Task Garden is currently a local-first single-user app with:

- React + TypeScript + Vite frontend in `apps/web`.
- FastAPI backend in `apps/api`.
- SQLite persistence by default.
- Alembic migrations for schema evolution.
- Local provider settings for STT, extraction, recap narrative, sync, and auth stubs.
- Optional local Ollama extraction/narrative providers.
- Optional local whisper.cpp STT provider.
- Deterministic mock providers for QA and tests.
- Playwright smoke tests that run against isolated local QA ports.

## Local-Only Today

These parts are intentionally local-only:

- SQLite database path via `TASK_GARDEN_DATABASE_URL`.
- Local audio/transcript handling.
- Local provider readiness checks.
- Local-only sync provider.
- No production auth provider.
- No hosted remote sync provider.
- No cloud AI provider implementation.

## Expected Hosted Single-User Components

Phase 10B should define and implement:

- Hosted FastAPI runtime.
- Managed Postgres database.
- Production migration execution.
- Single-user authentication.
- Remote sync API persistence and cursor handling.
- Secret management for provider keys if cloud providers are later enabled.
- Frontend deployment target and API base URL configuration.
- Environment-specific CORS origins.
- Logging/observability appropriate for a hosted single-user service.

## Environment Variables

Required or expected for local/dev:

- `VITE_API_BASE_URL`
- `TASK_GARDEN_ENV`
- `TASK_GARDEN_API_HOST`
- `TASK_GARDEN_API_PORT`
- `TASK_GARDEN_DATABASE_URL`
- `TASK_GARDEN_LOCAL_ONLY_MODE`
- `TASK_GARDEN_CLOUD_ENABLED`
- `TASK_GARDEN_STT_PROVIDER`
- `TASK_GARDEN_STT_MODEL`
- `TASK_GARDEN_STT_EXECUTABLE_PATH`
- `TASK_GARDEN_STT_MODEL_PATH`
- `TASK_GARDEN_TASK_EXTRACTION_PROVIDER`
- `TASK_GARDEN_EXTRACTION_MODEL`
- `TASK_GARDEN_RECAP_NARRATIVE_PROVIDER`
- `TASK_GARDEN_RECAP_MODEL`
- `TASK_GARDEN_OLLAMA_BASE_URL`
- `TASK_GARDEN_EXTRACTION_TIMEOUT_SECONDS`
- `TASK_GARDEN_AUDIO_STORAGE_DIR`
- `TASK_GARDEN_SYNC_PROVIDER`
- `TASK_GARDEN_SYNC_BASE_URL`
- `TASK_GARDEN_AUTH_PROVIDER`

Cloud/provider secrets must not be committed. `.env.example` keeps cloud API key fields empty.

## Database And Migrations

Current behavior:

- SQLite is default.
- Alembic migrations apply from an empty database.
- Local reset is manual and should be explicit.

Safe local reset pattern:

```powershell
Stop the API first.
Move or delete only the intended local DB under data\sqlite\.
cd apps\api
$env:TASK_GARDEN_DATABASE_URL="sqlite:///C:/dev/task-garden/data/sqlite/task-garden.db"
.\.venv\Scripts\alembic.exe upgrade head
```

Hosted readiness needs:

- Postgres URL support verification.
- Migration transaction behavior review under Postgres.
- Backup/restore plan before any production migration.
- Seed/demo scripts must never target production databases by default.

## Sync Considerations

Existing sync readiness includes:

- Devices.
- Change events.
- Sync cursors.
- Push/pull contracts.
- Local-only default behavior.

Phase 10B decisions:

- Whether hosted sync uses the same FastAPI app or a separate service boundary.
- Whether last-write-wins remains acceptable for the first hosted single-user sync.
- How device identity is persisted and rotated.
- How auth identity maps to the single-user dataset.

## Auth And Security Considerations

Current auth is a placeholder and should not be considered production-ready.

Before hosted deployment:

- Add a real auth provider or a safe single-user access gate.
- Define CORS allowlist per environment.
- Define secret loading from the hosting platform.
- Ensure provider errors remain sanitized at API boundaries.
- Ensure raw entries, transcripts, and recaps are treated as private user data.
- Decide whether local audio should ever be uploaded or whether hosted mode remains transcript-only.

## QA Baseline

Run before Phase 10B:

```powershell
npm run build:web
npm run check:garden-assets
npm run qa:e2e
npm run seed:demo -- --reset
cd apps\api
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\alembic.exe upgrade head
```

For a clean migration sanity check, use a temporary SQLite database path instead of the normal user database.

## Open Decisions For Phase 10B

- Hosted platform target.
- Postgres provider and connection management.
- Auth provider.
- Production CORS and frontend API URL strategy.
- Remote sync deployment shape.
- Whether hosted mode stores audio, transcripts only, or both.
- Whether cloud AI remains out of scope for hosted sync launch.
