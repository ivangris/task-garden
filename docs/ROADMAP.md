
---

## `docs/ROADMAP.md`

```md id="m1ev7x"
# Roadmap

## Overview

This roadmap describes the staged implementation plan for Task Garden.

The guiding strategy is:

1. make the app useful early
2. keep local-first operation intact
3. avoid rewriting core architecture later
4. add game and recap depth on top of a solid capture/planning foundation

---

## Phase 0 — foundation

### Goal
Establish project structure and architectural boundaries.

### Deliverables
- monorepo scaffold
- docs scaffold
- shared types and schemas package
- FastAPI app shell
- React app shell
- environment config structure
- provider interface definitions
- repository interface definitions
- migration setup

### Done when
- the project runs locally
- docs exist and reflect current intent
- providers and repositories are defined even if stubs only

---

## Phase 1 — core task system

### Goal
Make the app useful without audio or the garden.

### Deliverables
- typed/pasted raw entry creation
- raw entry persistence
- extraction batch persistence
- manual task creation
- extraction review screen
- confirm-and-save flow
- task persistence
- Inbox view
- Today view
- This Week view
- Projects view
- Completed view
- search and filters
- activity event logging

### Done when
- the user can enter text, review task candidates, save tasks, and manage them

---

## Phase 2 — local dictation

### Goal
Add the main “magic” interaction: speak naturally, get structured tasks.

### Deliverables
- microphone capture UI
- local audio handling
- transcription provider integration
- transcript persistence
- transcript preview
- extraction-from-transcript flow
- retry and fallback handling

### Done when
- the user can record audio and create reviewed tasks from the transcription result

---

## Phase 3 — provider switching

### Goal
Support local-first by default while preparing for cloud fallback.

### Deliverables
- settings UI for provider selection
- local extraction provider
- local STT provider
- optional cloud transcription provider
- optional cloud extraction provider
- provider-specific normalization
- disabled-by-default cloud behavior
- configuration validation

### Done when
- providers can be swapped without changing business logic
- the app still works in local-only mode

---

## Phase 4 — planning and recommendation engine

### Goal
Give the user practical help before adding deeper game complexity.

### Deliverables
- stale task detection
- overloaded week detection
- neglected project detection
- large task breakdown suggestions
- small wins suggestions
- recommendation snapshots
- optional weekly coach placeholder

### Done when
- the app can highlight problems and propose actionable next steps deterministically

---

## Phase 5 — garden domain

### Goal
Implement the reward and repair model behind the garden.

### Deliverables
- garden state model
- XP ledger
- unlock ledger
- decay event model
- recovery event model
- tile/zone model
- recompute service
- no-decay-with-zero-active-tasks rule
- initial unlock tables

### Done when
- garden state can be computed from task and activity history
- the core rules are tested

---

## Phase 6 — garden UI v1

### Goal
Make the garden visible and satisfying.

### Deliverables
- placeholder pixel-art asset pipeline
- isometric tile rendering
- restored vs decayed tiles
- basic plants and decorations
- fountain state changes
- unlock visualization
- zone highlighting
- lightweight animation hooks

### Done when
- completing tasks visibly improves the garden
- overdue active tasks visibly create repairable disrepair

---

## Phase 7 — recap engine

### Goal
Turn activity history into motivating summaries.

### Deliverables
- weekly recap metrics
- monthly recap metrics
- yearly recap metrics
- recap period persistence
- milestone detection
- highlight card generation
- recap UI shell
- optional narrative provider hook
- “Look at all you accomplished” opening state

### Done when
- the user can open recap views and see deterministic accomplishment summaries

---

## Phase 8 — sync readiness

### Goal
Prepare for multi-device use without breaking local-first operation.

### Deliverables
- device model
- change event log
- sync cursor model
- push/pull endpoints
- sync-ready repositories
- import/export utilities
- remote sync provider stub
- local-only default preserved

### Done when
- the system can support a future hosted backend without changing core domain rules

---

## Phase 9 — polish and packaging readiness

### Goal
Make the system stable, testable, and ready for future packaging.

### Deliverables
- improved empty states
- keyboard shortcuts
- dark mode polish
- better error states
- accessibility improvements
- test coverage expansion
- packaging review for Tauri readiness
- performance review
- asset replacement strategy

### Done when
- the app feels stable and coherent as a real personal tool

---

## Possible future phases

### Phase 10 — hosted single-user sync
- Postgres backend
- simple auth
- multi-device sync

### Phase 11 — richer garden systems
- seasonal themes
- biome variants
- more plant families
- collectible decoration sets

### Phase 12 — export and sharing
- export recap cards
- printable monthly/yearly summaries
- personal archive view

### Phase 13 — mobile adaptation
- iOS and Android client adaptation
- touch-first garden interactions
- mobile audio flow optimization

---

## Priority order summary

### Highest priority
- capture
- review
- task persistence
- task views

### Medium priority
- transcription
- provider switching
- recommendations

### High-value differentiators
- garden
- recaps

### Later
- sync
- packaging
- mobile
- export

---

## Risks and mitigations

### Risk: too much complexity too early
**Mitigation:** keep one phase per prompt and validate before moving on

### Risk: garden overwhelms productivity core
**Mitigation:** make the game layer optional and build it after core task flows work

### Risk: cloud fallback complicates architecture
**Mitigation:** isolate providers from business logic and disable cloud by default

### Risk: recap generation becomes token-heavy
**Mitigation:** compute deterministic metrics first and generate narrative only from compact summaries

### Risk: sync causes architecture drift
**Mitigation:** use repositories and change events early, but postpone real hosting

---

## Definition of “first compelling version”

A first compelling version exists when the user can:

- speak or type a raw entry
- preserve that input
- review extracted tasks
- save and manage them
- complete tasks
- see the garden improve
- open a weekly recap and feel progress