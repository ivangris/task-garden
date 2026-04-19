
## `docs/DESIGN_TOOLS_AND_REFERENCES.md`

```md
# Design Tools and References

## Purpose

This document lists the tools, libraries, reference sites, and workflow helpers recommended for Task Garden’s interface design and front-end implementation.

It also includes suggestions for keeping design work consistent and keeping agent usage efficient.

---

## Recommended baseline stack

### Core UI foundation
Use these as the default front-end design system stack:

- Tailwind CSS
- shadcn/ui
- Radix Primitives
- Lucide
- Motion

This stack gives:
- speed
- composability
- accessible primitives
- strong dark-mode support
- clean component ergonomics
- enough polish without locking the product into a rigid theme

---

## Why this stack

### Tailwind CSS
Use for:
- rapid layout iteration
- spacing consistency
- token-like utility usage
- fast refinement by coding agents

### shadcn/ui
Use for:
- production-friendly component scaffolding
- consistent component baseline
- editable source-controlled components rather than opaque package widgets

### Radix Primitives
Use for:
- accessible low-level behavior
- dialogs
- popovers
- menus
- tabs
- switches
- composable stateful UI

### Lucide
Use for:
- consistent icon language
- tree-shakeable icon imports
- clean interface semantics

### Motion
Use for:
- subtle interaction animation
- layout transitions
- recap progression
- garden feedback
- calm polish

---

## Recommended workflow tools

### Storybook
Use for:
- building components in isolation
- hard-to-reach UI states
- documenting the system as it grows
- design review without needing the whole app running

### Playwright
Use for:
- end-to-end flow testing
- review flow verification
- keyboard navigation checks
- regression checks on high-value paths

### MSW
Use for:
- mocking API states during front-end development
- previewing extraction/review states without live backends
- making Storybook states more realistic
- reducing friction during UI iteration

---

## Recommended design-skill workflow

### Root design file
Keep a repo-level `DESIGN.md`.

This file should be the persistent design brief for coding agents.

### UX and product docs
Keep these in sync:
- `DESIGN.md`
- `docs/UX_NOTES.md`
- `docs/GARDEN_SYSTEM.md`
- `docs/RECAPS.md`

### Optional skill-file workflow
If desired, add a design skill file generated from or inspired by TypeUI-style workflows.

Suggested options:
- a manually maintained `DESIGN.md`
- a pulled skill file adapted to the repo
- a project-specific skill file derived from your preferred gradient/dashboard aesthetic

---

## TypeUI usage suggestion

If you want agent-consistent UI generation, use TypeUI as inspiration or directly as a skill-file source.

Recommended approach:
1. browse the design-skill registry
2. choose a style close to your preferred visual language
3. adapt it into this project’s own `DESIGN.md`
4. keep the repo-level design file as the canonical source of truth

For this app, the best fit is likely:
- dashboard-like structure
- gradient-accent polish
- restrained premium dark mode

Do not let an external design skill override the product-specific rules of Task Garden.

---

## Best reference sites by purpose

### Real product flows
Use when you need:
- settings patterns
- task list patterns
- onboarding ideas
- filter panels
- search states
- empty states

Recommended:
- Mobbin

### High-polish web inspiration
Use when you need:
- layout composition
- hero card styling
- visual hierarchy ideas
- premium dark-mode references
- color system ideas

Recommended:
- Land-book
- Godly

### Component harvesting and patterns
Use when you need:
- buildable components
- immediately adaptable sections
- polished snippets
- interaction ideas

Recommended:
- shadcn/ui
- Magic UI
- 21st.dev
- Tailwind Plus if you are willing to pay for premium blocks

---

## What to reference for each part of the app

### Capture page
Reference:
- focused dashboard hero sections
- premium input surfaces
- voice/capture interactions
- compact review side panels

### Task views
Reference:
- productivity dashboards
- real app list/table hybrids
- clean filter bars
- detail drawers

### Garden page
Reference:
- management game overlays
- cozy strategy UI
- tile-map side panels
- minimal HUD patterns

### Recaps
Reference:
- annual wrapped-style experiences
- analytics highlight cards
- progress storytelling
- premium summary layouts

---

## Suggested additional libraries

These are optional but helpful.

### Good additions
- `clsx`
- `tailwind-merge`
- `class-variance-authority`
- charting library later for recap visuals if needed

### Consider later, not day 1
- advanced chart packages
- 3D libraries
- game engines
- heavy canvas abstractions

The garden should begin as a lightweight rendered view, not a full engine project.

---

## Storybook guidance

Use Storybook stories for:
- empty task states
- crowded task states
- extraction review with 1 candidate
- extraction review with many candidates
- garden state snapshots
- recap cards
- settings screens

This reduces iteration cost and helps prevent UI drift.

---

## Design consistency workflow

### Recommended process
1. update `DESIGN.md`
2. update `docs/UX_NOTES.md` if a pattern changes
3. build or revise components
4. add Storybook stories
5. test high-value flows
6. only then move on

### Avoid
- changing visual direction ad hoc in chat prompts
- mixing unrelated reference aesthetics
- letting one generated screen redefine the whole product

---

## Token-saving workflow for UI work

### Best practice
Do not describe the full design system in every agent prompt.

Instead:
- keep `DESIGN.md` stable
- point the agent to `DESIGN.md` and `docs/UX_NOTES.md`
- ask for one screen or subsystem at a time

### Example
Good:
- “Read DESIGN.md and docs/UX_NOTES.md. Implement the Capture page shell and extraction review drawer.”

Bad:
- “Build a beautiful premium app with gradients, cards, and some game feel.”

### Other savings
- use Storybook to isolate UI work
- use MSW to fake backend states
- keep a small set of approved screen references
- store prompt templates in repo files

---

## Plugin / tool adoption priority

### Add early
- Tailwind CSS
- shadcn/ui
- Radix
- Lucide
- Motion
- Storybook
- Playwright
- MSW

### Add after the repo grows
- Graph / code knowledge tools
- heavier design-skill tooling
- premium component subscriptions
- export/share tooling

---

## Recommended design reference workflow for this project

### Primary references
- Mobbin for product patterns
- Land-book / Godly for surface polish
- TypeUI for agent-readable design constraints
- shadcn/ui + Magic UI + 21st.dev for implementation shortcuts

### Final rule
Reference broadly.
Implement narrowly.
Keep Task Garden visually coherent.