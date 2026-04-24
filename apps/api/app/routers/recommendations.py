from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyRecommendationSnapshotRepository,
    SqlAlchemyTaskRepository,
)
from app.schemas.recommendations import RecommendationCurrentResponse, RecommendationItemResponse, RecommendationReason
from app.services.recommendations import create_current_recommendations_snapshot

router = APIRouter()


@router.get("/current", response_model=RecommendationCurrentResponse)
def get_current_recommendations(db: Session = Depends(get_db)) -> RecommendationCurrentResponse:
    snapshot = create_current_recommendations_snapshot(
        SqlAlchemyTaskRepository(db),
        SqlAlchemyProjectRepository(db),
        SqlAlchemyActivityEventRepository(db),
        SqlAlchemyRecommendationSnapshotRepository(db),
    )
    db.commit()
    return RecommendationCurrentResponse(
        snapshot_id=snapshot.id,
        generated_at=snapshot.generated_at,
        thresholds={key: int(value) for key, value in snapshot.payload["thresholds"].items()},
        items=[
            RecommendationItemResponse(**{**item, "reasons": [RecommendationReason(**reason) for reason in item.get("reasons", [])]})
            for item in snapshot.payload["items"]
        ],
    )
