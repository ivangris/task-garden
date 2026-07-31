# API Contracts

## Overview

This document defines the initial API surface for Task Garden.

The API should remain explicit, predictable, and boring. It should expose domain operations cleanly without leaking provider internals.

All request and response models should be defined using Pydantic schemas.

## General conventions

### Hosted single-user auth
Local development is unauthenticated by default. When `TASK_GARDEN_HOSTED_MODE=true` or `TASK_GARDEN_AUTH_PROVIDER=bearer_token`, mutating requests must include:

```text
Authorization: Bearer <single-user-token>
```

Read endpoints such as `GET /health` remain available for health checks. This is a private single-user boundary, not account management.

### Response principles
- return structured JSON
- include stable identifiers
- include timestamps where relevant
- prefer explicit status values
- avoid unbounded nested payloads when summary objects are enough

### Error principles
- preserve partial work when possible
- do not hide provider failures
- return actionable errors
- keep user-safe error messages at the API boundary

### Versioning
Initial implementation may be unversioned internally, but contracts should be written with future versioning in mind.

---

## Health and metadata

### `GET /health`
Returns API health status.

#### Response
```json
{
  "status": "ok"
}
```

## Local data safety

These routes are available only for a non-hosted, file-backed SQLite database. Backup files are constrained to `TASK_GARDEN_BACKUP_DIRECTORY`; restore requests cannot supply arbitrary filesystem paths.

### `GET /data-safety`

Returns backup readiness, the configured local database and backup locations, and available timestamped backups.

### `POST /data-safety/backups`

Creates a validated SQLite snapshot using SQLite's backup API.

### `POST /data-safety/restore`

Request:

```json
{
  "backup_name": "task-garden-manual-20260730-120000-000000.db",
  "confirmation": "RESTORE"
}
```

Before restoring, the service creates a `pre_restore` safety backup of the current database. The selected backup and restored database must both pass `PRAGMA quick_check`.

Hosted mode or a non-SQLite database returns `409`. Invalid, missing, or unsafe backup names return `422`.
