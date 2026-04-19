# DESIGN.md

## Mission

Design Task Garden as a calm, premium, desktop-first productivity app with an optional game layer.

The interface should feel:
- elegant
- intentional
- modern
- visually rewarding
- low-friction
- slightly magical, but not flashy

This is not a toy app and not a corporate enterprise dashboard.
It should sit somewhere between:
- a refined personal productivity tool
- a strategy/management game overlay
- a reflective progress journal

The main job of the UI is to make raw capture feel effortless and structured follow-through feel satisfying.

---

## Product personality

Task Garden should feel like:

- a smart planning desk
- a restorative personal command center
- a place where progress accumulates visibly
- a system that respects the user’s attention

It should not feel like:
- a generic SaaS admin panel
- a childish gamified checklist
- an overly sterile to-do app
- a cluttered AI dashboard

---

## Visual direction

### Primary style
Use a dark-first interface with luminous gradient accents, soft depth, refined contrast, and clean component structure.

### Secondary style
Blend:
- modern productivity dashboard
- soft glass-like layering where useful
- pixel-art isometric garden visuals in the game view
- restrained motion
- rich but controlled color

### Core aesthetic
“Gradient productivity meets desert-to-oasis management game.”

---

## Color system

### Foundation
Use a dark neutral base.

Suggested feel:
- near-black or deep graphite backgrounds
- layered surfaces with slightly different elevations
- bright but disciplined accent gradients
- warm nature colors reserved for garden and recap moments

### Accent logic
Use gradients for:
- primary CTA emphasis
- selected states
- key summary cards
- recap hero moments
- limited decorative UI moments

Do **not** put gradients everywhere.
Most surfaces should remain stable and calm.

### Suggested palette direction
- base background: charcoal / deep graphite
- panel background: slightly lighter charcoal
- text primary: near-white
- text secondary: muted slate
- primary accent gradient: indigo -> violet -> magenta
- secondary accent gradient: teal -> cyan for planning/recommendation states
- success/growth accent: soft emerald / moss / spring green
- warning/decay accent: amber / ochre / dusty orange
- danger accent: muted rose / ember red, not harsh pure red

### Garden palette
Garden colors should be more natural and earthy than the app shell:
- sand
- dry ochre
- olive
- moss
- sage
- lavender
- terracotta
- stone
- fountain blue
- bloom accents

---

## Typography

Use a clean sans serif optimized for UI readability.
Prefer a modern grotesk or neo-grotesk feel.

Typography should communicate:
- clarity first
- confidence second
- delight third

### Hierarchy goals
- large, confident page titles
- compact, highly readable list rows
- strong numeric styles for recap metrics
- elegant small labels and metadata
- restrained uppercase usage

### Tone
Avoid overly playful typography.
Avoid futuristic sci-fi fonts.
Avoid overly soft rounded consumer-app typography.

---

## Layout rules

### General
- prioritize information hierarchy
- preserve whitespace
- keep screens scannable
- avoid overcrowding
- use modular panels and clear grouping

### Capture screen
The capture screen is the heart of the app.
It should be visually inviting and frictionless.

Desired structure:
- large central capture area
- mic button or capture controls prominent
- transcript/raw note area readable and roomy
- extraction preview close by
- review flow obvious and safe

### Task screens
Task screens should favor:
- strong grouping
- compact vertical rhythm
- clear due/priority signals
- easy status editing
- low interaction cost

### Garden screen
The garden screen should feel more immersive than the rest of the product, but still integrated.
It should feel like a reward and reflection space, not a separate game app.

### Recap screens
Recap screens should be card-based, polished, celebratory, and easy to browse.
Think “personal year in review” more than “analytics report”.

---

## Surface design

Use layered cards and panels with subtle depth.

Preferred treatment:
- soft shadows
- low-opacity borders
- occasional glass-like treatment for hero cards
- rounded corners, but not overly bubbly
- clear separation between navigation, content, and utility panels

Avoid:
- heavy skeuomorphism
- high blur everywhere
- noisy background textures on every screen
- excessive nested cards

---

## Motion

Animation should be restrained and purposeful.

Use motion for:
- hover response
- panel entrance
- state changes
- garden restoration feedback
- recap card progression
- tab/view transitions

Avoid:
- constant floating animations
- excessive parallax
- long delays
- decorative motion that slows down task completion

### Motion principles
- fast
- smooth
- quiet
- meaningful

---

## Interaction patterns

### Capture first
The fastest path in the app should always be:
1. capture thought
2. review structure
3. save tasks

### Review is sacred
AI-generated tasks must feel editable, reviewable, and trustworthy.
The UI must make it obvious that the user is approving structured candidates, not accepting hidden automation.

### Lists should be efficient
Task management should feel quick and controlled.
Use:
- inline actions
- keyboard shortcuts
- compact chips
- predictable statuses

### Gamification should be peripheral
The game layer should enrich the emotional experience, not dominate the workflow.

---

## Navigation model

Preferred navigation:
- left sidebar for primary sections on desktop
- persistent top utility bar optional
- clear active state
- low visual clutter

Suggested nav items:
- Capture
- Inbox
- Today
- This Week
- Projects
- Completed
- Garden
- Recaps
- Settings

---

## Component guidance

### Buttons
- primary buttons may use gradient fills
- secondary buttons should be calmer
- destructive buttons should be clear but not loud
- icon buttons should be compact and accessible

### Cards
- use cards for summaries, review candidates, recap highlights, and recommendation blocks
- cards should vary by importance, not all look identical

### Chips and badges
Use chips for:
- priority
- effort
- energy
- labels
- status

They should be easy to scan and low-noise.

### Inputs
Inputs should feel refined and highly legible.
Avoid harsh borders and cramped spacing.

### Dialogs and drawers
Prefer drawers for review/context flows and dialogs for confirmation only.

---

## App-specific screens

### Capture
This should feel premium, focused, and welcoming.
It is acceptable to make this screen slightly more visually rich than others.

### Review
Review should feel safe and clear.
Use candidate cards or editable rows.
Emphasize:
- title
- project
- priority
- effort
- due date
- excerpt

### Task lists
Task lists should feel precise and efficient, closer to a great productivity app than a marketing site.

### Garden
The garden should use isometric pixel-art assets, but surrounding UI chrome should remain modern and elegant.

### Recaps
Recaps should feel like collectible progress snapshots:
- strong headers
- polished number treatments
- milestone cards
- before/after style visual summaries
- garden transformation moments

---

## Accessibility

Non-negotiables:
- clear contrast
- visible focus states
- keyboard support
- semantic structure
- screen-reader-friendly controls and labels
- reduced-motion compatibility where animation exists

Do not sacrifice readability for atmosphere.

---

## Implementation notes for AI agents

When generating UI in this project:
- do not default to a generic dashboard aesthetic
- do not overuse gradients
- do not over-animate
- do not create crowded cards or over-nested containers
- prioritize hierarchy, legibility, and emotional polish
- keep the garden visually distinct from the productivity shell
- make recap views feel special
- keep the default state elegant even before final art exists

When uncertain:
- choose clarity over novelty
- choose polish over ornament
- choose calm over hype