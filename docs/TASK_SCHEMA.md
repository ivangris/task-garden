
---

## `docs/TASK_SCHEMA.md`

```md
# Task Schema

## Overview

This document defines the key entities involved in capture, extraction, task persistence, activity tracking, and planning.

The system distinguishes between:

- raw user input
- extracted task candidates
- validated persisted tasks
- activity events derived from user actions

## Entity: RawEntry

A `RawEntry` is the preserved source material from the user.

### Fields
- `id`
- `source_type`  
  Values: `typed`, `pasted`, `audio_transcript`
- `raw_text`
- `audio_file_ref` optional
- `created_at`
- `updated_at`
- `device_id`
- `entry_status`  
  Values: `new`, `transcribed`, `extracted`, `reviewed`, `archived`

## Entity: TranscriptSegment

Used when a transcription provider returns chunked or timestamped output.

### Fields
- `id`
- `raw_entry_id`
- `segment_index`
- `start_ms` optional
- `end_ms` optional
- `text`
- `speaker_label` optional

## Entity: ExtractionBatch

Represents one extraction pass over a raw entry.

### Fields
- `id`
- `raw_entry_id`
- `provider_name`
- `model_name`
- `schema_version`
- `prompt_version`
- `summary`
- `needs_review`
- `open_questions` JSON array
- `created_at`

## Entity: ExtractedTaskCandidate

Represents a structured candidate returned by extraction before user confirmation.

### Fields
- `id`
- `extraction_batch_id`
- `title`
- `details`
- `project_or_group`
- `priority`
- `effort`
- `energy`
- `labels` JSON array
- `due_date` optional
- `parent_task_title` optional
- `confidence`
- `source_excerpt`
- `candidate_status`  
  Values: `pending_review`, `accepted`, `edited`, `rejected`

## Entity: Task

Represents a persisted user-approved task.

### Fields
- `id`
- `title`
- `details`
- `project_id` optional
- `status`
- `priority`
- `effort`
- `energy`
- `source_raw_entry_id` optional
- `source_extraction_batch_id` optional
- `created_at`
- `updated_at`
- `due_date` optional
- `completed_at` optional
- `parent_task_id` optional
- `device_id`
- `sync_status`
- `is_deleted`

### Task status values
- `inbox`
- `planned`
- `in_progress`
- `blocked`
- `completed`
- `archived`

## Entity: Project

### Fields
- `id`
- `name`
- `description` optional
- `color_token` optional
- `created_at`
- `updated_at`
- `is_archived`

## Entity: TaskLabel

### Fields
- `id`
- `name`
- `created_at`

## Entity: TaskLabelLink

### Fields
- `task_id`
- `label_id`

## Entity: TaskDependency

Optional support for sequencing and blockers.

### Fields
- `id`
- `task_id`
- `depends_on_task_id`
- `dependency_type`  
  Values: `blocks`, `relates_to`, `subtask_of`

## Entity: ActivityEvent

Every meaningful user action should be logged.

### Fields
- `id`
- `event_type`
- `entity_type`
- `entity_id`
- `metadata` JSON
- `created_at`
- `device_id`

### Example event types
- `raw_entry_created`
- `transcription_completed`
- `extraction_completed`
- `task_confirmed`
- `task_edited`
- `task_completed`
- `task_reopened`
- `task_deleted`
- `project_created`
- `garden_recomputed`
- `recap_generated`

## Extraction validation rules

When converting extracted candidates into persisted tasks:

- `title` is required
- `priority` must be one of:
  - `low`
  - `medium`
  - `high`
  - `critical`
- `effort` must be one of:
  - `small`
  - `medium`
  - `large`
- `energy` must be one of:
  - `low`
  - `medium`
  - `high`
- `confidence` must be clamped to `0.0 - 1.0`
- invalid candidates may remain attached to extraction history, but must not be persisted as tasks without correction

## Required review rule

No `ExtractedTaskCandidate` may become a `Task` without user confirmation.

## Search considerations

Search should cover:
- raw entries
- transcript segments
- task title
- task details
- project names
- label names

SQLite FTS5 can support this in local mode.