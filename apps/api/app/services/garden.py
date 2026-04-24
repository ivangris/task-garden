from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.entities import (
    DecayEvent,
    DecorationInstance,
    GardenState,
    GardenTile,
    GardenZone,
    PlantInstance,
    RecoveryEvent,
    Task,
    UnlockLedgerEntry,
    XPLedgerEntry,
)
from app.repositories.interfaces import (
    ActivityEventRepository,
    DecayEventRepository,
    DecorationInstanceRepository,
    GardenStateRepository,
    GardenTileRepository,
    GardenZoneRepository,
    PlantInstanceRepository,
    RecoveryEventRepository,
    TaskRepository,
    UnlockLedgerRepository,
    XPLedgerRepository,
)
from app.services.activity import log_activity
from app.services.common import generate_id, utcnow


BASELINE_KEY = "neglected_desert_plot"
GARDEN_STATE_ID = "garden-primary"
TILE_STATE_ORDER = ("desert", "recovering", "healthy", "lush")
XP_BY_EFFORT = {"small": 10, "medium": 25, "large": 60}
PRIORITY_BONUS = {"low": 0, "medium": 2, "high": 5, "critical": 8}
DECAY_EFFORT_WEIGHT = {"small": 1, "medium": 2, "large": 4}
DECAY_PRIORITY_WEIGHT = {"low": 0, "medium": 1, "high": 2, "critical": 3}
UNLOCK_DEFINITIONS = (
    ("starter_seeds", "plant", 25),
    ("watering_can", "tool", 75),
    ("moss_path", "decoration", 150),
    ("fountain_repair", "feature", 300),
    ("rare_bloom", "plant", 500),
    ("sun_arch", "decoration", 700),
)
ZONE_BLUEPRINTS = (
    ("zone-west", "West Patch", "west_patch", 1, ((0, 0), (1, 0), (0, 1), (1, 1))),
    ("zone-center", "Fountain Court", "fountain_court", 2, ((2, 0), (3, 0), (2, 1), (3, 1))),
    ("zone-east", "East Grove", "east_grove", 3, ((4, 0), (5, 0), (4, 1), (5, 1))),
)
ACTIVE_TASK_STATUSES = {"inbox", "planned", "in_progress", "blocked"}
MAX_TILE_UNITS = len(ZONE_BLUEPRINTS) * 4 * 3


@dataclass(slots=True)
class GardenRecomputeResult:
    state: GardenState
    zones: list[GardenZone]
    tiles: list[GardenTile]
    plants: list[PlantInstance]
    decorations: list[DecorationInstance]
    xp_entries: list[XPLedgerEntry]
    unlocks: list[UnlockLedgerEntry]
    decay_events: list[DecayEvent]
    recovery_events: list[RecoveryEvent]


def _coerce_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value


def _as_day(value: datetime) -> datetime.date:
    normalized = _coerce_datetime(value)
    assert normalized is not None
    return normalized.date()


def _streak_multiplier(streak_days: int) -> float:
    if streak_days >= 21:
        return 1.35
    if streak_days >= 7:
        return 1.2
    if streak_days >= 3:
        return 1.1
    return 1.0


def _build_zones(now: datetime) -> list[GardenZone]:
    return [
        GardenZone(
            id=zone_id,
            name=name,
            zone_key=zone_key,
            sort_order=sort_order,
            tile_count=len(coords),
            unlocked_at=now if sort_order == 1 else None,
        )
        for zone_id, name, zone_key, sort_order, coords in ZONE_BLUEPRINTS
    ]


def _completed_tasks(tasks: list[Task]) -> list[Task]:
    items = [task for task in tasks if task.completed_at is not None and not task.is_deleted]
    items.sort(key=lambda task: (_coerce_datetime(task.completed_at) or utcnow(), task.title.lower()))
    return items


def _active_tasks(tasks: list[Task]) -> list[Task]:
    return [task for task in tasks if task.status in ACTIVE_TASK_STATUSES and not task.is_deleted]


def _overdue_tasks(tasks: list[Task], now: datetime) -> list[Task]:
    normalized_now = _coerce_datetime(now)
    assert normalized_now is not None
    overdue: list[Task] = []
    for task in tasks:
        due_date = _coerce_datetime(task.due_date)
        if due_date is not None and due_date < normalized_now:
            overdue.append(task)
    overdue.sort(key=lambda task: (_coerce_datetime(task.due_date) or normalized_now, task.title.lower()))
    return overdue


def _build_xp_entries(completed_tasks: list[Task]) -> tuple[list[XPLedgerEntry], list[RecoveryEvent], int]:
    xp_entries: list[XPLedgerEntry] = []
    recovery_events: list[RecoveryEvent] = []
    total_recovery_points = 0
    streak_days = 0
    last_completion_day = None

    for task in completed_tasks:
        completed_at = _coerce_datetime(task.completed_at) or utcnow()
        completion_day = _as_day(completed_at)
        if last_completion_day is None:
            streak_days = 1
        elif (completion_day - last_completion_day).days == 0:
            streak_days = max(streak_days, 1)
        elif (completion_day - last_completion_day).days == 1:
            streak_days += 1
        else:
            streak_days = 1
        last_completion_day = completion_day

        effort_value = XP_BY_EFFORT.get(task.effort, 10)
        priority_bonus = PRIORITY_BONUS.get(task.priority, 0)
        multiplier = _streak_multiplier(streak_days)
        xp_amount = int(round((effort_value + priority_bonus) * multiplier))
        recovery_points = max(1, int(round(xp_amount / 18)))

        xp_entries.append(
            XPLedgerEntry(
                id=generate_id(),
                task_id=task.id,
                xp_amount=xp_amount,
                effort_value=effort_value,
                priority_bonus=priority_bonus,
                streak_multiplier=multiplier,
                awarded_at=completed_at,
            )
        )
        recovery_events.append(
            RecoveryEvent(
                id=generate_id(),
                task_id=task.id,
                task_title=task.title,
                recovery_points=recovery_points,
                xp_amount=xp_amount,
                recorded_at=completed_at,
            )
        )
        total_recovery_points += recovery_points

    return xp_entries, recovery_events, total_recovery_points


def _build_decay_events(active_tasks: list[Task], now: datetime) -> tuple[list[DecayEvent], int]:
    if not active_tasks:
        return [], 0

    overdue_tasks = _overdue_tasks(active_tasks, now)
    if not overdue_tasks:
        return [], 0

    decay_events: list[DecayEvent] = []
    total_decay_points = 0
    normalized_now = _coerce_datetime(now) or utcnow()
    for task in overdue_tasks:
        due_date = _coerce_datetime(task.due_date) or normalized_now
        days_overdue = max(1, (normalized_now.date() - due_date.date()).days)
        age_pressure = min(3, max(1, ((days_overdue - 1) // 3) + 1))
        decay_points = DECAY_EFFORT_WEIGHT.get(task.effort, 1) + DECAY_PRIORITY_WEIGHT.get(task.priority, 0) + age_pressure
        decay_events.append(
            DecayEvent(
                id=generate_id(),
                task_id=task.id,
                task_title=task.title,
                days_overdue=days_overdue,
                decay_points=decay_points,
                recorded_at=normalized_now,
            )
        )
        total_decay_points += decay_points
    return decay_events, total_decay_points


def _unlock_entries(total_xp: int, now: datetime) -> list[UnlockLedgerEntry]:
    return [
        UnlockLedgerEntry(
            id=generate_id(),
            unlock_key=unlock_key,
            unlock_type=unlock_type,
            threshold_value=threshold,
            unlocked_at=now,
        )
        for unlock_key, unlock_type, threshold in UNLOCK_DEFINITIONS
        if total_xp >= threshold
    ]


def _tile_state_for_units(units: int) -> str:
    return TILE_STATE_ORDER[max(0, min(units, 3))]


def _build_tiles(zones: list[GardenZone], growth_units: int, decay_units: int, now: datetime) -> list[GardenTile]:
    before_units_remaining = max(0, min(MAX_TILE_UNITS, growth_units))
    after_units_remaining = max(0, min(MAX_TILE_UNITS, growth_units - decay_units))
    tiles: list[GardenTile] = []
    zone_map = {zone.id: zone for zone in zones}

    for zone_id, _, _, _, coords in ZONE_BLUEPRINTS:
        zone = zone_map[zone_id]
        for tile_index, (coord_x, coord_y) in enumerate(coords):
            before_units = min(3, before_units_remaining)
            before_units_remaining = max(0, before_units_remaining - before_units)
            after_units = min(3, after_units_remaining)
            after_units_remaining = max(0, after_units_remaining - after_units)
            tiles.append(
                GardenTile(
                    id=f"{zone.id}-tile-{tile_index}",
                    zone_id=zone.id,
                    tile_index=tile_index,
                    coord_x=coord_x,
                    coord_y=coord_y,
                    tile_state=_tile_state_for_units(after_units),
                    growth_units=after_units,
                    decay_points=max(0, before_units - after_units),
                    last_changed_at=now,
                )
            )
    tiles.sort(key=lambda tile: (tile.coord_y, tile.coord_x))
    return tiles


def _build_plants_and_decorations(
    tiles: list[GardenTile],
    unlocks: list[UnlockLedgerEntry],
) -> tuple[list[PlantInstance], list[DecorationInstance]]:
    unlock_keys = {entry.unlock_key: entry for entry in unlocks}
    plants: list[PlantInstance] = []
    decorations: list[DecorationInstance] = []

    recovering_tiles = [tile for tile in tiles if tile.tile_state in {"recovering", "healthy", "lush"}]
    lush_tiles = [tile for tile in tiles if tile.tile_state == "lush"]
    center_tiles = [tile for tile in tiles if tile.zone_id == "zone-center"]

    if "starter_seeds" in unlock_keys:
        for index, tile in enumerate(recovering_tiles[:2]):
            plants.append(
                PlantInstance(
                    id=f"plant-{tile.id}-{index}",
                    garden_tile_id=tile.id,
                    plant_key="sage_clump" if index else "desert_sprout",
                    growth_stage="sprouting" if tile.tile_state == "recovering" else "growing",
                    unlocked_at=unlock_keys["starter_seeds"].unlocked_at,
                )
            )

    if "rare_bloom" in unlock_keys and lush_tiles:
        tile = lush_tiles[-1]
        plants.append(
            PlantInstance(
                id=f"plant-{tile.id}-rare",
                garden_tile_id=tile.id,
                plant_key="rare_bloom",
                growth_stage="blooming",
                unlocked_at=unlock_keys["rare_bloom"].unlocked_at,
            )
        )

    if "moss_path" in unlock_keys and center_tiles:
        decorations.append(
            DecorationInstance(
                id="decoration-moss-path",
                garden_tile_id=center_tiles[0].id,
                decoration_key="moss_path",
                variant_key="patched",
                unlocked_at=unlock_keys["moss_path"].unlocked_at,
            )
        )

    if "fountain_repair" in unlock_keys and center_tiles:
        decorations.append(
            DecorationInstance(
                id="decoration-fountain-core",
                garden_tile_id=center_tiles[-1].id,
                decoration_key="fountain_core",
                variant_key="restored",
                unlocked_at=unlock_keys["fountain_repair"].unlocked_at,
            )
        )

    if "sun_arch" in unlock_keys and lush_tiles:
        decorations.append(
            DecorationInstance(
                id="decoration-sun-arch",
                garden_tile_id=lush_tiles[0].id,
                decoration_key="sun_arch",
                variant_key="open",
                unlocked_at=unlock_keys["sun_arch"].unlocked_at,
            )
        )

    return plants, decorations


def _stage_key(restored_tile_count: int, healthy_tile_count: int, lush_tile_count: int) -> str:
    if lush_tile_count >= 4:
        return "lush_oasis"
    if healthy_tile_count >= 4:
        return "healthy_garden"
    if restored_tile_count > 0:
        return "recovering_plot"
    return "neglected_desert"


def _level_from_xp(total_xp: int) -> int:
    return max(1, (total_xp // 100) + 1)


def _ensure_baseline_state(
    state_repo: GardenStateRepository,
    zone_repo: GardenZoneRepository,
    tile_repo: GardenTileRepository,
    plant_repo: PlantInstanceRepository,
    decoration_repo: DecorationInstanceRepository,
) -> GardenState:
    existing = state_repo.get_current()
    if existing is not None:
        return existing

    now = utcnow()
    zones = _build_zones(now)
    tiles = _build_tiles(zones, 0, 0, now)
    state = GardenState(
        id=GARDEN_STATE_ID,
        baseline_key=BASELINE_KEY,
        stage_key="neglected_desert",
        total_xp=0,
        current_level=1,
        total_growth_units=0,
        total_decay_points=0,
        active_task_count=0,
        overdue_task_count=0,
        restored_tile_count=0,
        healthy_tile_count=0,
        lush_tile_count=0,
        health_score=0,
        last_recomputed_at=now,
    )
    zone_repo.replace_all(zones)
    tile_repo.replace_all(tiles)
    plant_repo.replace_all([])
    decoration_repo.replace_all([])
    return state_repo.replace(state)


def recompute_garden(
    tasks: TaskRepository,
    activity_events: ActivityEventRepository,
    state_repo: GardenStateRepository,
    zone_repo: GardenZoneRepository,
    tile_repo: GardenTileRepository,
    plant_repo: PlantInstanceRepository,
    decoration_repo: DecorationInstanceRepository,
    xp_repo: XPLedgerRepository,
    unlock_repo: UnlockLedgerRepository,
    decay_repo: DecayEventRepository,
    recovery_repo: RecoveryEventRepository,
) -> GardenRecomputeResult:
    now = utcnow()
    all_tasks = tasks.list_all()
    active_tasks = _active_tasks(all_tasks)
    completed_tasks = _completed_tasks(all_tasks)

    xp_entries, recovery_events, total_recovery_points = _build_xp_entries(completed_tasks)
    total_xp = sum(entry.xp_amount for entry in xp_entries)
    decay_events, total_decay_points = _build_decay_events(active_tasks, now)
    effective_decay_units = 0 if len(active_tasks) == 0 else (total_decay_points + 2) // 3
    zones = _build_zones(now)
    tiles = _build_tiles(zones, total_recovery_points, effective_decay_units, now)
    unlocks = _unlock_entries(total_xp, now)
    plants, decorations = _build_plants_and_decorations(tiles, unlocks)

    restored_tile_count = len([tile for tile in tiles if tile.tile_state != "desert"])
    healthy_tile_count = len([tile for tile in tiles if tile.tile_state in {"healthy", "lush"}])
    lush_tile_count = len([tile for tile in tiles if tile.tile_state == "lush"])
    visible_units = sum(tile.growth_units for tile in tiles)
    health_score = int(round((visible_units / MAX_TILE_UNITS) * 100)) if MAX_TILE_UNITS else 0
    overdue_task_count = len(decay_events)
    state = GardenState(
        id=GARDEN_STATE_ID,
        baseline_key=BASELINE_KEY,
        stage_key=_stage_key(restored_tile_count, healthy_tile_count, lush_tile_count),
        total_xp=total_xp,
        current_level=_level_from_xp(total_xp),
        total_growth_units=total_recovery_points,
        total_decay_points=total_decay_points,
        active_task_count=len(active_tasks),
        overdue_task_count=overdue_task_count,
        restored_tile_count=restored_tile_count,
        healthy_tile_count=healthy_tile_count,
        lush_tile_count=lush_tile_count,
        health_score=health_score,
        last_recomputed_at=now,
    )

    zone_repo.replace_all(zones)
    tile_repo.replace_all(tiles)
    plant_repo.replace_all(plants)
    decoration_repo.replace_all(decorations)
    xp_repo.replace_all(xp_entries)
    unlock_repo.replace_all(unlocks)
    decay_repo.replace_all(decay_events)
    recovery_repo.replace_all(recovery_events)
    saved_state = state_repo.replace(state)

    log_activity(
        activity_events,
        event_type="garden_recomputed",
        entity_type="garden_state",
        entity_id=saved_state.id,
        metadata={
            "total_xp": saved_state.total_xp,
            "stage_key": saved_state.stage_key,
            "overdue_task_count": saved_state.overdue_task_count,
            "restored_tile_count": saved_state.restored_tile_count,
        },
    )

    return GardenRecomputeResult(
        state=saved_state,
        zones=zones,
        tiles=tiles,
        plants=plants,
        decorations=decorations,
        xp_entries=xp_entries,
        unlocks=unlocks,
        decay_events=decay_events,
        recovery_events=recovery_events,
    )


def get_or_create_garden_overview(
    state_repo: GardenStateRepository,
    zone_repo: GardenZoneRepository,
    tile_repo: GardenTileRepository,
    plant_repo: PlantInstanceRepository,
    decoration_repo: DecorationInstanceRepository,
    unlock_repo: UnlockLedgerRepository,
    decay_repo: DecayEventRepository,
    recovery_repo: RecoveryEventRepository,
) -> GardenRecomputeResult:
    state = _ensure_baseline_state(state_repo, zone_repo, tile_repo, plant_repo, decoration_repo)
    return GardenRecomputeResult(
        state=state,
        zones=zone_repo.list_all(),
        tiles=tile_repo.list_all(),
        plants=plant_repo.list_all(),
        decorations=decoration_repo.list_all(),
        xp_entries=[],
        unlocks=unlock_repo.list_all(),
        decay_events=decay_repo.list_all(),
        recovery_events=recovery_repo.list_all(),
    )
