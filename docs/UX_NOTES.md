# UX Notes

## Purpose

This document captures interface direction, UX priorities, reference categories, and practical rules for building Task Garden’s interface.

It is meant to help:
- coding agents
- designers
- future contributors
- anyone sourcing UI inspiration

The goal is not just to make the app pretty.
The goal is to make it:
- easy to capture
- easy to review
- easy to trust
- easy to return to
- motivating over time

---

## Core UX thesis

Task Garden succeeds if the user feels:

1. “I can dump my thoughts here quickly.”
2. “The app organizes them without taking control away from me.”
3. “I can see what matters this week.”
4. “I can look back and feel momentum.”
5. “The garden makes follow-through visible.”

The main UX value is not the task database.
It is the feeling of turning chaos into progress.

---

## UX priorities in order

1. capture speed
2. review clarity
3. task list usability
4. trust and editability
5. recap readability
6. garden delight

If a feature is beautiful but slows capture or review, it should lose.

---

## Main user journeys

### Journey 1 — quick capture
The user has a burst of thoughts and wants to get them out fast.

Success criteria:
- capture starts immediately
- text is easy to paste or dictate
- no complex setup
- no forced categorization before input
- extracted tasks are grouped clearly

### Journey 2 — review and organize
The user needs to validate what the AI understood.

Success criteria:
- candidate tasks are easy to scan
- edits are lightweight
- the user can reject bad candidates fast
- the user can trust that nothing is committed without confirmation

### Journey 3 — daily execution
The user wants to know what to do now.

Success criteria:
- Today and This Week are obvious and scannable
- task weight is visible
- small wins are easy to identify
- stale tasks are surfaced without shame

### Journey 4 — reflection
The user wants to look back and feel progress.

Success criteria:
- accomplishments are summarized elegantly
- cards feel meaningful, not generic
- garden change is visible
- the tone is motivating and grounded

---

## Information architecture

### Primary navigation
- Capture
- Inbox
- Today
- This Week
- Projects
- Completed
- Garden
- Recaps
- Settings

### Suggested initial landing page
Capture should be the default home screen or the most prominent first destination.

Reason:
this product is differentiated most by low-friction capture, not by traditional task tables.

---

## Capture UX notes

### Capture screen goals
- welcoming
- fast
- safe
- structured
- premium-feeling

### Recommended layout
Desktop:
- large capture panel
- visible mic / dictation CTA
- transcript/raw note pane
- extraction preview pane
- clear confirm step

### Design notes
- do not make capture look like a chat app
- do not hide the raw entry
- make microphone state highly legible
- show extraction as “suggested structure,” not “the final answer”

### Recommended microcopy tone
- direct
- calm
- useful
- not overenthusiastic

Examples:
- “Speak naturally. We’ll turn it into task candidates.”
- “Review before saving.”
- “Nothing is saved until you confirm.”

---

## Review UX notes

This is one of the most important screens in the product.

### Review screen must communicate:
- the app extracted likely tasks
- the user remains in control
- edits are expected and normal
- rejection is easy
- the structure is useful, not magical for its own sake

### Candidate card content
Each candidate should surface:
- title
- project/group
- priority
- effort
- energy
- due date
- source excerpt
- confidence only if it helps, not if it adds noise

### Interaction rules
- accept/reject should be one click
- editing should be inline or one lightweight expansion away
- bulk confirm can exist, but not at the expense of clarity

---

## Task list UX notes

### List goals
- high scanability
- low friction
- easy triage
- useful grouping

### Show prominently
- title
- status
- priority
- due timing
- project
- effort

### Show secondarily
- labels
- energy
- timestamps
- excerpt/source links

### Avoid
- oversized cards for every task
- excessive columns
- too many competing visual states
- loud colors on every row

### Helpful views
- Inbox for unsorted/new items
- Today for immediate execution
- This Week for planning
- Projects for grouped context
- Completed for satisfaction and history

---

## Recommendation UX notes

Recommendations should feel like:
- coaching
- triage help
- reflective nudges

They should not feel like:
- commands
- guilt
- overbearing AI advice

### Best recommendation types
- stale task surfaced gently
- oversized task suggests breakdown
- overloaded week warning
- neglected project reminder
- small-win suggestion

### Display guidance
- compact cards
- low-noise styling
- visible rationale
- easy dismissal

---

## Garden UX notes

The garden is a reward and reflection layer.

### It should communicate:
- restoration
- momentum
- care
- visible discipline
- recoverability

### It should not communicate:
- punishment
- failure spirals
- arbitrary randomness

### Important emotional rule
Disrepair should feel repairable, not catastrophic.

### Recommended garden interactions
- hover/tap tile or zone for detail
- click unlocked decoration to inspect
- subtle animation on restoration
- recap tie-ins for “what changed”

### Relationship to core app
The garden should be a destination, not the main workflow.
The app must remain strong even if the user rarely opens the garden.

---

## Recap UX notes

The recap experience should feel special.

### Weekly recap
- compact
- motivating
- practical
- card-based

### Monthly recap
- more trend-oriented
- stronger visual progression
- a bit more reflective

### Yearly recap
- the most polished and story-like view in the product
- should feel close to a “year in review” product moment
- should include a strong opening card

### Strong opening line direction
- “Look at all you accomplished”
- “Here’s what you kept building”
- “From desert to oasis”
- “This is what your year looked like in motion”

### UI patterns for recaps
- hero header
- metric cards
- project summary cards
- streak / comeback cards
- garden transformation card
- timeline or milestone strip

---

## Interface references to use

These references serve different purposes.
Do not copy them blindly. Use them intentionally.

### 1. Real app flow references
Use when you need:
- task flows
- onboarding patterns
- account settings layouts
- list and detail patterns
- real-world product structure

Suggested source:
- Mobbin

### 2. Web visual inspiration
Use when you need:
- visual polish
- composition ideas
- hero treatments
- color systems
- premium-feeling surfaces

Suggested sources:
- Land-book
- Godly

### 3. Agent-oriented design skill references
Use when you need:
- persistent style constraints
- reusable UI design rules for coding agents
- design consistency across prompts

Suggested source:
- TypeUI skill files / design files

### 4. Component harvesting
Use when you need:
- production-adaptable components
- polished blocks
- interaction patterns
- inspiration you can immediately adapt

Suggested sources:
- shadcn/ui
- Magic UI
- 21st.dev

---

## How to use references well

### Good pattern
- find 2–3 references per screen
- extract layout, hierarchy, and interaction ideas
- combine them with the Task Garden design brief
- keep the product internally consistent

### Bad pattern
- copying one reference wholesale
- mixing too many aesthetic systems
- making capture look like one app and recaps like a totally different product

---

## Screen-by-screen reference suggestions

### Capture
Use:
- premium dashboard landing layout references
- focused input/capture references
- lightweight chat-adjacent composition without copying chat UI

### Inbox / Today / This Week
Use:
- productivity app list patterns
- clean dashboard tables/lists
- compact row hierarchy

### Garden
Use:
- management game UI principles
- cozy strategy overlays
- isometric game references
- restrained HUD-style panels

### Recaps
Use:
- year-in-review card systems
- premium analytics highlights
- swipeable or progressive card storytelling
- music/product recap inspiration patterns

---

## Recommended implementation tools

### Core UI system
- Tailwind CSS
- shadcn/ui
- Radix Primitives
- Lucide
- Motion

### Useful workflow tools
- Storybook
- Playwright
- MSW

### Design-skill workflow
- root `DESIGN.md`
- optional TypeUI-generated or TypeUI-inspired skill file
- repo docs for persistent context

---

## UX anti-patterns to avoid

- generic SaaS dashboard clone
- too much glassmorphism everywhere
- task rows that are too tall
- garden visuals bleeding into every screen
- recap pages that look like database reports
- AI confidence indicators everywhere
- too many color-coded status systems
- too much decorative motion
- requiring too many clicks to save reviewed tasks

---

## Accessibility reminders

- visible focus states
- keyboard-first flows for heavy users
- contrast must hold up in dark mode
- garden visuals cannot carry critical information alone
- recap cards should remain readable without relying on color

---

## Final UX rule

When uncertain, optimize for:
- fast capture
- low cognitive load
- visible progress
- emotional clarity
- long-term consistency