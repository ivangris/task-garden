from fastapi import APIRouter

from app.routers import (
    entries,
    entry_extractions,
    extractions,
    garden,
    health,
    planning,
    projects,
    recommendations,
    recaps,
    settings,
    sync,
    tasks,
)

router = APIRouter()
router.include_router(health.router, tags=["health"])
router.include_router(settings.router, prefix="/settings", tags=["settings"])
router.include_router(entries.router, prefix="/entries", tags=["entries"])
router.include_router(entry_extractions.router, prefix="/entries", tags=["entries"])
router.include_router(extractions.router, prefix="/extractions", tags=["extractions"])
router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])
router.include_router(recommendations.router, prefix="/recommendations", tags=["recommendations"])
router.include_router(planning.router, prefix="/planning", tags=["planning"])
router.include_router(garden.router, prefix="/garden", tags=["garden"])
router.include_router(recaps.router, prefix="/recaps", tags=["recaps"])
router.include_router(sync.router, prefix="/sync", tags=["sync"])
