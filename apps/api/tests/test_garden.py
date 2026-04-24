import os
import tempfile
import unittest
from datetime import timedelta

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.domain.entities import Project, Task
from app.main import create_application
from app.repositories.sqlalchemy import SqlAlchemyProjectRepository, SqlAlchemyTaskRepository
from app.services.common import generate_id, utcnow
from app.services.garden import recompute_garden
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyDecayEventRepository,
    SqlAlchemyDecorationInstanceRepository,
    SqlAlchemyGardenStateRepository,
    SqlAlchemyGardenTileRepository,
    SqlAlchemyGardenZoneRepository,
    SqlAlchemyPlantInstanceRepository,
    SqlAlchemyRecoveryEventRepository,
    SqlAlchemyUnlockLedgerRepository,
    SqlAlchemyXPLedgerRepository,
)


class GardenTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["TASK_GARDEN_DATABASE_URL"] = f"sqlite:///{self.temp_dir.name}/task-garden-garden.db"
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        engine = get_engine()
        Base.metadata.create_all(engine)
        self.client = TestClient(create_application())

    def tearDown(self) -> None:
        self.client.close()
        get_engine().dispose()
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        os.environ.pop("TASK_GARDEN_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def add_task(
        self,
        title: str,
        *,
        status: str = "completed",
        priority: str = "medium",
        effort: str = "medium",
        energy: str = "medium",
        due_days_offset: int | None = None,
        completed_days_ago: int | None = 0,
        created_days_ago: int = 0,
        project_id: str | None = None,
    ) -> Task:
        now = utcnow()
        due_date = now + timedelta(days=due_days_offset) if due_days_offset is not None else None
        completed_at = None if completed_days_ago is None else now - timedelta(days=completed_days_ago)
        updated_at = completed_at or now
        session = get_session_factory()()
        try:
            task = SqlAlchemyTaskRepository(session).add(
                Task(
                    id=generate_id(),
                    title=title,
                    status=status,
                    priority=priority,
                    effort=effort,
                    energy=energy,
                    created_at=now - timedelta(days=created_days_ago),
                    updated_at=updated_at,
                    due_date=due_date,
                    completed_at=completed_at,
                    project_id=project_id,
                )
            )
            session.commit()
            return task
        finally:
            session.close()

    def add_project(self, name: str) -> Project:
        now = utcnow()
        session = get_session_factory()()
        try:
            project = SqlAlchemyProjectRepository(session).add(
                Project(id=generate_id(), name=name, created_at=now, updated_at=now)
            )
            session.commit()
            return project
        finally:
            session.close()

    def recompute(self):
        session = get_session_factory()()
        try:
            result = recompute_garden(
                SqlAlchemyTaskRepository(session),
                SqlAlchemyActivityEventRepository(session),
                SqlAlchemyGardenStateRepository(session),
                SqlAlchemyGardenZoneRepository(session),
                SqlAlchemyGardenTileRepository(session),
                SqlAlchemyPlantInstanceRepository(session),
                SqlAlchemyDecorationInstanceRepository(session),
                SqlAlchemyXPLedgerRepository(session),
                SqlAlchemyUnlockLedgerRepository(session),
                SqlAlchemyDecayEventRepository(session),
                SqlAlchemyRecoveryEventRepository(session),
            )
            session.commit()
            return result
        finally:
            session.close()

    def test_xp_calculation_uses_effort_priority_and_streak(self) -> None:
        self.add_task("Small admin win", effort="small", priority="low", completed_days_ago=2)
        self.add_task("Medium progress step", effort="medium", priority="medium", completed_days_ago=1)
        self.add_task("Large strategic win", effort="large", priority="high", completed_days_ago=0)

        result = self.recompute()

        self.assertEqual(result.state.total_xp, 10 + 27 + 72)
        self.assertEqual(len(result.xp_entries), 3)
        self.assertAlmostEqual(result.xp_entries[-1].streak_multiplier, 1.1)

    def test_unlock_progression_tracks_thresholds(self) -> None:
        self.add_task("Critical launch prep", effort="large", priority="critical", completed_days_ago=1)
        self.add_task("Critical launch follow-through", effort="large", priority="critical", completed_days_ago=0)

        result = self.recompute()
        unlock_keys = [item.unlock_key for item in result.unlocks]

        self.assertIn("starter_seeds", unlock_keys)
        self.assertIn("watering_can", unlock_keys)
        self.assertNotIn("moss_path", unlock_keys)

    def test_decay_calculation_uses_overdue_active_tasks(self) -> None:
        self.add_task(
            "Overdue contract review",
            status="in_progress",
            effort="medium",
            priority="high",
            completed_days_ago=None,
            due_days_offset=-7,
            created_days_ago=10,
        )

        result = self.recompute()

        self.assertEqual(result.state.overdue_task_count, 1)
        self.assertEqual(result.state.total_decay_points, 7)
        self.assertEqual(len(result.decay_events), 1)
        self.assertEqual(result.decay_events[0].days_overdue, 7)

    def test_recovery_stays_possible_when_completed_work_outweighs_decay(self) -> None:
        self.add_task("Ship first draft", effort="large", priority="high", completed_days_ago=0)
        self.add_task(
            "Past-due follow-up",
            status="planned",
            effort="small",
            priority="low",
            completed_days_ago=None,
            due_days_offset=-4,
            created_days_ago=5,
        )

        result = self.recompute()

        self.assertGreater(result.state.total_growth_units, 0)
        self.assertGreater(result.state.restored_tile_count, 0)
        self.assertEqual(result.state.total_decay_points, 3)
        self.assertEqual(result.tiles[0].tile_state, "lush")

    def test_no_decay_when_zero_active_tasks(self) -> None:
        self.add_task("Recovered overdue item", effort="medium", priority="medium", completed_days_ago=0, due_days_offset=-10)

        result = self.recompute()

        self.assertEqual(result.state.active_task_count, 0)
        self.assertEqual(result.state.overdue_task_count, 0)
        self.assertEqual(result.state.total_decay_points, 0)
        self.assertEqual(len(result.decay_events), 0)

    def test_recompute_is_stable_from_same_input_history(self) -> None:
        project = self.add_project("Garden Bench")
        self.add_task("Prep soil notes", effort="small", priority="medium", completed_days_ago=1, project_id=project.id)
        self.add_task("Repair overdue edge", status="blocked", effort="medium", priority="medium", completed_days_ago=None, due_days_offset=-3, created_days_ago=4, project_id=project.id)

        first = self.recompute()
        second = self.recompute()

        self.assertEqual(first.state.total_xp, second.state.total_xp)
        self.assertEqual(first.state.total_decay_points, second.state.total_decay_points)
        self.assertEqual([tile.tile_state for tile in first.tiles], [tile.tile_state for tile in second.tiles])
        self.assertEqual([item.unlock_key for item in first.unlocks], [item.unlock_key for item in second.unlocks])

    def test_garden_routes_return_state_tiles_and_recompute(self) -> None:
        self.add_task("First completed win", effort="medium", priority="high", completed_days_ago=0)

        state_response = self.client.get("/garden/state")
        self.assertEqual(state_response.status_code, 200)
        self.assertEqual(state_response.json()["state"]["baseline_key"], "neglected_desert_plot")

        recompute_response = self.client.post("/garden/recompute")
        self.assertEqual(recompute_response.status_code, 200)
        self.assertGreater(recompute_response.json()["state"]["total_xp"], 0)

        tiles_response = self.client.get("/garden/tiles")
        self.assertEqual(tiles_response.status_code, 200)
        self.assertEqual(len(tiles_response.json()["tiles"]), 12)
