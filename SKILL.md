# SKILL.md

## Purpose

This skill file defines how AI coding/design agents should build the interface and user-facing experience for **Task Garden**.

Task Garden is a local-first, desktop-first productivity app that turns spoken or typed brain-dumps into structured tasks and visualizes progress through an isometric pixel-art garden.

This file is primarily about:
- interface quality
- visual direction
- UX priorities
- screen behavior
- component choices
- implementation tone

It does **not** replace the product and architecture docs.
It complements them.

---

## Read these before making UI or front-end decisions

Read in this order:

1. `AGENTS.md`
2. `docs/BUILD_SPEC.md`
3. `docs/ARCHITECTURE.md`
4. `docs/TASK_SCHEMA.md`
5. `DESIGN.md`
6. `docs/UX_NOTES.md`
7. `docs/GARDEN_SYSTEM.md`
8. `docs/RECAPS.md`
9. `docs/DESIGN_TOOLS_AND_REFERENCES.md`
10. `docs/TOKEN_STRATEGY.md`

If the requested work is UI-only, prioritize:
- `DESIGN.md`
- `docs/UX_NOTES.md`
- `docs/GARDEN_SYSTEM.md`
- `docs/RECAPS.md`

---

## Product feeling

Task Garden should feel like:

- a refined personal productivity tool
- a calm planning desk
- a restorative command center
- a system where progress accumulates visibly
- a premium app with a subtle game layer

It should **not** feel like:

- a generic SaaS admin dashboard
- a childish gamified checklist
- a noisy AI chat interface
- an over-decorated landing page
- a harsh productivity guilt machine

---

## Core UX priorities

In order:

1. capture speed
2. review clarity
3. task list usability
4. trust and editability
5. recap readability
6. garden delight

If there is tension between beauty and usability, choose usability.
If there is tension between novelty and clarity, choose clarity.
If there is tension between atmosphere and speed, choose speed.

---

## Product rules to respect

- The app must feel good in **local-only mode**.
- AI-extracted tasks must **never** bypass review.
- Raw input must always be preserved.
- The garden must **not decay** when there are zero active tasks.
- The garden may decay only from overdue incomplete active tasks.
- The game layer must remain optional and not block task management.
- Recaps are first-class product features, not an afterthought.
- Cloud provider support may exist, but the UI must not assume cloud is active.

---

## Visual direction

### High-level direction
Use a dark-first, premium interface with restrained gradients, layered cards, strong typography, and calm visual depth.

### Aesthetic blend
Combine:
- modern productivity dashboard structure
- premium dark-mode surfaces
- selective gradient accents
- elegant card hierarchy
- pixel-art isometric garden visuals in the garden view only

### Core visual idea
“Gradient productivity shell around a desert-to-oasis management-game core.”

---

## Color guidance

### Shell
- dark graphite / charcoal base
- soft layered surfaces
- near-white primary text
- muted secondary text
- subtle borders
- premium but restrained accent gradients

### Accent usage
Use gradients selectively for:
- primary CTAs
- selected states
- important hero cards
- recap highlights
- special status emphasis

Do not cover the whole UI in gradients.

### Nature and game accents
Use earthy tones for garden-related moments:
- sand
- moss
- sage
- olive
- lavender
- fountain blue
- terracotta
- stone neutrals

### Warning / decay
Use warm dusty tones, not aggressive alarm colors:
- amber
- ochre
- muted orange
- soft rust

---

## Typography

Use a clean, modern sans serif.

Typography should communicate:
- clarity
- confidence
- polish

Avoid:
- overly playful rounded fonts
- sci-fi or futuristic fonts
- excessively stylized display type

Use:
- strong page headers
- compact metadata
- crisp list typography
- confident numeric styles in recap cards

---

## Layout principles

- preserve whitespace
- keep screens scannable
- use modular panels
- avoid overly deep nesting
- maintain a strong hierarchy
- optimize the first screen for action, not decoration

### Desktop structure
Preferred desktop layout:
- left sidebar navigation
- main content area
- optional right-side contextual panel/drawer where useful
- top utility bar only if needed

### Mobile future
Do not hardcode desktop assumptions so deeply that mobile adaptation becomes painful later.

---

## Screen-specific guidance

### 1. Capture
This is the most important screen.

Goals:
- premium
- inviting
- fast
- readable
- safe
- obvious next step

Must support:
- typed entry
- pasted entry
- microphone capture
- transcript/raw note visibility
- extraction preview
- review-before-save flow

Do not make it feel like a chat interface.
Do not hide the raw input.
Do not imply tasks are saved before confirmation.

### 2. Review
This is the trust screen.

Goals:
- easy scanning
- easy editing
- easy rejection
- explicit user control

Each task candidate should make these fields easy to inspect:
- title
- project/group
- priority
- effort
- energy
- due date
- source excerpt

Confidence can be shown only if it improves decisions.
Do not make confidence visually dominant.

### 3. Task views
Task views should feel efficient and composed.

Primary views:
- Inbox
- Today
- This Week
- Projects
- Completed

Design goals:
- fast scanability
- minimal clutter
- visible priority and due timing
- easy state changes
- compact task density

Avoid oversized cards for every task.
Prefer clean list rows with optional expansion.

### 4. Garden
The garden should feel special, but not detached from the rest of the app.

Goals:
- reward
- reflection
- restoration
- visible progress
- repairability

The surrounding UI chrome should remain modern and premium.
Do not turn the entire product into a game UI.

### 5. Recaps
Recaps should feel polished and memorable.

Goals:
- visual storytelling
- accomplishment framing
- emotional clarity
- grounded metrics
- browsable cards

Use:
- strong opening card
- metric cards
- project highlight cards
- streak/comeback cards
- garden transformation cards

The yearly recap should feel like a real product moment.

---

## Interaction principles

### Capture first
The fastest flow in the app should always be:
1. capture
2. review
3. confirm
4. manage

### Review is sacred
Model-generated content must feel like a suggestion the user is approving, not an automated system acting on their behalf.

### Efficient lists
Use:
- inline actions
- drawers for detail
- compact chips
- predictable status patterns
- keyboard support

### Game is peripheral
The garden should enrich the emotional loop, not interrupt execution.

---

## Component guidance

### Baseline stack
Prefer:
- Tailwind CSS
- shadcn/ui
- Radix Primitives
- Lucide icons
- Motion for restrained animation

### Buttons
- primary buttons may use gradient fills
- secondary buttons should remain quieter
- destructive actions should be clear but not loud
- icon buttons should be compact and accessible

### Cards
Use cards for:
- review candidates
- recap highlights
- recommendation blocks
- key summary surfaces

Do not make every surface the same card.

### Chips / badges
Use for:
- priority
- effort
- energy
- labels
- status

They should be readable and low-noise.

### Drawers / dialogs
Prefer drawers for review and contextual editing.
Use dialogs for confirmations and short focused flows.

---

## Motion guidance

Use motion sparingly and purposefully.

Good uses:
- panel entrance
- hover state
- confirmation feedback
- garden restoration cues
- recap card progression
- subtle transitions

Avoid:
- constant floating
- excessive parallax
- long animation delays
- decorative motion that slows the workflow

Motion should feel:
- fast
- quiet
- smooth
- intentional

---

## Accessibility requirements

Non-negotiable:
- visible focus states
- keyboard-friendly flows
- semantic structure
- readable contrast
- reduced-motion compatibility
- garden visuals must not be the only way to understand important state

---

## Design reference strategy

Use references intentionally, not literally.

### Real product flows
Use for:
- settings
- navigation
- filters
- list/detail patterns
- onboarding
- empty states

### High-polish visual references
Use for:
- surface styling
- composition
- premium dark mode
- hero card hierarchy
- recap polish

### Component harvesting
Use for:
- production-adaptable blocks
- accessible primitives
- polished sections

### Agent-readable style references
Use for:
- persistent constraints
- reusable design direction
- keeping generated UI coherent

The repo’s own design docs remain the source of truth.

---

## Implementation instructions for AI coding agents

When generating UI:

- do not default to a generic admin dashboard
- do not overuse gradients
- do not over-animate
- do not make the interface noisy
- do not make task rows too tall
- do not make the garden look like a separate product
- do not bury capture behind extra steps
- do not make recap pages look like raw analytics dashboards

Do:

- prioritize hierarchy and readability
- keep core flows compact
- make the capture screen feel premium
- make review feel safe and obvious
- make recaps feel special
- keep the garden visually distinct but integrated
- use placeholder art gracefully until final assets exist

---

## Recommended supporting tools

Add or plan for:
- Storybook
- Playwright
- MSW

Use Storybook for:
- review states
- empty states
- recommendation cards
- recap cards
- garden state snapshots

Use Playwright for:
- capture flow
- review/confirm flow
- task completion flow
- recap access

Use MSW for:
- mocked extraction states
- mocked provider states
- design iteration without backend friction

---

## Token discipline for UI work

For UI prompts:
- point to `DESIGN.md` and `docs/UX_NOTES.md`
- name the exact screen or subsystem
- ask for changed files only
- keep response verbosity low

Do not restate the whole design system in each prompt.

---

## Final rule

When uncertain, optimize for:
- fast capture
- low cognitive load
- calm polish
- trustworthy review
- visible progress
- long-term coherence