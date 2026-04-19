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

## Repository hygiene

- Keep only `.env.example` in version control
- Do not commit local SQLite databases, runtime logs, or generated audio/transcript artifacts
- Security issues should be reported privately; see [SECURITY.md](./SECURITY.md)
