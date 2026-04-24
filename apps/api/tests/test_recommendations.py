import os
import tempfile
import unittest
from datetime import timedelta

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.domain.entities import ActivityEvent, Project, Task
from app.main import create_application
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyProjectRepository,
    SqlAlchemyRecommendationSnapshotRepository,
    SqlAlchemyTaskRepository,
)
from app.services.common import generate_id, utcnow
from app.services.recommendations import create_current_recommendations_snapshot


class RecommendationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["TASK_GARDEN_DATABASE_URL"] = f"sqlite:///{self.temp_dir.name}/task-garden-test.db"
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

    def add_project(self, name: str, *, created_at=None) -> Project:
        now = created_at or utcnow()
        session = get_session_factory()()
        try:
            project = SqlAlchemyProjectRepository(session).add(
                Project(id=generate_id(), name=name, created_at=now, updated_at=now)
            )
            session.commit()
            return project
        finally:
            session.close()

    def add_task(
        self,
        title: str,
        *,
        status: str = "inbox",
        priority: str = "medium",
        effort: str = "medium",
        energy: str = "medium",
        created_days_ago: int = 0,
        updated_days_ago: int | None = None,
        due_in_days: int | None = None,
        project_id: str | None = None,
        completed_days_ago: int | None = None,
    ) -> Task:
        now = utcnow()
        created_at = now - timedelta(days=created_days_ago)
        updated_at = now - timedelta(days=updated_days_ago if updated_days_ago is not None else created_days_ago)
        due_date = now + timedelta(days=due_in_days) if due_in_days is not None else None
        completed_at = now - timedelta(days=completed_days_ago) if completed_days_ago is not None else None
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
                    created_at=created_at,
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

    def add_task_activity(self, task_id: str, *, event_type: str, days_ago: int) -> None:
        created_at = utcnow() - timedelta(days=days_ago)
        session = get_session_factory()()
        try:
            SqlAlchemyActivityEventRepository(session).add(
                ActivityEvent(
                    id=generate_id(),
                    event_type=event_type,
                    entity_type="task",
                    entity_id=task_id,
                    metadata={},
                    created_at=created_at,
                )
            )
            session.commit()
        finally:
            session.close()

    def current_snapshot(self):
        session = get_session_factory()()
        try:
            snapshot = create_current_recommendations_snapshot(
                SqlAlchemyTaskRepository(session),
                SqlAlchemyProjectRepository(session),
                SqlAlchemyActivityEventRepository(session),
                SqlAlchemyRecommendationSnapshotRepository(session),
            )
            session.commit()
            return snapshot
        finally:
            session.close()

    def test_stale_task_rule_detects_untouched_active_task(self) -> None:
        task = self.add_task("Follow up on vendor reply", updated_days_ago=10)
        self.add_task_activity(task.id, event_type="task_updated", days_ago=9)

        snapshot = self.current_snapshot()
        stale_items = [item for item in snapshot.payload["items"] if item["rule_type"] == "stale_task"]

        self.assertEqual(len(stale_items), 1)
        self.assertEqual(stale_items[0]["task_id"], task.id)
        self.assertIn("days_since_touch", stale_items[0]["metadata"])

    def test_overloaded_week_rule_detects_heavy_due_load(self) -> None:
        for index in range(5):
            self.add_task(
                f"Week load {index}",
                effort="large" if index % 2 == 0 else "medium",
                priority="high",
                due_in_days=index,
            )

        snapshot = self.current_snapshot()
        rules = {item["rule_type"] for item in snapshot.payload["items"]}
        self.assertIn("overloaded_week", rules)

    def test_neglected_project_rule_detects_quiet_project_with_active_work(self) -> None:
        project = self.add_project("Atlas")
        self.add_task("Old completion", status="completed", project_id=project.id, created_days_ago=25, completed_days_ago=20)
        self.add_task("Atlas next step", project_id=project.id, created_days_ago=12, updated_days_ago=12)

        snapshot = self.current_snapshot()
        neglected = [item for item in snapshot.payload["items"] if item["rule_type"] == "neglected_project"]
        self.assertEqual(len(neglected), 1)
        self.assertEqual(neglected[0]["project_id"], project.id)

    def test_large_task_breakdown_rule_detects_stale_large_task(self) -> None:
        task = self.add_task("Plan migration rollout", effort="large", updated_days_ago=6)

        snapshot = self.current_snapshot()
        breakdown = [item for item in snapshot.payload["items"] if item["rule_type"] == "large_task_breakdown"]
        self.assertEqual(len(breakdown), 1)
        self.assertEqual(breakdown[0]["task_id"], task.id)

    def test_small_wins_rule_suggests_small_tasks_when_backlog_is_heavy(self) -> None:
        for index in range(9):
            self.add_task(f"Large backlog {index}", effort="large", priority="medium", created_days_ago=2)
        for index in range(3):
            self.add_task(f"Small win {index}", effort="small", priority="high", due_in_days=index)

        snapshot = self.current_snapshot()
        small_wins = [item for item in snapshot.payload["items"] if item["rule_type"] == "small_wins"]
        self.assertEqual(len(small_wins), 1)
        suggested = small_wins[0]["metadata"]["suggested_titles"]
        self.assertEqual(len(suggested), 3)
        self.assertIn("Small win 0", suggested)

    def test_get_current_recommendations_persists_snapshot(self) -> None:
        self.add_task("Stale planning follow-up", updated_days_ago=8)

        response = self.client.get("/recommendations/current")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["snapshot_id"])
        self.assertGreaterEqual(len(payload["items"]), 1)

        session = get_session_factory()()
        try:
            snapshots = SqlAlchemyRecommendationSnapshotRepository(session).list_recent("current_recommendations", limit=5)
            self.assertEqual(len(snapshots), 1)
            self.assertEqual(snapshots[0].id, payload["snapshot_id"])
        finally:
            session.close()

    def test_weekly_preview_returns_focus_warnings_and_persists_snapshot(self) -> None:
        project = self.add_project("Operations")
        due_soon = self.add_task("Finish weekly budget pass", project_id=project.id, priority="critical", effort="large", due_in_days=1)
        self.add_task("Update operations checklist", project_id=project.id, due_in_days=2, effort="medium")
        self.add_task("Book contractor follow-up", project_id=project.id, effort="small", due_in_days=0)
        for index in range(3):
            self.add_task(f"Extra load {index}", project_id=project.id, effort="medium", priority="high", due_in_days=index + 3)

        response = self.client.post("/planning/weekly-preview")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["top_focus_items"][0]["id"], due_soon.id)
        self.assertGreaterEqual(len(payload["warnings"]), 1)
        self.assertGreaterEqual(len(payload["suggestion_summaries"]), 1)

        session = get_session_factory()()
        try:
            snapshots = SqlAlchemyRecommendationSnapshotRepository(session).list_recent("weekly_preview", limit=5)
            self.assertEqual(len(snapshots), 1)
            self.assertEqual(snapshots[0].id, payload["snapshot_id"])
        finally:
            session.close()
