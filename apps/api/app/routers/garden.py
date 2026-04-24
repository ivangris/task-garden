from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Header

from app.db.session import get_db
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyChangeEventRepository,
    SqlAlchemyDecayEventRepository,
    SqlAlchemyDecorationInstanceRepository,
    SqlAlchemyGardenStateRepository,
    SqlAlchemyGardenTileRepository,
    SqlAlchemyGardenZoneRepository,
    SqlAlchemyPlantInstanceRepository,
    SqlAlchemyRecoveryEventRepository,
    SqlAlchemyTaskRepository,
    SqlAlchemyUnlockLedgerRepository,
    SqlAlchemyXPLedgerRepository,
)
from app.schemas.garden import (
    DecayEventResponse,
    DecorationInstanceResponse,
    GardenOverviewResponse,
    GardenStateResponse,
    GardenTileResponse,
    GardenTilesResponse,
    GardenZoneResponse,
    PlantInstanceResponse,
    RecoveryEventResponse,
    UnlockLedgerEntryResponse,
)
from app.services.garden import get_or_create_garden_overview, recompute_garden
from app.services.sync import record_change_event, snapshot_garden_state

router = APIRouter()


def _build_overview_response(overview: object) -> GardenOverviewResponse:
    return GardenOverviewResponse(
        state=GardenStateResponse.model_validate(overview.state),
        zones=[GardenZoneResponse.model_validate(zone) for zone in overview.zones],
        unlocks=[UnlockLedgerEntryResponse.model_validate(item) for item in overview.unlocks],
        recent_decay_events=[DecayEventResponse.model_validate(item) for item in overview.decay_events[-5:]],
        recent_recovery_events=[RecoveryEventResponse.model_validate(item) for item in overview.recovery_events[-5:]],
    )


@router.get("/state", response_model=GardenOverviewResponse)
def get_garden_state(db: Session = Depends(get_db)) -> GardenOverviewResponse:
    overview = get_or_create_garden_overview(
        SqlAlchemyGardenStateRepository(db),
        SqlAlchemyGardenZoneRepository(db),
        SqlAlchemyGardenTileRepository(db),
        SqlAlchemyPlantInstanceRepository(db),
        SqlAlchemyDecorationInstanceRepository(db),
        SqlAlchemyUnlockLedgerRepository(db),
        SqlAlchemyDecayEventRepository(db),
        SqlAlchemyRecoveryEventRepository(db),
    )
    db.commit()
    return _build_overview_response(overview)


@router.get("/tiles", response_model=GardenTilesResponse)
def get_garden_tiles(db: Session = Depends(get_db)) -> GardenTilesResponse:
    overview = get_or_create_garden_overview(
        SqlAlchemyGardenStateRepository(db),
        SqlAlchemyGardenZoneRepository(db),
        SqlAlchemyGardenTileRepository(db),
        SqlAlchemyPlantInstanceRepository(db),
        SqlAlchemyDecorationInstanceRepository(db),
        SqlAlchemyUnlockLedgerRepository(db),
        SqlAlchemyDecayEventRepository(db),
        SqlAlchemyRecoveryEventRepository(db),
    )
    db.commit()
    return GardenTilesResponse(
        state=GardenStateResponse.model_validate(overview.state),
        zones=[GardenZoneResponse.model_validate(zone) for zone in overview.zones],
        tiles=[GardenTileResponse.model_validate(tile) for tile in overview.tiles],
        plants=[PlantInstanceResponse.model_validate(item) for item in overview.plants],
        decorations=[DecorationInstanceResponse.model_validate(item) for item in overview.decorations],
    )


@router.post("/recompute", response_model=GardenOverviewResponse)
def post_recompute_garden(
    db: Session = Depends(get_db),
    device_id: str | None = Header(default=None, alias="X-Task-Garden-Device-Id"),
) -> GardenOverviewResponse:
    overview = recompute_garden(
        SqlAlchemyTaskRepository(db),
        SqlAlchemyActivityEventRepository(db),
        SqlAlchemyGardenStateRepository(db),
        SqlAlchemyGardenZoneRepository(db),
        SqlAlchemyGardenTileRepository(db),
        SqlAlchemyPlantInstanceRepository(db),
        SqlAlchemyDecorationInstanceRepository(db),
        SqlAlchemyXPLedgerRepository(db),
        SqlAlchemyUnlockLedgerRepository(db),
        SqlAlchemyDecayEventRepository(db),
        SqlAlchemyRecoveryEventRepository(db),
    )
    record_change_event(
        SqlAlchemyChangeEventRepository(db),
        entity_type="garden_state",
        entity_id=overview.state.id,
        change_type="recomputed",
        payload=snapshot_garden_state(overview.state),
        device_id=device_id,
        changed_at=overview.state.last_recomputed_at,
    )
    db.commit()
    return _build_overview_response(overview)
