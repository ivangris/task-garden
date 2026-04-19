# Architecture

## Overview

Task Garden uses a **local-first, provider-switchable, monorepo architecture**.

The system should be designed so that:
- local-only operation is the default
- cloud providers can be plugged in without changing domain logic
- SQLite can be replaced or complemented by Postgres later
- the same domain rules drive task management, garden updates, and recap generation

## Architectural principles

### 1. Domain-first
Business rules belong in domain services, not in routers or UI components.

### 2. Provider isolation
Speech-to-text, extraction, narrative generation, auth, and sync providers must be isolated behind interfaces.

### 3. Persistence isolation
Persistence access must go through repositories.

### 4. Local-first
The default runtime path should not depend on external services.

### 5. Replaceability
Art assets, models, providers, and storage backends should be replaceable.

### 6. Deterministic core
AI can suggest structure and narrative, but deterministic code should validate, persist, score, and summarize.

## Monorepo layout

```text
task-garden/
  apps/
    web/
    api/
  packages/
    shared-types/
    shared-schemas/
    shared-prompts/
    ui-kit/
  docs/
  assets/
  scripts/
  data/