from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GardenStateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    baseline_key: str
    stage_key: str
    total_xp: int
    current_level: int
    total_growth_units: int
    total_decay_points: int
    active_task_count: int
    overdue_task_count: int
    restored_tile_count: int
    healthy_tile_count: int
    lush_tile_count: int
    health_score: int
    last_recomputed_at: datetime


class GardenZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    zone_key: str
    sort_order: int
    tile_count: int
    unlocked_at: datetime | None = None


class GardenTileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    zone_id: str
    tile_index: int
    coord_x: int
    coord_y: int
    tile_state: str
    growth_units: int
    decay_points: int
    last_changed_at: datetime


class PlantInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    garden_tile_id: str
    plant_key: str
    growth_stage: str
    unlocked_at: datetime | None = None


class DecorationInstanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    garden_tile_id: str
    decoration_key: str
    variant_key: str | None = None
    unlocked_at: datetime | None = None


class UnlockLedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    unlock_key: str
    unlock_type: str
    threshold_value: int
    unlocked_at: datetime


class DecayEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    task_title: str
    days_overdue: int
    decay_points: int
    recorded_at: datetime


class RecoveryEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    task_title: str
    recovery_points: int
    xp_amount: int
    recorded_at: datetime


class GardenOverviewResponse(BaseModel):
    state: GardenStateResponse
    zones: list[GardenZoneResponse]
    unlocks: list[UnlockLedgerEntryResponse]
    recent_decay_events: list[DecayEventResponse]
    recent_recovery_events: list[RecoveryEventResponse]


class GardenTilesResponse(BaseModel):
    state: GardenStateResponse
    zones: list[GardenZoneResponse]
    tiles: list[GardenTileResponse]
    plants: list[PlantInstanceResponse]
    decorations: list[DecorationInstanceResponse]
