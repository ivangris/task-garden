# AGENTS.md

This repository contains **Task Garden**, a local-first, desktop-first productivity app that turns spoken or typed brain-dumps into structured tasks and visualizes progress through an isometric pixel-art garden.

## Read this first

Before making changes, read these files in order:

1. `docs/BUILD_SPEC.md`
2. `docs/ARCHITECTURE.md`
3. `docs/TASK_SCHEMA.md`
4. `docs/GARDEN_SYSTEM.md`
5. `docs/RECAPS.md`
6. `docs/PROVIDERS.md`

## Working principles

- Favor **domain clarity** over cleverness.
- Favor **small, testable changes** over broad rewrites.
- Keep **AI providers isolated** from business logic.
- Keep **persistence isolated** behind repositories.
- Keep **local-first operation** working at all times.
- Never make cloud services required for normal development.
- Never auto-save AI-extracted tasks without a **review-and-confirm** step.
- Never let model output directly mutate persistent state without deterministic validation.
- Prefer deterministic logic over AI when possible.
- Keep the UI calm, low-friction, and easy to scan.

## Product rules that must not be broken

- The app must work in **local-only mode**.
- Cloud AI providers may exist, but must be **disabled by default**.
- The user must be able to:
  - record audio or type text
  - preserve the raw original entry
  - review extracted tasks before saving
  - edit extracted tasks before saving
  - manage tasks without using voice or AI
- The garden may decay only when there are **overdue incomplete active tasks**.
- The garden must **not** decay when the user has **zero active tasks**.
- The game layer must remain **optional** and must not block task management.
- Weekly, monthly, and yearly recap features are part of the core product vision.

## Coding style

### General
- Keep functions small and named clearly.
- Prefer explicit types.
- Avoid premature abstraction unless it supports provider switching, persistence boundaries, or future sync.
- Use shared schemas/types where possible.
- Avoid introducing new dependencies without a strong reason.

### Frontend
- Use React + TypeScript.
- Keep components focused and composable.
- Separate presentational components from data-fetching/state logic.
- Keep accessibility in mind for keyboard flows, forms, and dialogs.
- Avoid over-animating the interface.

### Backend
- Use FastAPI.
- Use Pydantic models for all request/response contracts.
- Keep routers thin.
- Place domain logic in services/domain modules, not in routers.
- Use repositories for all persistence access.

### Data
- Use migrations for schema changes.
- Design schemas so they can move from SQLite to Postgres later with minimal friction.
- Include timestamps, device metadata, and sync metadata where appropriate.

## Output expectations for coding agents

When responding to implementation prompts:

- Do **not** restate the entire project spec.
- Summarize briefly.
- Return:
  1. files changed
  2. what was implemented
  3. any blockers or follow-up concerns
- Prefer diffs or focused updates over long explanations.

## Safe implementation boundaries

Do not:
- remove the review step
- hardcode API keys
- make OpenAI or any cloud API mandatory
- couple provider logic directly to UI components
- couple garden rendering directly to task storage logic
- generate recap narratives from raw unbounded history if deterministic summaries are available

Do:
- preserve raw user inputs
- validate all extracted task candidates
- snapshot recap metrics
- persist activity history
- make provider selection configurable
- make art assets replaceable

## Testing priorities

When adding or modifying features, prioritize tests for:

- task extraction normalization and validation
- review-and-confirm flow
- provider switching
- no-decay-when-zero-active-tasks rule
- recommendation generation
- recap metric generation
- sync event generation and replay