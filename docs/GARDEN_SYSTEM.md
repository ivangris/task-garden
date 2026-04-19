# Garden System

## Overview

The garden is a first-class domain system, not a cosmetic add-on.

It serves as a visual representation of the user’s follow-through over time.

The garden starts as a **neglected desert plot** and becomes restored, planted, decorated, and alive as the user completes tasks. If the user creates tasks and lets them become overdue, parts of the garden fall into disrepair.

Important rule:

> If there are zero active tasks, the garden must not decay.

## Fantasy and tone

The garden should feel:

- calm
- restorative
- satisfying
- lightly game-like
- visually rewarding
- never cruel or punishing

This is not a stress mechanic. It is a momentum mechanic.

## Visual direction

- isometric pixel art
- tile-based layout
- desert-to-oasis transformation
- paths, hedges, flowers, fountain, planters, arches, statues, rare plants
- visible restoration and visible disrepair
- collectible decorative elements

## Starting state

The user begins with:
- dry sand or cracked soil
- sparse scrub or dead plants
- broken or empty fountain
- damaged path edges
- minimal greenery
- low-level atmosphere of neglect, not devastation

## Core systems

### 1. XP
Task completion grants XP.

### 2. Unlocks
XP and milestone conditions unlock:
- seeds
- water uses
- fertilizer
- basic plants
- decorative objects
- rare plants
- upgraded fountain states
- biome variants later

### 3. Tile restoration
Garden tiles transition through states:
- `desert`
- `recovering`
- `healthy`
- `lush`

### 4. Decay
Overdue active tasks generate decay pressure.

### 5. Recovery
Completing tasks reverses decay and restores affected areas.

## Core rule: decay trigger

Decay should be computed only from **active overdue tasks**.

No decay should happen when:
- the user has no tasks
- the user has no overdue tasks
- the user is inactive but has no outstanding commitments

## Suggested formulas

## XP by effort

- small: `10`
- medium: `25`
- large: `60`

## Priority bonus

- low: `0`
- medium: `2`
- high: `5`
- critical: `8`

## Streak multiplier

- base: `1.0`
- 3-day streak: `1.1`
- 7-day streak: `1.2`
- 21-day streak: `1.35`

## XP formula

```text
task_xp = (effort_xp + priority_bonus) * streak_multiplier

## Daily decay formula
if active_overdue_tasks == 0:
    decay_points = 0
else:
    decay_points = sum(task_decay_weight)

    Recovery should feel faster than decay