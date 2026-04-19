# Build Spec

## Product name

**Task Garden**

## Product summary

Task Garden is a local-first productivity app that converts spoken or typed brain-dumps into structured tasks and visualizes progress through a calm isometric pixel-art garden. The user starts with a neglected desert plot. As tasks are completed, the garden is restored, planted, decorated, and expanded. If the user creates tasks and leaves them overdue, parts of the garden fall into disrepair. If the user has no active tasks, there is no decay.

The app is desktop-first initially, but it should be built so it can later be packaged for desktop and adapted for mobile.

## Core promise

The app should help the user:

- capture tasks quickly from plain dictation or text
- organize those tasks into a workable plan
- track accomplishments over time
- stay motivated through a gentle management-game style layer
- reflect on progress through weekly, monthly, and yearly recaps

## Primary goals

1. **Frictionless capture**
   - The user should be able to speak naturally.
   - The app should preserve the raw input.
   - The app should turn that input into structured task candidates.

2. **Trustworthy organization**
   - Extracted tasks must be reviewed before being saved.
   - The app must support projects, labels, priority, effort, energy, due dates, and subtasks.
   - The app should support search, filtering, and task history.

3. **Actionable planning**
   - The app should provide deterministic recommendations first.
   - AI-based planning notes may be layered on later, but must remain advisory.

4. **Motivating progress**
   - Completed tasks should visibly improve the garden.
   - Overdue incomplete tasks should create repairable disrepair.
   - The garden must feel restorative, not punitive.

5. **Meaningful reflection**
   - The app should generate weekly, monthly, and yearly recaps.
   - Recaps should highlight accomplishments, momentum, and patterns.

## Non-goals for v1

- multi-user collaboration
- team workspaces
- social feeds or sharing features
- full app-store mobile release
- complex real-time multiplayer systems
- autonomous task actions without user confirmation
- requiring cloud AI or remote servers to use the app

## Target user

Initial target user is a **single user** running the app across one or more personal devices.

## Platform strategy

### Initial
- local web app
- desktop-first UX
- local database
- local AI supported

### Future
- Tauri packaging for desktop
- hosted single-user sync
- iOS and Android clients
- optional cloud AI fallback

## AI strategy

The system must support both local and cloud AI providers through interchangeable provider interfaces.

### Local-first providers
- speech-to-text via local engine
- task extraction via local model
- planning via local model

### Optional cloud fallback
- speech-to-text via cloud provider
- task extraction via cloud provider
- recap narrative generation via cloud provider

Cloud providers must be implemented in a way that they can remain disabled by default.

## Core user flows

### 1. Text capture flow
1. User types or pastes a raw entry.
2. Raw entry is saved.
3. Task extraction is run.
4. Extracted task candidates are shown in review.
5. User edits or deletes candidates.
6. User confirms.
7. Tasks are saved.

### 2. Voice capture flow
1. User records audio.
2. Audio is transcribed.
3. Transcript is saved as a raw entry.
4. Extraction is run on transcript text.
5. Review and confirm flow is identical to text flow.

### 3. Task management flow
1. User reviews Inbox, Today, This Week, Projects, Completed.
2. User updates status, edits tasks, adds subtasks, reopens tasks.
3. Activity is logged.
4. Garden state and recap metrics are updated through domain services.

### 4. Recap flow
1. System computes deterministic metrics for a period.
2. Metrics are snapshotted.
3. Optional narrative layer is generated from compact summary metrics.
4. User views recap cards and summary pages.

## Functional requirements

### Capture
- support typed capture
- support pasted notes
- support recorded audio
- preserve raw input
- preserve transcript
- preserve extraction batches

### Task extraction
- generate structured candidates
- include confidence and source excerpt
- allow user edits before save
- reject invalid candidates from direct persistence

### Task management
- inbox
- today view
- week view
- projects view
- completed view
- search
- filters
- subtasks
- labels
- project grouping
- timestamps
- activity history

### Planning
- stale task detection
- overloaded week detection
- neglected project detection
- small wins suggestions
- large-task breakdown suggestions
- optional weekly coaching note

### Garden
- desert starting state
- restoration through task completion
- disrepair through overdue active tasks
- no decay with zero active tasks
- unlockable decorations
- unlockable rare plants
- visible recovery loop
- optional game layer

### Recaps
- weekly recap
- monthly recap
- yearly recap
- deterministic metrics
- optional narrative
- cards/highlights
- “Look at all you accomplished” framing

### Settings
- provider selection
- local-only mode toggle
- sync toggle
- model names
- model URLs
- cloud key fields
- garden settings
- recap settings
- export/import

## Quality requirements

- responsive enough for desktop use
- stable in local-only mode
- deterministic validation around AI outputs
- replaceable assets
- test coverage around rules and invariants
- provider switching without business logic rewrites

## Important product invariants

- Raw user input must always be preserved.
- AI-extracted tasks must never bypass user review.
- The garden must not decay if there are no active tasks.
- Deterministic metrics should be the basis of recaps.
- The app must remain usable without cloud access.

## Phasing

### Phase 0
Scaffold repo, shared types, provider interfaces, docs, and migrations.

### Phase 1
Implement text capture, extraction, review flow, task persistence, and task views.

### Phase 2
Implement audio recording and transcription.

### Phase 3
Implement optional cloud fallback providers.

### Phase 4
Implement sync-ready data structures and endpoints.

### Phase 5
Implement garden domain and garden UI.

### Phase 6
Implement deterministic recommendations and recap engine.

### Phase 7
Polish, tests, and packaging preparation.

## Success criteria for first usable version

The first usable version is successful if the user can:

- enter text or speak
- get structured task candidates
- review and save those tasks
- manage them across basic views
- complete tasks
- see the garden improve
- see a weekly recap of completed work