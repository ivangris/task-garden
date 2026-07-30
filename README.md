# Task Garden

Task Garden is a local-first, desktop-first productivity app that turns spoken or typed brain-dumps into structured tasks and visualizes progress through an isometric pixel-art garden.

You start with a neglected desert plot. As you complete tasks, the garden is restored, planted, decorated, and brought to life. If you create tasks and leave them overdue, parts of the garden fall into disrepair. If you have no active tasks, there is no decay.

The app is built to work well in local-only mode first, while keeping the door open for optional cloud AI, multi-device sync, and future desktop/mobile packaging.

[MIT License](./LICENSE)

---

## Core features

- typed and voice-based task capture
- preservation of raw notes and transcripts
- AI-assisted task extraction with review before save
- task organization by project, priority, effort, energy, labels, and date
- Inbox, Tasks with date/status filters, Projects, Garden, Recaps, and Settings views
- deterministic recommendation engine
- isometric pixel-art garden meta-game
- weekly, monthly, and yearly accomplishment recaps
- provider-switchable architecture for local or cloud AI
- sync-ready design for future multi-device use

---

## Product principles

- **local-first**
- **single-user first**
- **review before commit**
- **deterministic validation around AI**
- **optional game layer**
- **optional cloud fallback**
- **calm, low-friction experience**

---

## Repo structure

```text
task-garden/
  AGENTS.md
  README.md
  docs/
  apps/
    web/
    api/
  packages/
    shared-types/
    shared-schemas/
    shared-prompts/
    ui-kit/
  assets/
  scripts/
  data/
  infra/
```

## Current personal-beta baseline

The current app includes:
- typed and microphone capture with preserved transcripts
- automatic local transcription and task extraction after recording
- review-and-confirm before extracted tasks are persisted
- Inbox, task filters, project management, recommendations, garden state, and recaps
- local Ollama and whisper.cpp provider paths with explicit readiness checks
- SQLite local mode plus a rehearsed optional Postgres/hosted API foundation
- backend, browser-smoke, migration, asset, and frontend build validation

The current garden is a functional v1 renderer. The next visual milestone is the cohesive Garden V2 oasis renderer described in [docs/RELEASE_BASELINE.md](./docs/RELEASE_BASELINE.md).

## Local development

### Web
```bash
npm install
npm run dev:web
```

### API
```bash
cd apps/api
python -m venv .venv
.venv\\Scripts\\activate
pip install -e .
uvicorn app.main:app --reload
```

### Database migration
```bash
cd apps/api
alembic upgrade head
```

### Local dictation setup

Use `whisper.cpp` for real local transcription on Windows:

```bash
TASK_GARDEN_STT_PROVIDER=whisper_cpp
TASK_GARDEN_STT_EXECUTABLE_PATH=C:\\path\\to\\whisper-cli.exe
TASK_GARDEN_STT_MODEL_PATH=C:\\path\\to\\ggml-base.en.bin
TASK_GARDEN_AUDIO_STORAGE_DIR=../../data/audio
```

If `whisper.cpp` is selected but the executable or model path is missing, Task Garden reports transcription as not configured. The deterministic STT stub is available only when explicitly selected for testing. After a recording stops, the app transcribes it, places the editable transcript in the composer, and starts extraction automatically.

### Local Ollama extraction setup

To use Ollama locally:

```bash
TASK_GARDEN_TASK_EXTRACTION_PROVIDER=ollama
TASK_GARDEN_OLLAMA_BASE_URL=http://127.0.0.1:11434
TASK_GARDEN_EXTRACTION_MODEL=gemma3:4b
TASK_GARDEN_EXTRACTION_TIMEOUT_SECONDS=60
```

Make sure Ollama is running and the selected model has been pulled locally. Settings can discover installed generation models; `gemma3:4b` is a practical example only when it is installed. If Ollama fails or returns malformed structured output, Task Garden preserves the raw entry and shows an extraction error instead of silently falling back to the mock extractor.

### Optional local recap narratives

To use a local Ollama recap narrative provider:

```bash
TASK_GARDEN_RECAP_NARRATIVE_PROVIDER=ollama
TASK_GARDEN_RECAP_MODEL=gemma3:4b
TASK_GARDEN_OLLAMA_BASE_URL=http://127.0.0.1:11434
```

You can also leave recap narratives `off` or use the deterministic `mock` provider for testing. If Ollama fails, recap cards and metrics still work, and the app records the narrative failure state instead of silently falling back.

### Extraction evaluation harness

You can compare local extraction targets against the sample corpus:

```bash
cd apps/api
.venv\Scripts\python scripts\eval_extraction_samples.py --target mock --target ollama:llama3.1:8b --target ollama:qwen2.5:7b
```

Add `--json` if you want machine-readable output.

### Browser QA harness

The browser smoke suite uses Playwright and an isolated QA SQLite database. Node `22.19.0` or newer is supported by the validated local baseline; the repo includes `.node-version`.

Install browsers once:

```bash
cd apps/web
npx playwright install chromium
```

Run the smoke suite from the repo root:

```bash
npm run qa:e2e
```

For headed inspection:

```bash
npm run qa:e2e:headed
```

The suite starts the FastAPI backend on `127.0.0.1:18000` with mock local providers and a reset QA database, then starts the Vite app on `127.0.0.1:15173` and verifies the core Capture, Inbox, Tasks, Projects, Garden, Recaps, and Settings flows.

Run the complete local release gate with:

```bash
npm run verify:baseline
```

This runs backend tests, frontend typecheck/build, garden asset validation, a clean temporary SQLite migration, and Playwright smoke tests.

### Demo data

Seed a deterministic demo database for visual QA:

```bash
npm run seed:demo -- --reset
```

The script prints the database URL to use when starting the API. It creates transcript/source material, active tasks, overdue tasks, completed tasks, projects, garden state, recommendations, and recaps.

Manual QA steps live in [docs/QA_CHECKLIST.md](./docs/QA_CHECKLIST.md).

## Optional hosted single-user mode

Task Garden remains local-first by default. The private hosted API foundation supports future multi-device sync, but it is not required for normal local use.

Hosted mode expects:
- a hosted FastAPI API
- Postgres-compatible database URL
- explicit CORS allowlist
- a single-user bearer token for write requests
- a frontend `VITE_API_BASE_URL` pointing at the hosted API

Minimal hosted API environment:

```bash
TASK_GARDEN_ENV=production
TASK_GARDEN_HOSTED_MODE=true
TASK_GARDEN_LOCAL_ONLY_MODE=false
TASK_GARDEN_DATABASE_URL=postgresql+psycopg://task_garden:REPLACE_ME@host:5432/task_garden
TASK_GARDEN_CORS_ALLOWED_ORIGINS=https://task-garden.example.com
TASK_GARDEN_AUTH_PROVIDER=bearer_token
TASK_GARDEN_SINGLE_USER_AUTH_TOKEN=replace-with-a-long-random-token
TASK_GARDEN_SYNC_PROVIDER=remote_api
```

When hosted mode is enabled, write requests require:

```text
Authorization: Bearer <TASK_GARDEN_SINGLE_USER_AUTH_TOKEN>
```

The example Docker Compose file is for local hosted-mode rehearsal only:

```bash
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/hosted-rehearsal.ps1 -Reset
```

Run migrations before using a hosted database:

```bash
cd apps/api
alembic upgrade head
```

See [docs/DEPLOYMENT_READINESS.md](./docs/DEPLOYMENT_READINESS.md) for the Phase 10B deployment plan and limitations.

Hosted mode stores transcripts and raw entries as durable data. Recorded audio remains temporary and is discarded after successful transcription unless a future explicit audio-storage feature is designed.

## Repository hygiene

- Keep only `.env.example` in version control
- Do not commit local SQLite databases, runtime logs, or generated audio/transcript artifacts
- Security issues should be reported privately; see [SECURITY.md](./SECURITY.md)
