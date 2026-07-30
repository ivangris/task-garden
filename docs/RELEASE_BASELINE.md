# Personal Beta Release Baseline

Date: 2026-07-29

## Purpose

This checkpoint defines the first release state intended for regular single-user local use. It preserves Task Garden's local-first architecture and records what is validated, what remains intentionally limited, and what must happen before the garden visual overhaul.

## Included

- typed and microphone capture
- real local whisper.cpp transcription when configured
- automatic transcription and extraction after recording stops
- editable transcript in the composer
- review-and-confirm extraction workflow
- manual and extracted task persistence
- task date, status, and project filters
- project create, edit, and delete behavior
- deterministic recommendations
- deterministic garden state and v1 renderer
- weekly, monthly, and yearly recaps
- optional local Ollama recap reflection
- optional single-user hosted API foundation and sync contracts

## Validated Local Runtime

- Windows PowerShell
- Node 22.19.0 or newer
- React, TypeScript, and Vite frontend
- Python virtualenv under `apps/api/.venv`
- FastAPI and SQLite
- Ollama at a configurable local base URL
- whisper.cpp at configurable executable and model paths

## Release Gate

Run:

```powershell
npm run verify:baseline
```

The command verifies:

- backend unit and API tests
- frontend TypeScript
- frontend production build
- garden asset manifest
- Alembic migrations against a new temporary SQLite database
- Playwright browser smoke tests

Optional gates:

```powershell
npm run verify:baseline -- -SeedDemo
npm run verify:baseline -- -Hosted
```

`-SeedDemo` intentionally resets only the documented demo database. `-Hosted` runs the Docker/Postgres hosted rehearsal and requires Docker Desktop.

## Known Limitations

- The garden v1 renderer is functional but visually inconsistent. Garden V2 is the next product-design milestone.
- There is no first-class local backup and restore command yet. Do not rely on a single unprotected SQLite database for important personal history.
- Attachments are represented in the composer UI but are not yet persisted as source material.
- Hosted mode is a private rehearsal foundation, not a public production deployment.
- Sync uses single-user last-write-wins assumptions.
- Desktop packaging and mobile clients are not implemented.

## Data Safety Until Backup Exists

- Keep `data/sqlite/task-garden.db` out of version control.
- Stop the API before manually copying the database.
- Store any manual copy outside the repository and outside the same physical disk when possible.
- Never run demo reset commands against the normal personal database.

## Next Checkpoint

Implement explicit local SQLite backup and restore with safe destination validation, timestamped backups, and a documented recovery test. Garden V2 implementation should begin only after that data-safety checkpoint is validated.
