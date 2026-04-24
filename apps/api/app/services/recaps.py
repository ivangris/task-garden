from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from fastapi import HTTPException, status

from app.domain.entities import (
    ActivityEvent,
    HighlightCard,
    Milestone,
    Project,
    ProjectSummary,
    RecapMetricSnapshot,
    RecapNarrative,
    RecapPeriod,
    RecoveryEvent,
    StreakSummary,
    Task,
    UnlockLedgerEntry,
    XPLedgerEntry,
)
from app.repositories.interfaces import (
    ActivityEventRepository,
    HighlightCardRepository,
    MilestoneRepository,
    ProjectRepository,
    ProjectSummaryRepository,
    RecapMetricSnapshotRepository,
    RecapPeriodRepository,
    RecoveryEventRepository,
    StreakSummaryRepository,
    TaskRepository,
    UnlockLedgerRepository,
    XPLedgerRepository,
)
from app.schemas.recaps import (
    HighlightCardResponse,
    MilestoneResponse,
    ProjectSummaryResponse,
    RecapMetricValueResponse,
    RecapNarrativeResponse,
    RecapPeriodResponse,
    StreakSummaryResponse,
)
from app.services.common import generate_id, utcnow


MAX_TILE_UNITS = 36
ACTIVE_STATUSES = {"inbox", "planned", "in_progress", "blocked"}
EFFORT_SCORE = {"small": 1, "medium": 2, "large": 3}
PRIORITY_SCORE = {"low": 0, "medium": 1, "high": 2, "critical": 3}
PERIOD_TYPES = {"weekly", "monthly", "yearly"}
ACTIVE_DAY_EVENT_TYPES = {
    "raw_entry_created",
    "task_created",
    "task_updated",
    "task_completed",
    "task_reopened",
    "task_confirmed_from_extraction",
    "project_created",
    "transcription_completed",
}


@dataclass(slots=True)
class _StreakSegment:
    start: date
    end: date
    length: int


@dataclass(slots=True)
class _GardenPeriodSummary:
    start_stage_key: str
    end_stage_key: str
    start_health_score: int
    end_health_score: int
    health_delta: int
    xp_gained: int
    unlock_count: int
    recovery_points: int
    overdue_recoveries: int


@dataclass(slots=True)
class _PeriodScope:
    period_type: str
    label: str
    window_start: datetime
    window_end: datetime


def _coerce_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _start_of_day(value: date) -> datetime:
    return datetime.combine(value, time.min, tzinfo=UTC)


def _end_of_day(value: date) -> datetime:
    return datetime.combine(value, time.max, tzinfo=UTC)


def _period_scope(period_type: str, anchor: datetime | None = None) -> _PeriodScope:
    if period_type not in PERIOD_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported recap period.")

    now = _coerce_datetime(anchor) or utcnow()
    today = now.date()
    if period_type == "weekly":
        start_day = today - timedelta(days=today.weekday())
        end_day = start_day + timedelta(days=6)
        label = f"Week of {start_day.strftime('%b %d, %Y')}"
    elif period_type == "monthly":
        start_day = date(today.year, today.month, 1)
        if today.month == 12:
            end_day = date(today.year, 12, 31)
        else:
            end_day = date(today.year, today.month + 1, 1) - timedelta(days=1)
        label = start_day.strftime("%B %Y")
    else:
        start_day = date(today.year, 1, 1)
        end_day = date(today.year, 12, 31)
        label = str(today.year)

    return _PeriodScope(
        period_type=period_type,
        label=label,
        window_start=_start_of_day(start_day),
        window_end=_end_of_day(end_day),
    )


def _within_window(value: datetime | None, start: datetime, end: datetime) -> bool:
    normalized = _coerce_datetime(value)
    return normalized is not None and start <= normalized <= end


def _completed_tasks(tasks: list[Task], start: datetime, end: datetime) -> list[Task]:
    items = [task for task in tasks if _within_window(task.completed_at, start, end)]
    items.sort(key=lambda item: (_coerce_datetime(item.completed_at) or end, item.title.lower()))
    return items


def _created_tasks(tasks: list[Task], start: datetime, end: datetime) -> list[Task]:
    items = [task for task in tasks if _within_window(task.created_at, start, end)]
    items.sort(key=lambda item: (_coerce_datetime(item.created_at) or end, item.title.lower()))
    return items


def _reopened_tasks(activity_events: list[ActivityEvent], start: datetime, end: datetime) -> int:
    return len([event for event in activity_events if event.event_type == "task_reopened" and _within_window(event.created_at, start, end)])


def _activity_days(activity_events: list[ActivityEvent], completed: list[Task]) -> set[date]:
    days = {
        (_coerce_datetime(event.created_at) or utcnow()).date()
        for event in activity_events
        if event.event_type in ACTIVE_DAY_EVENT_TYPES
    }
    days.update((_coerce_datetime(task.completed_at) or utcnow()).date() for task in completed if task.completed_at is not None)
    return days


def _completion_days(tasks: list[Task], end: datetime) -> list[date]:
    days = {
        (_coerce_datetime(task.completed_at) or utcnow()).date()
        for task in tasks
        if task.completed_at is not None and (_coerce_datetime(task.completed_at) or utcnow()) <= end
    }
    return sorted(days)


def _streak_segments(days: list[date]) -> list[_StreakSegment]:
    if not days:
        return []
    segments: list[_StreakSegment] = []
    start = days[0]
    previous = days[0]
    length = 1
    for current in days[1:]:
        if (current - previous).days == 1:
            length += 1
        else:
            segments.append(_StreakSegment(start=start, end=previous, length=length))
            start = current
            length = 1
        previous = current
    segments.append(_StreakSegment(start=start, end=previous, length=length))
    return segments


def _current_streak_days(segments: list[_StreakSegment], window_end: datetime) -> int:
    if not segments:
        return 0
    last = segments[-1]
    return last.length if last.end == window_end.date() else 0


def _period_best_segment(segments: list[_StreakSegment], start: datetime, end: datetime) -> _StreakSegment | None:
    eligible = [segment for segment in segments if start.date() <= segment.end <= end.date()]
    if not eligible:
        return None
    eligible.sort(key=lambda item: (-item.length, item.end, item.start))
    return eligible[0]


def _estimate_garden_state_from_recovery_points(total_recovery_points: int) -> tuple[str, int]:
    visible_units = max(0, min(MAX_TILE_UNITS, total_recovery_points))
    lush_tiles = visible_units // 3
    remainder = visible_units % 3
    restored_tiles = lush_tiles + (1 if remainder > 0 else 0)
    healthy_tiles = lush_tiles + (1 if remainder >= 2 else 0)
    health_score = int(round((visible_units / MAX_TILE_UNITS) * 100)) if MAX_TILE_UNITS else 0

    if lush_tiles >= 4:
        stage_key = "lush_oasis"
    elif healthy_tiles >= 4:
        stage_key = "healthy_garden"
    elif restored_tiles > 0:
        stage_key = "recovering_plot"
    else:
        stage_key = "neglected_desert"
    return stage_key, health_score


def _recovery_points_from_xp(xp_amount: int) -> int:
    return max(1, int(round(xp_amount / 18)))


def _garden_summary(entries: list[XPLedgerEntry], unlocks: list[UnlockLedgerEntry], completed: list[Task], start: datetime, end: datetime) -> _GardenPeriodSummary:
    xp_before = sum(entry.xp_amount for entry in entries if (_coerce_datetime(entry.awarded_at) or end) < start)
    xp_through = sum(entry.xp_amount for entry in entries if (_coerce_datetime(entry.awarded_at) or end) <= end)
    xp_gained = sum(entry.xp_amount for entry in entries if _within_window(entry.awarded_at, start, end))

    recovery_before = sum(_recovery_points_from_xp(entry.xp_amount) for entry in entries if (_coerce_datetime(entry.awarded_at) or end) < start)
    recovery_through = sum(_recovery_points_from_xp(entry.xp_amount) for entry in entries if (_coerce_datetime(entry.awarded_at) or end) <= end)

    start_stage, start_health = _estimate_garden_state_from_recovery_points(recovery_before)
    end_stage, end_health = _estimate_garden_state_from_recovery_points(recovery_through)

    unlock_count = len([item for item in unlocks if _within_window(item.unlocked_at, start, end)])
    overdue_recoveries = len(
        [
            task
            for task in completed
            if task.due_date is not None
            and task.completed_at is not None
            and (_coerce_datetime(task.completed_at) or end) > (_coerce_datetime(task.due_date) or start)
        ]
    )
    return _GardenPeriodSummary(
        start_stage_key=start_stage,
        end_stage_key=end_stage,
        start_health_score=start_health,
        end_health_score=end_health,
        health_delta=end_health - start_health,
        xp_gained=xp_gained,
        unlock_count=unlock_count,
        recovery_points=recovery_through - recovery_before,
        overdue_recoveries=overdue_recoveries,
    )


def _completion_rate(completed_count: int, created_count: int) -> float | None:
    if created_count <= 0:
        return None
    return round((completed_count / created_count) * 100, 1)


def _project_name(task: Task, project_map: dict[str, Project]) -> str:
    if task.project_id and task.project_id in project_map:
        return project_map[task.project_id].name
    return "Independent"


def _project_summaries(completed: list[Task], xp_entries: list[XPLedgerEntry], project_map: dict[str, Project], period_id: str) -> list[ProjectSummary]:
    xp_by_task = {entry.task_id: entry.xp_amount for entry in xp_entries}
    groups: dict[tuple[str | None, str], list[Task]] = defaultdict(list)
    for task in completed:
        groups[(task.project_id, _project_name(task, project_map))].append(task)

    total_completed = max(1, len(completed))
    items: list[ProjectSummary] = []
    for sort_order, ((project_id, project_name), tasks_for_project) in enumerate(
        sorted(groups.items(), key=lambda item: (-len(item[1]), -sum(xp_by_task.get(task.id, 0) for task in item[1]), item[0][1].lower()))
    ):
        counts = Counter(task.effort for task in tasks_for_project)
        latest_completion = max((_coerce_datetime(task.completed_at) for task in tasks_for_project if task.completed_at is not None), default=None)
        items.append(
            ProjectSummary(
                id=generate_id(),
                period_id=period_id,
                project_id=project_id,
                project_name=project_name,
                completed_task_count=len(tasks_for_project),
                xp_gained=sum(xp_by_task.get(task.id, 0) for task in tasks_for_project),
                completion_share=round(len(tasks_for_project) / total_completed, 3),
                effort_small_count=counts.get("small", 0),
                effort_medium_count=counts.get("medium", 0),
                effort_large_count=counts.get("large", 0),
                latest_completion_at=latest_completion,
                sort_order=sort_order,
            )
        )
    return items


def _milestones(
    all_tasks: list[Task],
    unlocks: list[UnlockLedgerEntry],
    garden_summary: _GardenPeriodSummary,
    period_id: str,
    start: datetime,
    end: datetime,
) -> list[Milestone]:
    items: list[Milestone] = []
    completed_all = sorted(
        [task for task in all_tasks if task.completed_at is not None and (_coerce_datetime(task.completed_at) or end) <= end],
        key=lambda task: (_coerce_datetime(task.completed_at) or end, task.title.lower()),
    )
    for threshold in (10, 50, 100):
        if len(completed_all) < threshold:
            continue
        task = completed_all[threshold - 1]
        completed_at = _coerce_datetime(task.completed_at)
        if completed_at and start <= completed_at <= end:
            items.append(
                Milestone(
                    id=generate_id(),
                    period_id=period_id,
                    milestone_key=f"completed_{threshold}",
                    title=f"Hit {threshold} completed tasks",
                    description=f"{task.title} marked the moment you crossed {threshold} completed tasks overall.",
                    metric_value=threshold,
                    detected_at=completed_at,
                    sort_order=len(items),
                )
            )

    segments = _streak_segments(_completion_days(all_tasks, end))
    best_segment = max(segments, key=lambda item: item.length, default=None)
    if best_segment and start.date() <= best_segment.end <= end.date() and best_segment.length >= 3:
        items.append(
            Milestone(
                id=generate_id(),
                period_id=period_id,
                milestone_key="longest_streak_reached",
                title="Set a new streak high-water mark",
                description=f"You reached a {best_segment.length}-day completion streak.",
                metric_value=best_segment.length,
                detected_at=_end_of_day(best_segment.end),
                sort_order=len(items),
            )
        )

    rare_unlock = next((item for item in unlocks if item.unlock_key == "rare_bloom" and _within_window(item.unlocked_at, start, end)), None)
    if rare_unlock is not None:
        items.append(
            Milestone(
                id=generate_id(),
                period_id=period_id,
                milestone_key="rare_bloom_unlock",
                title="Unlocked the rare bloom",
                description="A rare garden unlock landed in this recap window.",
                metric_value=rare_unlock.threshold_value,
                detected_at=rare_unlock.unlocked_at,
                sort_order=len(items),
            )
        )

    if garden_summary.health_delta >= 15:
        items.append(
            Milestone(
                id=generate_id(),
                period_id=period_id,
                milestone_key="strong_recovery_period",
                title="Strong recovery stretch",
                description=f"Garden health moved up {garden_summary.health_delta} points across the period.",
                metric_value=garden_summary.health_delta,
                detected_at=end,
                sort_order=len(items),
            )
        )
    return items


def _biggest_win(completed: list[Task]) -> Task | None:
    if not completed:
        return None
    return max(
        completed,
        key=lambda task: (
            EFFORT_SCORE.get(task.effort, 1),
            PRIORITY_SCORE.get(task.priority, 0),
            len(task.title),
            task.title.lower(),
        ),
    )


def _metrics(
    *,
    period_id: str,
    scope: _PeriodScope,
    completed: list[Task],
    created: list[Task],
    activity_days: set[date],
    reopened_count: int,
    xp_entries: list[XPLedgerEntry],
    unlocks: list[UnlockLedgerEntry],
    project_summaries: list[ProjectSummary],
    streak_summary: StreakSummary,
    garden_summary: _GardenPeriodSummary,
) -> list[RecapMetricSnapshot]:
    effort_distribution = Counter(task.effort for task in completed)
    priority_distribution = Counter(task.priority for task in completed)
    top_project_names = [item.project_name for item in project_summaries[:3]]
    biggest_win = _biggest_win(completed)
    completion_rate = _completion_rate(len(completed), len(created))

    values = [
        ("total_tasks_completed", float(len(completed)), None, {}),
        ("active_days", float(len(activity_days)), None, {}),
        ("completion_rate", completion_rate, None, {}),
        ("reopened_task_count", float(reopened_count), None, {}),
        ("overdue_recovered_count", float(garden_summary.overdue_recoveries), None, {}),
        ("xp_gained", float(garden_summary.xp_gained), None, {}),
        ("unlocks_earned", float(garden_summary.unlock_count), None, {}),
        ("garden_health_start", float(garden_summary.start_health_score), None, {}),
        ("garden_health_end", float(garden_summary.end_health_score), None, {}),
        ("garden_health_delta", float(garden_summary.health_delta), None, {}),
        ("garden_stage_change", None, f"{garden_summary.start_stage_key}->{garden_summary.end_stage_key}", {}),
        ("effort_distribution", None, None, dict(effort_distribution)),
        ("priority_distribution", None, None, dict(priority_distribution)),
        ("top_projects", None, None, {"names": top_project_names}),
        ("longest_streak_days", float(streak_summary.longest_streak_days), None, {}),
        ("current_streak_days", float(streak_summary.current_streak_days), None, {}),
        ("period_best_streak_days", float(streak_summary.period_best_streak_days), None, {}),
        ("biggest_completed_task", None, biggest_win.title if biggest_win else None, {}),
    ]

    metrics: list[RecapMetricSnapshot] = []
    for sort_order, (metric_key, numeric_value, text_value, json_value) in enumerate(values):
        metrics.append(
            RecapMetricSnapshot(
                id=generate_id(),
                period_id=period_id,
                metric_key=metric_key,
                sort_order=sort_order,
                numeric_value=numeric_value,
                text_value=text_value,
                json_value=json_value,
            )
        )
    return metrics


def _cards(
    *,
    period_id: str,
    scope: _PeriodScope,
    completed: list[Task],
    project_summaries: list[ProjectSummary],
    streak_summary: StreakSummary,
    garden_summary: _GardenPeriodSummary,
    milestones: list[Milestone],
) -> list[HighlightCard]:
    biggest_win = _biggest_win(completed)
    top_project = project_summaries[0] if project_summaries else None
    cards: list[HighlightCard] = []

    hero_title = {
        "weekly": "This week in momentum",
        "monthly": "This month in momentum",
        "yearly": "Look at all you accomplished",
    }[scope.period_type]
    hero_support = {
        "weekly": "A concise snapshot of what moved forward.",
        "monthly": "Your strongest themes and recoveries from the month.",
        "yearly": "A grounded year-in-review built from the work you actually finished.",
    }[scope.period_type]
    cards.append(
        HighlightCard(
            id=generate_id(),
            period_id=period_id,
            card_type="hero",
            title=hero_title,
            subtitle=scope.label,
            primary_value=str(len(completed)),
            secondary_value="tasks completed",
            supporting_text=hero_support,
            visual_hint="gradient_hero",
            sort_order=0,
        )
    )

    cards.append(
        HighlightCard(
            id=generate_id(),
            period_id=period_id,
            card_type="active_days",
            title="You showed up",
            subtitle="Active days",
            primary_value=str(streak_summary.active_days),
            secondary_value="days",
            supporting_text="Momentum compounds when work happens across multiple days, not just one big burst.",
            visual_hint="cool_glow",
            sort_order=1,
        )
    )

    if top_project is not None:
        cards.append(
            HighlightCard(
                id=generate_id(),
                period_id=period_id,
                card_type="top_project",
                title="Top project theme",
                subtitle=top_project.project_name,
                primary_value=str(top_project.completed_task_count),
                secondary_value="completed tasks",
                supporting_text=f"{top_project.project_name} carried the biggest share of finished work in this period.",
                visual_hint="project_focus",
                sort_order=2,
            )
        )

    cards.append(
        HighlightCard(
            id=generate_id(),
            period_id=period_id,
            card_type="streak",
            title="Streak and comeback",
            subtitle="Consistency snapshot",
            primary_value=str(streak_summary.period_best_streak_days),
            secondary_value="best streak days",
            supporting_text=f"Current streak: {streak_summary.current_streak_days} days. Longest overall streak: {streak_summary.longest_streak_days} days.",
            visual_hint="streak",
            sort_order=3,
        )
    )

    cards.append(
        HighlightCard(
            id=generate_id(),
            period_id=period_id,
            card_type="garden",
            title="Garden transformation",
            subtitle=f"{garden_summary.start_stage_key.replace('_', ' ')} to {garden_summary.end_stage_key.replace('_', ' ')}",
            primary_value=f"+{garden_summary.xp_gained} XP",
            secondary_value=f"{garden_summary.health_delta:+d} health",
            supporting_text=f"Unlocks earned: {garden_summary.unlock_count}. Overdue recoveries: {garden_summary.overdue_recoveries}.",
            visual_hint="garden",
            sort_order=4,
        )
    )

    if biggest_win is not None:
        cards.append(
            HighlightCard(
                id=generate_id(),
                period_id=period_id,
                card_type="biggest_win",
                title="Notable win",
                subtitle=biggest_win.title,
                primary_value=biggest_win.effort,
                secondary_value=biggest_win.priority,
                supporting_text="This was the heaviest completed lift in the period based on effort and priority.",
                visual_hint="warm_spotlight",
                sort_order=5,
            )
        )

    if milestones:
        first = milestones[0]
        cards.append(
            HighlightCard(
                id=generate_id(),
                period_id=period_id,
                card_type="milestone",
                title="Milestone reached",
                subtitle=first.title,
                primary_value=str(first.metric_value) if first.metric_value is not None else None,
                secondary_value=None,
                supporting_text=first.description,
                visual_hint="milestone",
                sort_order=6,
            )
        )
    return cards


def _response(
    period: RecapPeriod,
    metrics: list[RecapMetricSnapshot],
    cards: list[HighlightCard],
    milestones: list[Milestone],
    streak_summary: StreakSummary | None,
    project_summaries: list[ProjectSummary],
    narrative: RecapNarrative | None = None,
) -> RecapPeriodResponse:
    return RecapPeriodResponse(
        id=period.id,
        period_type=period.period_type,  # type: ignore[arg-type]
        period_label=period.period_label,
        window_start=period.window_start,
        window_end=period.window_end,
        generated_at=period.generated_at,
        metrics=[
            RecapMetricValueResponse(
                metric_key=item.metric_key,
                numeric_value=item.numeric_value,
                text_value=item.text_value,
                json_value=item.json_value,
            )
            for item in metrics
        ],
        cards=[HighlightCardResponse.model_validate(item) for item in cards],
        milestones=[MilestoneResponse.model_validate(item) for item in milestones],
        streak_summary=StreakSummaryResponse.model_validate(streak_summary) if streak_summary is not None else None,
        project_summaries=[ProjectSummaryResponse.model_validate(item) for item in project_summaries],
        narrative=RecapNarrativeResponse.model_validate(narrative) if narrative is not None else None,
    )


def generate_recap(
    period_type: str,
    periods: RecapPeriodRepository,
    metrics_repo: RecapMetricSnapshotRepository,
    cards_repo: HighlightCardRepository,
    milestones_repo: MilestoneRepository,
    streak_repo: StreakSummaryRepository,
    project_repo: ProjectSummaryRepository,
    tasks: TaskRepository,
    projects: ProjectRepository,
    activity_events: ActivityEventRepository,
    xp_ledger: XPLedgerRepository,
    unlock_ledger: UnlockLedgerRepository,
    recovery_events: RecoveryEventRepository,
) -> RecapPeriodResponse:
    scope = _period_scope(period_type)
    now = utcnow()
    all_tasks = tasks.list_all()
    all_projects = {project.id: project for project in projects.list_all()}
    all_activity = [event for event in activity_events.list_all() if _within_window(event.created_at, scope.window_start, scope.window_end)]
    completed = _completed_tasks(all_tasks, scope.window_start, scope.window_end)
    created = _created_tasks(all_tasks, scope.window_start, scope.window_end)
    xp_entries = [entry for entry in xp_ledger.list_all() if _within_window(entry.awarded_at, scope.window_start, scope.window_end)]
    xp_entries_all = xp_ledger.list_all()
    unlocks = unlock_ledger.list_all()
    _ = [event for event in recovery_events.list_all() if _within_window(event.recorded_at, scope.window_start, scope.window_end)]
    activity_days = _activity_days(all_activity, completed)
    completion_days = _completion_days(all_tasks, scope.window_end)
    segments = _streak_segments(completion_days)
    best_segment = _period_best_segment(segments, scope.window_start, scope.window_end)
    streak_summary = StreakSummary(
        id=generate_id(),
        period_id="",
        current_streak_days=_current_streak_days(segments, scope.window_end),
        longest_streak_days=max((segment.length for segment in segments), default=0),
        period_best_streak_days=best_segment.length if best_segment else 0,
        active_days=len(activity_days),
        streak_start=_start_of_day(best_segment.start) if best_segment else None,
        streak_end=_end_of_day(best_segment.end) if best_segment else None,
    )

    period = periods.upsert(
        RecapPeriod(
            id=generate_id(),
            period_type=scope.period_type,
            period_label=scope.label,
            window_start=scope.window_start,
            window_end=scope.window_end,
            generated_at=now,
        )
    )
    streak_summary.period_id = period.id
    project_summaries = _project_summaries(completed, xp_entries, all_projects, period.id)
    garden_summary = _garden_summary(xp_entries_all, unlocks, completed, scope.window_start, scope.window_end)
    milestone_items = _milestones(all_tasks, unlocks, garden_summary, period.id, scope.window_start, scope.window_end)
    metric_items = _metrics(
        period_id=period.id,
        scope=scope,
        completed=completed,
        created=created,
        activity_days=activity_days,
        reopened_count=_reopened_tasks(all_activity, scope.window_start, scope.window_end),
        xp_entries=xp_entries,
        unlocks=unlocks,
        project_summaries=project_summaries,
        streak_summary=streak_summary,
        garden_summary=garden_summary,
    )
    card_items = _cards(
        period_id=period.id,
        scope=scope,
        completed=completed,
        project_summaries=project_summaries,
        streak_summary=streak_summary,
        garden_summary=garden_summary,
        milestones=milestone_items,
    )

    saved_metrics = metrics_repo.replace_for_period(period.id, metric_items)
    saved_cards = cards_repo.replace_for_period(period.id, card_items)
    saved_milestones = milestones_repo.replace_for_period(period.id, milestone_items)
    saved_streak = streak_repo.replace_for_period(period.id, streak_summary)
    saved_projects = project_repo.replace_for_period(period.id, project_summaries)
    return _response(period, saved_metrics, saved_cards, saved_milestones, saved_streak, saved_projects)


def get_recap(
    period_id: str,
    periods: RecapPeriodRepository,
    metrics_repo: RecapMetricSnapshotRepository,
    cards_repo: HighlightCardRepository,
    milestones_repo: MilestoneRepository,
    streak_repo: StreakSummaryRepository,
    project_repo: ProjectSummaryRepository,
    narrative: RecapNarrative | None = None,
) -> RecapPeriodResponse:
    period = periods.get(period_id)
    if period is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recap period not found.")
    return _response(
        period,
        metrics_repo.list_for_period(period_id),
        cards_repo.list_for_period(period_id),
        milestones_repo.list_for_period(period_id),
        streak_repo.get_for_period(period_id),
        project_repo.list_for_period(period_id),
        narrative,
    )
