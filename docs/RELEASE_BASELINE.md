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
- timestamped local SQLite backup and validated restore

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
- Attachments are represented in the composer UI but are not yet persisted as source material.
- Hosted mode is a private rehearsal foundation, not a public production deployment.
- Sync uses single-user last-write-wins assumptions.
- Desktop packaging and mobile clients are not implemented.

## Data Safety

- Create local backups from Settings before important changes.
- Restore accepts only backups from the configured backup directory and creates a pre-restore safety backup first.
- Set `TASK_GARDEN_BACKUP_DIRECTORY` to another drive for stronger protection.
- Keep both the active database and backup directory out of version control.
- Never run demo reset commands against the normal personal database.
- Run `npm run verify:data-safety` to rehearse backup and restore against temporary data.

## Next Checkpoint

Begin Garden V2 from the approved oasis direction while preserving the existing garden API and deterministic domain rules.
