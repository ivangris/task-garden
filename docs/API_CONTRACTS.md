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
