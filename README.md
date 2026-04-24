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
- Inbox, Today, This Week, Projects, Completed, and Search views
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

## Phase 0 scaffold

This repository now includes:
- `apps/web`: React + TypeScript + Vite desktop shell
- `apps/api`: FastAPI app shell with provider and repository interfaces
- `packages/*`: placeholder shared packages for types, schemas, prompts, and UI kit
- `data/sqlite`: local SQLite target directory

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

The default Phase 2 transcription path stays fully local and testable with the built-in deterministic STT stub.

If you want to try `whisper.cpp` on Windows, configure these environment variables before starting the API:

```bash
TASK_GARDEN_STT_PROVIDER=whisper_cpp
TASK_GARDEN_STT_EXECUTABLE_PATH=C:\\path\\to\\whisper-cli.exe
TASK_GARDEN_STT_MODEL_PATH=C:\\path\\to\\ggml-base.en.bin
TASK_GARDEN_AUDIO_STORAGE_DIR=../../data/audio
```

If `whisper.cpp` is selected but the executable or model path is missing, Task Garden reports transcription as not configured. The deterministic STT stub remains available only when explicitly selected for testing.

### Local Ollama extraction setup

Phase 3A adds an explicit local extraction provider choice between `mock` and `ollama`.

To use Ollama locally:

```bash
TASK_GARDEN_TASK_EXTRACTION_PROVIDER=ollama
TASK_GARDEN_OLLAMA_BASE_URL=http://127.0.0.1:11434
TASK_GARDEN_EXTRACTION_MODEL=llama3.1:8b
TASK_GARDEN_EXTRACTION_TIMEOUT_SECONDS=60
```

Make sure Ollama is running and the selected model has been pulled locally. If Ollama fails or returns malformed structured output, Task Garden preserves the raw entry and shows an extraction error instead of silently falling back to the mock extractor.

### Optional local recap narratives

Phase 7B keeps recap metrics deterministic and adds an explicit optional narrative layer on top.

To use a local Ollama recap narrative provider:

```bash
TASK_GARDEN_RECAP_NARRATIVE_PROVIDER=ollama
TASK_GARDEN_RECAP_MODEL=llama3.1:8b
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

## Repository hygiene

- Keep only `.env.example` in version control
- Do not commit local SQLite databases, runtime logs, or generated audio/transcript artifacts
- Security issues should be reported privately; see [SECURITY.md](./SECURITY.md)
