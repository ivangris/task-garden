from dataclasses import asdict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyRecommendationSnapshotRepository,
    SqlAlchemyTaskRepository,
)
from app.schemas.recommendations import RecommendationItemResponse, RecommendationReason, WeeklyPreviewResponse
from app.schemas.tasks import TaskResponse
from app.services.recommendations import create_weekly_preview_snapshot

router = APIRouter()


def _task_response(task: object, project_names: dict[str, str]) -> TaskResponse:
    payload = TaskResponse.model_validate(task)
    project_id = getattr(task, "project_id", None)
    return payload.model_copy(update={"project_name": project_names.get(project_id or "")})


@router.post("/weekly-preview", response_model=WeeklyPreviewResponse)
def post_weekly_preview(db: Session = Depends(get_db)) -> WeeklyPreviewResponse:
    project_repo = SqlAlchemyProjectRepository(db)
    snapshot, result = create_weekly_preview_snapshot(
        SqlAlchemyTaskRepository(db),
        project_repo,
        SqlAlchemyActivityEventRepository(db),
        SqlAlchemyRecommendationSnapshotRepository(db),
    )
    db.commit()
    project_names = {project.id: project.name for project in project_repo.list_all()}
    return WeeklyPreviewResponse(
        snapshot_id=snapshot.id,
        generated_at=result.generated_at,
        window_start=result.window_start,
        window_end=result.window_end,
        top_focus_items=[_task_response(task, project_names) for task in result.top_focus_items],
        warnings=[
            RecommendationItemResponse(
                **{**asdict(item), "reasons": [RecommendationReason(**asdict(reason)) for reason in item.reasons]},
            )
            for item in result.warnings
        ],
        suggestion_summaries=result.suggestion_summaries,
        thresholds=result.thresholds,
    )
