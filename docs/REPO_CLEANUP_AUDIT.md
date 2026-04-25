# Repo Cleanup Audit

Date: 2026-04-24

## Scope

Phase 10A reviewed the current Phase 9F product UI/workflow changes and Phase 9E QA harness changes as one release-baseline worktree.

## Files Removed

Only generated or reproducible local artifacts were removed:

- `output/` - Playwright reports, traces, screenshots, and last-run metadata.
- `apps/web/dist/` - Vite production build output.
- `apps/web/tsconfig.tsbuildinfo` - TypeScript incremental build cache.
- `apps/api/**/__pycache__/` - Python bytecode caches produced by local tests and scripts.

No source files, migrations, provider stubs, docs, or asset files were deleted.

## Files Kept Despite Looking Suspicious

- `apps/api/app/providers/stubs.py` - still used for deterministic extraction, recap narrative testing, STT test fallback, and local-only sync behavior.
- `apps/api/app/garden/README.md` and `apps/api/app/recap/README.md` - placeholder package docs, but still useful package anchors and harmless.
- `apps/web/src/features/garden/asset-manifest.json` and `asset-manifest.ts` - both are intentional; JSON is the swappable asset map and TS provides typed access.
- `apps/web/public/assets/vendor/kenney/**` - all files are referenced by the garden asset manifest and recorded in `docs/ASSET_LEDGER.md`.
- `packages/shared-*` and `packages/ui-kit` placeholder packages - intentionally scaffolded for future shared contracts and UI extraction.
- `apps/api/app/db/migrations/versions/*.py` - all migrations are retained; migration history must not be rewritten.
- `data/audio/**`, `data/sqlite/**`, and `runtime-logs/**` - ignored local runtime/user artifacts. They were not deleted automatically because they may contain local user state.

## Ambiguous Items Requiring Future Decision

- `docs/BUILD_SPEC.md`, `docs/UX_NOTES.md`, `SKILL.md`, and `DESIGN.md` still describe the broad product vision; they were updated only where current primary navigation conflicted with the app.
- Placeholder package implementations under `packages/*/src/index.ts` are intentionally minimal. They can be expanded or removed only when shared packages are either adopted or declared out of scope.
- Future cloud provider placeholders remain documented but unimplemented. This is intentional until hosted single-user sync/cloud work starts.

## Current Ignored Generated Artifact Locations

- `apps/web/dist/`
- `apps/web/tsconfig.tsbuildinfo`
- `output/playwright/`
- `output/playwright-report/`
- `test-results/`
- `apps/api/**/__pycache__/`
- `data/sqlite/*.db`
- `data/audio/*`
- `runtime-logs/`
- `node_modules/`
- `.venv/` and `apps/api/.venv/`

## Audit Checks Performed

- Reviewed `git status --short` for all uncommitted Phase 9F/9E files.
- Checked tracked files for generated build/test/database/audio artifacts.
- Checked frontend screen component references.
- Checked backend router references.
- Checked garden asset manifest references against imported vendor assets.
- Searched docs for removed primary sidebar pages and updated current-navigation references.
- Searched for obvious secret patterns; findings were false positives such as local header names, test database names, or empty example variables.

## Suggested Future Cleanup

- Consider moving long-term product vision docs to explicitly distinguish "vision" from "current implementation" if the app keeps diverging from early IA.
- Add a real frontend unit-test runner only if component-level behavior becomes too expensive to cover through Playwright smoke tests.
- Revisit placeholder shared packages before Phase 10B if hosted contracts should be published from `packages/shared-schemas`.
