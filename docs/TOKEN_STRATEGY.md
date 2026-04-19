
---

## `docs/TOKEN_STRATEGY.md`

```md id="wgdb7x"
# Token Strategy

## Purpose

This document defines how to keep coding-assistant usage efficient while building Task Garden.

The goal is to reduce waste from:
- repeated project explanations
- oversized prompts
- unnecessary architectural restatement
- broad, multi-phase implementation requests
- avoidable retries from unstructured outputs

This project should be developed with deliberate context discipline.

---

## Core principles

### 1. Store stable context in the repo
The repo should hold the long-lived project context in markdown files.

This means:
- product vision lives in docs
- architecture lives in docs
- garden rules live in docs
- recap rules live in docs
- provider behavior lives in docs

Do not keep re-explaining the whole app in chat prompts once the repo docs exist.

### 2. Prompt one phase at a time
Do not ask for:
- full end-to-end implementation
- complete product builds in one pass
- backend + frontend + art + sync + recap all at once

Instead, ask for one bounded phase or subsystem.

### 3. Require short implementation summaries
When using coding assistants, request:
- files changed
- brief summary
- blockers

Avoid long narrative explanations unless debugging.

### 4. Prefer structured outputs
Use schemas and fixed response contracts wherever possible.

Structured outputs reduce:
- parsing retries
- repair prompts
- ambiguity
- token-heavy cleanup steps

### 5. Put static instructions first
Stable instruction prefixes are easier to reuse consistently across prompts and caching behavior.

Variable details should come later.

---

## Repo-based context strategy

These files should act as the primary context source:

- `AGENTS.md`
- `docs/BUILD_SPEC.md`
- `docs/ARCHITECTURE.md`
- `docs/TASK_SCHEMA.md`
- `docs/GARDEN_SYSTEM.md`
- `docs/RECAPS.md`
- `docs/PROVIDERS.md`
- `docs/API_CONTRACTS.md`

Before requesting code changes, prompt the agent to read only the relevant docs.

### Example
For garden work:
- `AGENTS.md`
- `docs/GARDEN_SYSTEM.md`
- `docs/ARCHITECTURE.md`

For recap work:
- `AGENTS.md`
- `docs/RECAPS.md`
- `docs/ARCHITECTURE.md`

For provider work:
- `AGENTS.md`
- `docs/PROVIDERS.md`
- `docs/API_CONTRACTS.md`

---

## Prompt design rules

### Good prompt characteristics
- specific
- scoped
- references repo docs
- names the exact subsystem
- asks for bounded output

### Bad prompt characteristics
- re-explains the whole app
- asks for many unrelated layers at once
- requests full rewrites
- asks for long explanations with every step
- omits which docs matter for the task

---

## Preferred prompt format

Use a pattern like this:

1. tell the agent which docs to read
2. define one clear implementation target
3. list hard constraints
4. define expected response format

### Template
```text
Read AGENTS.md and docs/<RELEVANT_DOC>.md first.

Implement <ONE BOUNDED FEATURE OR PHASE>.

Requirements:
- ...
- ...
- ...

Do not:
- ...
- ...

Return only:
1. files changed
2. brief summary
3. blockers or follow-up concerns