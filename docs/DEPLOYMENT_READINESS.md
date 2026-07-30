# Deployment Readiness

## Phase 10C Baseline

Task Garden remains local-first by default. Phase 10C validates the private hosted single-user API foundation locally with Docker, Postgres, Alembic migrations, bearer-token auth, CORS, hosted frontend configuration, and sync push/pull contracts.

This is deployment scaffolding, not a production SaaS launch. There are no user accounts, teams, OAuth flows, hosted cloud AI providers, or collaborative editing guarantees.

## Intended Hosted Shape

- Web frontend: static Vite build pointed at either local API or hosted API through `VITE_API_BASE_URL`.
- API backend: FastAPI app from `apps/api`, deployable directly or through the API Dockerfile.
- Database: SQLite for local development, Postgres-compatible URL for hosted mode.
- Auth boundary: single-user bearer token for mutating hosted API requests.
- Sync: existing device, change event, and cursor contracts remain the backbone for future remote sync.
- Provider mode: local/mock providers remain valid; cloud AI providers stay disabled/unimplemented in this phase.
- Fallback: local SQLite mode remains the normal development path and does not require auth or Docker.

## Recommended Deployment Path

1. Deploy the FastAPI API as a private single-user service.
2. Provision a managed Postgres database.
3. Run Alembic migrations against the hosted database.
4. Set a long random `TASK_GARDEN_SINGLE_USER_AUTH_TOKEN`.
5. Set `TASK_GARDEN_CORS_ALLOWED_ORIGINS` to the exact frontend origin.
6. Build/deploy the web app with `VITE_API_BASE_URL` set to the hosted API URL.
7. Configure the frontend token only in a private deployment context.

## Alternative Path

For a low-friction private install, run the example Docker Compose stack on a trusted machine or VPS. This is useful for rehearsal and personal experimentation, but it is not a hardened production recipe.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\hosted-rehearsal.ps1 -Reset
```

## Environment Variables

### Frontend

- `VITE_API_BASE_URL` - local default is `http://127.0.0.1:8000`; hosted builds should use the hosted API URL.
- `VITE_API_AUTH_TOKEN` - optional private hosted token. Leave unset for local development.

### Backend Runtime

- `TASK_GARDEN_ENV` - `development` locally, `production` when hosted.
- `TASK_GARDEN_API_HOST` - local bind host for non-container runs.
- `TASK_GARDEN_API_PORT` - local bind port for non-container runs.
- `TASK_GARDEN_DATABASE_URL` - SQLite URL locally; `postgresql+psycopg://...` for hosted Postgres.
- `TASK_GARDEN_CORS_ALLOWED_ORIGINS` - comma-separated allowlist. Use exact origins in hosted mode.
- `TASK_GARDEN_HOSTED_MODE` - `false` locally, `true` for private hosted API mode.
- `TASK_GARDEN_SINGLE_USER_AUTH_TOKEN` - required for hosted write access.
- `TASK_GARDEN_AUTH_PROVIDER` - `none` locally, `bearer_token` in hosted mode.
- `TASK_GARDEN_SYNC_PROVIDER` - `local_only` locally, `remote_api` when rehearsing hosted sync.
- `TASK_GARDEN_LOCAL_ONLY_MODE` - `true` locally, usually `false` when hosted.
- `TASK_GARDEN_CLOUD_ENABLED` - remains `false` in Phase 10B.
- `TASK_GARDEN_LOGGING_LEVEL` - runtime log level hint for hosting environments.

### Provider Variables

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

Cloud provider keys must stay unset unless a future phase explicitly implements cloud providers.

## Local Hosted-Mode Rehearsal

Prerequisites:

- Docker Desktop running with Linux containers.
- Node/npm dependencies installed.
- API virtualenv available for non-Docker validation.

Run the automated rehearsal:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\hosted-rehearsal.ps1 -Reset
```

The rehearsal:

- builds the API Docker image
- starts Postgres in Docker Compose
- runs Alembic migrations against Postgres
- starts the hosted API on `http://127.0.0.1:18080`
- confirms `GET /health`
- confirms unauthenticated writes return `401`
- confirms authenticated writes succeed
- registers a sync device
- pulls change events with a cursor
- pushes a sync change event

The compose database is intentionally not published to a host port, which avoids conflicts with local Postgres installations. Use `docker compose exec db ...` for database inspection during rehearsal.

## Auth Boundary

Hosted mode protects write methods: `POST`, `PUT`, `PATCH`, and `DELETE`.

Clients must send:

```text
Authorization: Bearer <TASK_GARDEN_SINGLE_USER_AUTH_TOKEN>
```

If hosted mode is enabled and no token is configured, write requests fail closed with `503`. If the token is missing or invalid, write requests return `401`.

This boundary is intentionally simple. It is suitable only for a private single-user deployment behind TLS. It is not account management and does not provide roles, registration, password reset, or multi-user isolation.

## Database And Migrations

SQLite remains the default:

```powershell
cd apps\api
$env:TASK_GARDEN_DATABASE_URL="sqlite:///C:/dev/task-garden/data/sqlite/task-garden.db"
.\.venv\Scripts\alembic.exe upgrade head
```

Hosted Postgres rehearsal:

```powershell
cd apps\api
$env:TASK_GARDEN_DATABASE_URL="postgresql+psycopg://task_garden:REPLACE_ME@host:5432/task_garden"
.\.venv\Scripts\alembic.exe upgrade head
```

Migration notes:

- Do not delete or rewrite existing Alembic migration files.
- Run migrations before starting the hosted API.
- Back up hosted data before migrations once real data exists.
- Demo seed scripts must not target production databases by default.

## Sync Behavior

The current sync contract remains:

- devices register with `/sync/register-device`
- local mutations emit `change_events`
- `/sync/push` accepts client-side change envelopes
- `/sync/pull` returns cursor-based server changes
- cursors track per-device progress

Phase 10B keeps single-user assumptions. Last-write-wins behavior is acceptable for the first private sync foundation, but it can overwrite competing device edits if the same entity changes on multiple devices before sync.

## Docker Scaffolding

API Dockerfile:

```powershell
docker build -f apps/api/Dockerfile -t task-garden-api .
```

Hosted rehearsal stack:

```powershell
docker compose -p task-garden-hosted -f docker-compose.hosted.example.yml up --build
```

Docker is optional. Normal local development should continue to use the existing Python virtualenv and Vite scripts.

## Security Notes

- Never commit real `.env` files or hosted tokens.
- Use exact CORS origins in hosted mode; do not use wildcard origins.
- Use TLS in front of the hosted API.
- Treat raw entries, transcripts, tasks, recaps, and sync payloads as private user data.
- The frontend token approach is acceptable only for a private single-user deployment. A broader product would need real server-side session/auth architecture.

## Transcript And Audio Policy

Hosted mode stores transcripts, raw entries, task data, recaps, garden state, and sync metadata as durable data. It does not store durable audio recordings after successful transcription. Audio upload handling remains temporary, and `audio_file_ref` should be cleared after transcription succeeds.

If transcription fails, retry behavior should preserve enough temporary state for the current attempt where the runtime supports it. Cloud object storage is intentionally out of scope for Phase 10C.

## Validation Baseline

Run before hosted deployment work continues:

```powershell
npm run build:web
npm run typecheck:web
npm run check:garden-assets
npm run qa:e2e
npm run seed:demo -- --reset
cd apps\api
.\.venv\Scripts\python.exe -m unittest discover -s tests
.\.venv\Scripts\alembic.exe upgrade head
```

For clean migration sanity, point `TASK_GARDEN_DATABASE_URL` at a temporary SQLite DB instead of the normal local user database.

## Manual Deployment Checklist

- Confirm hosted environment variables are set through the hosting platform, not committed files.
- Confirm database connectivity from the API runtime.
- Run Alembic migrations.
- Confirm `GET /health` works.
- Confirm a write request fails without bearer token.
- Confirm the same write succeeds with bearer token.
- Confirm frontend uses the hosted API URL.
- Confirm hosted frontend CORS preflight succeeds from the exact frontend origin.
- Confirm hosted transcript flow clears `audio_file_ref` after successful transcription.
- Confirm local-only mode still runs without hosted env vars.

## Rollback And Reset Considerations

- Local reset: stop the API, move or delete only the intended local SQLite DB, then rerun migrations.
- Hosted rollback: restore a database backup and redeploy the previous API image/revision.
- Do not run demo seed reset against hosted production data.

## Checklist For Phase 10D

- Final hosted platform target.
- Managed Postgres provider.
- Secret management path for the single-user token.
- TLS/reverse proxy setup.
- Hosted frontend deployment target and private-token handling.
- Production migration execution process.
- Backup/restore process for Postgres.
- Whether the private frontend-token model is enough for the first personal deployment or should be replaced before real hosted use.
- First end-to-end multi-device sync rehearsal.
