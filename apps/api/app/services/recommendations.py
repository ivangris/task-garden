from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from app.domain.entities import RecommendationSnapshot, Task
from app.repositories.interfaces import (
    ActivityEventRepository,
    ProjectRepository,
    RecommendationSnapshotRepository,
    TaskRepository,
)
from app.services.common import generate_id, utcnow


ACTIVE_TASK_STATUSES = {"inbox", "planned", "in_progress", "blocked"}
RECOMMENDATION_THRESHOLDS = {
    "stale_days": 7,
    "overload_medium_large_count": 5,
    "overload_points": 8,
    "neglected_completion_gap_days": 14,
    "neglected_oldest_active_days": 7,
    "large_task_stale_days": 5,
    "heavy_backlog_tasks": 12,
    "heavy_backlog_large_tasks": 4,
    "small_wins_limit": 3,
    "focus_item_limit": 3,
}


@dataclass(slots=True)
class RecommendationReason:
    label: str
    value: str


@dataclass(slots=True)
class RecommendationItem:
    id: str
    rule_type: str
    level: str
    title: str
    rationale: str
    reasons: list[RecommendationReason]
    metadata: dict[str, object]
    task_id: str | None = None
    project_id: str | None = None


@dataclass(slots=True)
class WeeklyPreviewResult:
    generated_at: datetime
    window_start: datetime
    window_end: datetime
    top_focus_items: list[Task]
    warnings: list[RecommendationItem]
    suggestion_summaries: list[str]
    thresholds: dict[str, int]


def _start_of_day(value: datetime) -> datetime:
    value = _coerce_datetime(value)
    return value.replace(hour=0, minute=0, second=0, microsecond=0)


def _end_of_day(value: datetime) -> datetime:
    value = _coerce_datetime(value)
    return value.replace(hour=23, minute=59, second=59, microsecond=999999)


def _coerce_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _is_active(task: Task) -> bool:
    return task.status in ACTIVE_TASK_STATUSES and not task.is_deleted


def _days_between(earlier: datetime, later: datetime) -> int:
    normalized_earlier = _coerce_datetime(earlier)
    normalized_later = _coerce_datetime(later)
    assert normalized_earlier is not None and normalized_later is not None
    return max(0, int((normalized_later - normalized_earlier).days))


def _effort_points(effort: str) -> int:
    return {"small": 1, "medium": 2, "large": 3}.get(effort, 1)


def _priority_points(priority: str) -> int:
    return {"low": 0, "medium": 1, "high": 2, "critical": 3}.get(priority, 0)


def _latest_task_touch_map(tasks: list[Task], activity_events: ActivityEventRepository) -> dict[str, datetime]:
    latest = {task.id: _coerce_datetime(task.updated_at) or utcnow() for task in tasks}
    for event in activity_events.list_all():
        event_created_at = _coerce_datetime(event.created_at)
        if event.entity_type == "task" and event.entity_id in latest and event_created_at and event_created_at > latest[event.entity_id]:
            latest[event.entity_id] = event_created_at
    return latest


def _active_tasks(tasks: list[Task]) -> list[Task]:
    return [task for task in tasks if _is_active(task)]


def _due_within_window(task: Task, window_start: datetime, window_end: datetime) -> bool:
    due_date = _coerce_datetime(task.due_date)
    return due_date is not None and _coerce_datetime(window_start) <= due_date <= _coerce_datetime(window_end)


def _serialize_item(item: RecommendationItem) -> dict[str, object]:
    payload = asdict(item)
    payload["reasons"] = [asdict(reason) for reason in item.reasons]
    return payload


def _due_sort_value(task: Task, now: datetime) -> datetime:
    return _coerce_datetime(task.due_date) or datetime.max.replace(tzinfo=_coerce_datetime(now).tzinfo)


def _snapshot_payload(
    *,
    generated_at: datetime,
    items: list[RecommendationItem],
    thresholds: dict[str, int],
    top_focus_items: list[Task] | None = None,
    window_start: datetime | None = None,
    window_end: datetime | None = None,
    suggestion_summaries: list[str] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "generated_at": generated_at.isoformat(),
        "items": [_serialize_item(item) for item in items],
        "thresholds": thresholds,
    }
    if top_focus_items is not None:
        payload["top_focus_item_ids"] = [task.id for task in top_focus_items]
    if suggestion_summaries is not None:
        payload["suggestion_summaries"] = suggestion_summaries
    if window_start is not None:
        payload["window_start"] = window_start.isoformat()
    if window_end is not None:
        payload["window_end"] = window_end.isoformat()
    return payload


def _stale_task_recommendations(active_tasks: list[Task], latest_touch: dict[str, datetime], now: datetime) -> list[RecommendationItem]:
    threshold = RECOMMENDATION_THRESHOLDS["stale_days"]
    stale_candidates = [
        (task, latest_touch.get(task.id, task.updated_at))
        for task in active_tasks
        if _days_between(latest_touch.get(task.id, task.updated_at), now) >= threshold
    ]
    stale_candidates.sort(key=lambda item: (item[1], _due_sort_value(item[0], now), item[0].title.lower()))

    items: list[RecommendationItem] = []
    for task, touched_at in stale_candidates[:3]:
        days = _days_between(touched_at, now)
        items.append(
            RecommendationItem(
                id=f"stale-{task.id}",
                rule_type="stale_task",
                level="warning",
                title=f"Re-check: {task.title}",
                rationale="This task has been active without a recent touch, so it may need a next step or a deliberate defer.",
                task_id=task.id,
                metadata={"days_since_touch": days, "status": task.status},
                reasons=[
                    RecommendationReason(label="Untouched", value=f"{days} days"),
                    RecommendationReason(label="Status", value=task.status.replace("_", " ")),
                ],
            )
        )
    return items


def _overloaded_week_recommendation(active_tasks: list[Task], now: datetime) -> list[RecommendationItem]:
    window_start = _start_of_day(now)
    window_end = _end_of_day(window_start + timedelta(days=6))
    due_this_week = [
        task for task in active_tasks if _due_within_window(task, window_start, window_end) and task.effort in {"medium", "large"}
    ]
    due_this_week.sort(key=lambda task: (_due_sort_value(task, now), -_priority_points(task.priority), task.title.lower()))
    load_points = sum(_effort_points(task.effort) + _priority_points(task.priority) for task in due_this_week)
    if len(due_this_week) < RECOMMENDATION_THRESHOLDS["overload_medium_large_count"] and load_points < RECOMMENDATION_THRESHOLDS["overload_points"]:
        return []

    return [
        RecommendationItem(
            id="overloaded-week",
            rule_type="overloaded_week",
            level="warning",
            title="This week looks heavier than usual.",
            rationale="There are enough medium and large due items this week that the schedule may need triage before it feels manageable.",
            metadata={
                "task_ids": [task.id for task in due_this_week[:5]],
                "medium_large_due_count": len(due_this_week),
                "load_points": load_points,
            },
            reasons=[
                RecommendationReason(label="Medium / large due", value=str(len(due_this_week))),
                RecommendationReason(label="Load points", value=str(load_points)),
            ],
        )
    ]


def _neglected_project_recommendations(tasks: list[Task], project_repo: ProjectRepository, now: datetime) -> list[RecommendationItem]:
    threshold = RECOMMENDATION_THRESHOLDS["neglected_completion_gap_days"]
    active_age_threshold = RECOMMENDATION_THRESHOLDS["neglected_oldest_active_days"]
    projects = {project.id: project for project in project_repo.list_all() if not project.is_archived}
    completions_by_project: dict[str, datetime] = {}
    active_by_project: dict[str, list[Task]] = {}

    for task in tasks:
        if task.project_id is None or task.project_id not in projects:
            continue
        if task.completed_at is not None:
            current = completions_by_project.get(task.project_id)
            if current is None or task.completed_at > current:
                completions_by_project[task.project_id] = task.completed_at
        elif _is_active(task):
            active_by_project.setdefault(task.project_id, []).append(task)

    items: list[RecommendationItem] = []
    for project_id, project_tasks in active_by_project.items():
        project = projects[project_id]
        last_completion = completions_by_project.get(project_id)
        oldest_active = min(project_tasks, key=lambda task: task.created_at)
        oldest_active_days = _days_between(oldest_active.created_at, now)
        days_since_completion = _days_between(last_completion, now) if last_completion else None
        if oldest_active_days < active_age_threshold:
            continue
        if last_completion and days_since_completion < threshold:
            continue
        items.append(
            RecommendationItem(
                id=f"neglected-{project.id}",
                rule_type="neglected_project",
                level="warning",
                title=f"{project.name} has been quiet for a while.",
                rationale="This project still has active work, but it has not seen a recent completion. A small forward move may help it start moving again.",
                project_id=project.id,
                metadata={
                    "active_task_count": len(project_tasks),
                    "days_since_completion": days_since_completion,
                    "oldest_active_task_id": oldest_active.id,
                },
                reasons=[
                    RecommendationReason(label="Active tasks", value=str(len(project_tasks))),
                    RecommendationReason(
                        label="Last completion",
                        value=f"{days_since_completion} days ago" if days_since_completion is not None else "No completions yet",
                    ),
                ],
            )
        )
    items.sort(key=lambda item: ((item.metadata.get("days_since_completion") or 9999), -(int(item.metadata["active_task_count"]))))
    items.reverse()
    return items[:2]


def _large_task_breakdown_recommendations(active_tasks: list[Task], latest_touch: dict[str, datetime], now: datetime) -> list[RecommendationItem]:
    threshold = RECOMMENDATION_THRESHOLDS["large_task_stale_days"]
    large_tasks = [
        (task, _days_between(latest_touch.get(task.id, task.updated_at), now))
        for task in active_tasks
        if task.effort == "large" and _days_between(latest_touch.get(task.id, task.updated_at), now) >= threshold
    ]
    large_tasks.sort(key=lambda item: (-item[1], _due_sort_value(item[0], now), item[0].title.lower()))

    items: list[RecommendationItem] = []
    for task, stale_days in large_tasks[:2]:
        items.append(
            RecommendationItem(
                id=f"breakdown-{task.id}",
                rule_type="large_task_breakdown",
                level="info",
                title=f"Break down: {task.title}",
                rationale="Large tasks that sit untouched for several days usually become easier once the next concrete slice is defined.",
                task_id=task.id,
                metadata={"days_since_touch": stale_days},
                reasons=[
                    RecommendationReason(label="Effort", value="large"),
                    RecommendationReason(label="Untouched", value=f"{stale_days} days"),
                ],
            )
        )
    return items


def _small_wins_recommendation(active_tasks: list[Task], now: datetime) -> list[RecommendationItem]:
    active_count = len(active_tasks)
    large_task_count = len([task for task in active_tasks if task.effort == "large"])
    if active_count < RECOMMENDATION_THRESHOLDS["heavy_backlog_tasks"] and large_task_count < RECOMMENDATION_THRESHOLDS["heavy_backlog_large_tasks"]:
        return []

    small_tasks = [
        task for task in active_tasks if task.effort == "small" and task.status in {"inbox", "planned", "in_progress"}
    ]
    small_tasks.sort(
        key=lambda task: (
            _due_sort_value(task, now),
            -_priority_points(task.priority),
            _coerce_datetime(task.created_at),
            task.title.lower(),
        )
    )
    picked = small_tasks[: RECOMMENDATION_THRESHOLDS["small_wins_limit"]]
    if not picked:
        return []

    return [
        RecommendationItem(
            id="small-wins",
            rule_type="small_wins",
            level="info",
            title="A few small wins could reset momentum.",
            rationale="The backlog is heavy enough that finishing two or three small tasks may create useful space before tackling the bigger lifts.",
            metadata={
                "task_ids": [task.id for task in picked],
                "active_task_count": active_count,
                "large_task_count": large_task_count,
                "suggested_titles": [task.title for task in picked],
            },
            reasons=[
                RecommendationReason(label="Active backlog", value=str(active_count)),
                RecommendationReason(label="Large tasks", value=str(large_task_count)),
            ],
        )
    ]


def _compute_recommendation_items(
    tasks: list[Task],
    activity_events: ActivityEventRepository,
    project_repo: ProjectRepository,
    now: datetime,
) -> list[RecommendationItem]:
    active_tasks = _active_tasks(tasks)
    latest_touch = _latest_task_touch_map(active_tasks, activity_events)
    items = [
        *_stale_task_recommendations(active_tasks, latest_touch, now),
        *_overloaded_week_recommendation(active_tasks, now),
        *_neglected_project_recommendations(tasks, project_repo, now),
        *_large_task_breakdown_recommendations(active_tasks, latest_touch, now),
        *_small_wins_recommendation(active_tasks, now),
    ]
    level_order = {"warning": 0, "info": 1}
    items.sort(key=lambda item: (level_order[item.level], item.rule_type, item.title.lower()))
    return items


def _focus_items(active_tasks: list[Task], now: datetime) -> list[Task]:
    window_start = _start_of_day(now)
    window_end = _end_of_day(window_start + timedelta(days=6))
    due_this_week = [task for task in active_tasks if _due_within_window(task, window_start, window_end)]
    due_this_week.sort(
        key=lambda task: (
            -_priority_points(task.priority),
            _due_sort_value(task, now),
            -_effort_points(task.effort),
            task.title.lower(),
        )
    )
    if len(due_this_week) >= RECOMMENDATION_THRESHOLDS["focus_item_limit"]:
        return due_this_week[: RECOMMENDATION_THRESHOLDS["focus_item_limit"]]

    remaining = [task for task in active_tasks if task.id not in {item.id for item in due_this_week}]
    remaining.sort(
        key=lambda task: (
            -_priority_points(task.priority),
            -(1 if task.effort == "large" else 0),
            _coerce_datetime(task.created_at),
            task.title.lower(),
        )
    )
    return (due_this_week + remaining)[: RECOMMENDATION_THRESHOLDS["focus_item_limit"]]


def create_current_recommendations_snapshot(
    tasks: TaskRepository,
    projects: ProjectRepository,
    activity_events: ActivityEventRepository,
    snapshots: RecommendationSnapshotRepository,
) -> RecommendationSnapshot:
    now = utcnow()
    items = _compute_recommendation_items(tasks.list_all(), activity_events, projects, now)
    snapshot = RecommendationSnapshot(
        id=generate_id(),
        snapshot_kind="current_recommendations",
        generated_at=now,
        payload=_snapshot_payload(generated_at=now, items=items, thresholds=RECOMMENDATION_THRESHOLDS),
    )
    return snapshots.add(snapshot)


def create_weekly_preview_snapshot(
    tasks: TaskRepository,
    projects: ProjectRepository,
    activity_events: ActivityEventRepository,
    snapshots: RecommendationSnapshotRepository,
) -> tuple[RecommendationSnapshot, WeeklyPreviewResult]:
    now = utcnow()
    window_start = _start_of_day(now)
    window_end = _end_of_day(window_start + timedelta(days=6))
    all_tasks = tasks.list_all()
    active_tasks = _active_tasks(all_tasks)
    recommendation_items = _compute_recommendation_items(all_tasks, activity_events, projects, now)
    warnings = [item for item in recommendation_items if item.level == "warning"]
    focus_items = _focus_items(active_tasks, now)
    suggestion_summaries = [item.title for item in recommendation_items[:3]]
    result = WeeklyPreviewResult(
        generated_at=now,
        window_start=window_start,
        window_end=window_end,
        top_focus_items=focus_items,
        warnings=warnings,
        suggestion_summaries=suggestion_summaries,
        thresholds=RECOMMENDATION_THRESHOLDS,
    )
    snapshot = RecommendationSnapshot(
        id=generate_id(),
        snapshot_kind="weekly_preview",
        generated_at=now,
        window_start=window_start,
        window_end=window_end,
        payload=_snapshot_payload(
            generated_at=now,
            items=warnings,
            thresholds=RECOMMENDATION_THRESHOLDS,
            top_focus_items=focus_items,
            window_start=window_start,
            window_end=window_end,
            suggestion_summaries=suggestion_summaries,
        ),
    )
    return snapshots.add(snapshot), result
