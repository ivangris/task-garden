
---

## `docs/RECAPS.md`

```md
# Recaps

## Overview

Task Garden includes three recap layers:

- weekly recap
- monthly recap
- yearly recap

The purpose of recaps is to help the user see progress, patterns, and momentum over time.

The tone should be:
- encouraging
- concrete
- reflective
- visually satisfying
- grounded in real activity data

## Core principle

Recaps must be built from **deterministic metrics first**.

Optional AI-generated narrative should be based on compact structured summaries, not on unbounded raw history.

## Why recaps matter

Recaps turn task history into:
- motivation
- memory
- identity reinforcement
- long-term perspective

They help the user say:
- “Look at all I accomplished”
- “This is what I kept showing up for”
- “This is how I recovered”
- “This is how my garden changed”

## Recap periods

### Weekly
A short, motivating snapshot.

### Monthly
A trend-oriented reflection with more category breakdown.

### Yearly
A more story-like summary with milestone and transformation framing.

## Recap data pipeline

1. collect relevant period range
2. compute deterministic metrics
3. store recap metric snapshot
4. derive highlights and milestone cards
5. optionally generate narrative text from structured summary
6. cache result for later viewing

## Deterministic metrics

### Common metrics across periods
- total tasks completed
- completion rate
- active days
- reopened tasks count
- overdue recovered count
- top projects
- label distribution
- completion by effort
- completion by priority
- streak data
- garden XP gained
- unlocks earned
- net garden health change

## Weekly recap

### Goal
Show immediate momentum.

### Weekly metrics
- tasks completed
- active days this week
- completion rate this week
- biggest completed task
- smallest wins count
- most active project
- overdue tasks recovered
- garden tiles restored
- XP gained
- streak status

### Weekly card ideas
- “You completed X tasks”
- “You showed up on Y days”
- “Your top focus was PROJECT”
- “Biggest lift: TASK”
- “You restored Z tiles”
- “Your streak is now N days”

### Weekly tone
- concise
- practical
- motivating
- not overly sentimental

## Monthly recap

### Goal
Show themes and trends.

### Monthly metrics
- total completed
- weekly completion trend
- top 3 projects
- longest streak
- most productive weekday
- most delayed category
- average effort distribution
- garden health change
- unlocks earned
- restored vs decayed zones
- recovery moments

### Monthly card ideas
- “This month in momentum”
- “Your dominant project”
- “You kept showing up on…”
- “What bloomed”
- “What got stuck”
- “Biggest recovery”

### Monthly tone
- reflective
- grounded
- a little more narrative

## Yearly recap

### Goal
Create a memorable “year in progress” story.

### Yearly metrics
- total completed tasks
- total active days
- highest streak
- top project themes
- estimated effort completed
- biggest wins
- most consistent month
- toughest month recovered
- overdue recoveries
- total XP earned
- total unlocks earned
- garden start vs end state
- net lushness / health change
- signature achievements
- recurring goal themes

### Yearly card ideas
- opening card: “Look at all you accomplished”
- “Your year in tasks”
- “What you kept building”
- “Your biggest comeback”
- “The month you found momentum”
- “From desert to oasis”
- “Your signature win”
- “What the year says about your priorities”

### Yearly tone
- celebratory
- story-like
- warm
- still grounded in real metrics

## Milestone logic

Milestones can be detected from activity data.

Examples:
- first 100 completed tasks
- first rare garden unlock
- longest streak reached
- most completed tasks in a week
- project completed after long delay
- recovery after large decay period

## Narrative generation

Narrative generation should be optional.

If used:
- generate from compact structured summaries
- keep narratives short
- never invent metrics
- always prefer concrete phrasing over vague praise

### Suggested narrative inputs
- period type
- period date range
- total completed
- top projects
- biggest wins
- streak stats
- garden transformation summary
- 5–10 representative completed task titles
- notable recovery events

## Caching and reproducibility

Each recap should have:
- a deterministic metric snapshot
- a versioned narrative if generated
- a prompt version if AI was used
- a model/provider identifier if AI was used

This allows:
- reproducible recap history
- later regeneration with new prompt versions
- controlled token usage

## Domain entities

### RecapPeriod
Represents the time window.

### RecapMetricSnapshot
Stores deterministic numbers and aggregates.

### RecapStory
Stores optional generated text and metadata.

### HighlightCard
Stores card-level recap elements for UI rendering.

### Milestone
Stores meaningful achievements.

### StreakSummary
Stores period streak information.

### ProjectSummary
Stores per-project recap statistics.

## Suggested highlight card schema

Each card may contain:
- `id`
- `period_id`
- `card_type`
- `title`
- `subtitle`
- `primary_value`
- `secondary_value` optional
- `supporting_text` optional
- `visual_hint` optional
- `sort_order`

## UI guidance

The recap UI should feel:
- polished
- clean
- card-based
- satisfying to browse

Avoid:
- overloading the user with tables
- too much text on one screen
- burying the main accomplishments

## Export potential

Future recap export targets may include:
- image cards
- printable recap pages
- shareable story format
- end-of-year slideshow

These are not required for v1, but the data model should support them later.

## Invariants

- recap metrics must be deterministic
- generated narratives must not replace factual metrics
- recap generation must work even if no AI provider is enabled
- zero-completion periods should still produce a graceful recap state
- garden transformation should be included wherever meaningful