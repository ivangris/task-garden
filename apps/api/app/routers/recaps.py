from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends

from app.db.session import get_db
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyHighlightCardRepository,
    SqlAlchemyMilestoneRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyProjectSummaryRepository,
    SqlAlchemyRecapMetricSnapshotRepository,
    SqlAlchemyRecapNarrativeRepository,
    SqlAlchemyRecapPeriodRepository,
    SqlAlchemyRecoveryEventRepository,
    SqlAlchemyStreakSummaryRepository,
    SqlAlchemyTaskRepository,
    SqlAlchemyUnlockLedgerRepository,
    SqlAlchemyXPLedgerRepository,
)
from app.config import get_settings
from app.repositories.sqlalchemy import SqlAlchemySettingsRepository
from app.schemas.recaps import HighlightCardListResponse, RecapNarrativeResponse, RecapPeriodResponse
from app.services.recap_narratives import generate_recap_narrative, get_recap_narrative
from app.services.recaps import generate_recap, get_recap
from app.services.settings import get_settings_payload

router = APIRouter()


def _recap_repositories(db: Session) -> tuple[
    SqlAlchemyRecapPeriodRepository,
    SqlAlchemyRecapMetricSnapshotRepository,
    SqlAlchemyHighlightCardRepository,
    SqlAlchemyMilestoneRepository,
    SqlAlchemyStreakSummaryRepository,
    SqlAlchemyProjectSummaryRepository,
    SqlAlchemyRecapNarrativeRepository,
]:
    return (
        SqlAlchemyRecapPeriodRepository(db),
        SqlAlchemyRecapMetricSnapshotRepository(db),
        SqlAlchemyHighlightCardRepository(db),
        SqlAlchemyMilestoneRepository(db),
        SqlAlchemyStreakSummaryRepository(db),
        SqlAlchemyProjectSummaryRepository(db),
        SqlAlchemyRecapNarrativeRepository(db),
    )


@router.post("/generate-weekly", response_model=RecapPeriodResponse)
def post_generate_weekly_recap(db: Session = Depends(get_db)) -> RecapPeriodResponse:
    period_repo, metric_repo, card_repo, milestone_repo, streak_repo, project_summary_repo, _ = _recap_repositories(db)
    result = generate_recap(
        "weekly",
        period_repo,
        metric_repo,
        card_repo,
        milestone_repo,
        streak_repo,
        project_summary_repo,
        SqlAlchemyTaskRepository(db),
        SqlAlchemyProjectRepository(db),
        SqlAlchemyActivityEventRepository(db),
        SqlAlchemyXPLedgerRepository(db),
        SqlAlchemyUnlockLedgerRepository(db),
        SqlAlchemyRecoveryEventRepository(db),
    )
    db.commit()
    return result


@router.post("/generate-monthly", response_model=RecapPeriodResponse)
def post_generate_monthly_recap(db: Session = Depends(get_db)) -> RecapPeriodResponse:
    period_repo, metric_repo, card_repo, milestone_repo, streak_repo, project_summary_repo, _ = _recap_repositories(db)
    result = generate_recap(
        "monthly",
        period_repo,
        metric_repo,
        card_repo,
        milestone_repo,
        streak_repo,
        project_summary_repo,
        SqlAlchemyTaskRepository(db),
        SqlAlchemyProjectRepository(db),
        SqlAlchemyActivityEventRepository(db),
        SqlAlchemyXPLedgerRepository(db),
        SqlAlchemyUnlockLedgerRepository(db),
        SqlAlchemyRecoveryEventRepository(db),
    )
    db.commit()
    return result


@router.post("/generate-yearly", response_model=RecapPeriodResponse)
def post_generate_yearly_recap(db: Session = Depends(get_db)) -> RecapPeriodResponse:
    period_repo, metric_repo, card_repo, milestone_repo, streak_repo, project_summary_repo, _ = _recap_repositories(db)
    result = generate_recap(
        "yearly",
        period_repo,
        metric_repo,
        card_repo,
        milestone_repo,
        streak_repo,
        project_summary_repo,
        SqlAlchemyTaskRepository(db),
        SqlAlchemyProjectRepository(db),
        SqlAlchemyActivityEventRepository(db),
        SqlAlchemyXPLedgerRepository(db),
        SqlAlchemyUnlockLedgerRepository(db),
        SqlAlchemyRecoveryEventRepository(db),
    )
    db.commit()
    return result


@router.get("/{period_id}", response_model=RecapPeriodResponse)
def get_recap_period(period_id: str, db: Session = Depends(get_db)) -> RecapPeriodResponse:
    period_repo, metric_repo, card_repo, milestone_repo, streak_repo, project_summary_repo, narrative_repo = _recap_repositories(db)
    return get_recap(
        period_id,
        period_repo,
        metric_repo,
        card_repo,
        milestone_repo,
        streak_repo,
        project_summary_repo,
        narrative_repo.get_for_period(period_id),
    )


@router.get("/{period_id}/cards", response_model=HighlightCardListResponse)
def get_recap_cards(period_id: str, db: Session = Depends(get_db)) -> HighlightCardListResponse:
    period_repo, metric_repo, card_repo, milestone_repo, streak_repo, project_summary_repo, narrative_repo = _recap_repositories(db)
    recap = get_recap(
        period_id,
        period_repo,
        metric_repo,
        card_repo,
        milestone_repo,
        streak_repo,
        project_summary_repo,
        narrative_repo.get_for_period(period_id),
    )
    return HighlightCardListResponse(items=recap.cards)


@router.post("/{period_id}/generate-narrative", response_model=RecapNarrativeResponse)
def post_generate_recap_narrative(period_id: str, db: Session = Depends(get_db)) -> RecapNarrativeResponse:
    period_repo, metric_repo, card_repo, milestone_repo, streak_repo, project_summary_repo, narrative_repo = _recap_repositories(db)
    recap = get_recap(
        period_id,
        period_repo,
        metric_repo,
        card_repo,
        milestone_repo,
        streak_repo,
        project_summary_repo,
        narrative_repo.get_for_period(period_id),
    )
    defaults = get_settings()
    effective_settings = defaults.model_copy(
        update=get_settings_payload(SqlAlchemySettingsRepository(db), defaults).model_dump()
    )
    result = generate_recap_narrative(recap, narrative_repo, effective_settings)
    db.commit()
    return result


@router.get("/{period_id}/narrative", response_model=RecapNarrativeResponse)
def get_recap_period_narrative(period_id: str, db: Session = Depends(get_db)) -> RecapNarrativeResponse:
    return get_recap_narrative(period_id, SqlAlchemyRecapNarrativeRepository(db))
