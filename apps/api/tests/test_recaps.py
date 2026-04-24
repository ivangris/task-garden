import os
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import httpx
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.domain.entities import Project, Task
from app.main import create_application
from app.repositories.sqlalchemy import SqlAlchemyProjectRepository, SqlAlchemyTaskRepository
from app.schemas.recaps import RecapPeriodResponse
from app.services.recap_narratives import build_recap_narrative_summary, recap_summary_hash
from app.services.common import generate_id
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


FIXED_NOW = datetime(2026, 4, 19, 12, 0, tzinfo=UTC)


class RecapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        os.environ["TASK_GARDEN_DATABASE_URL"] = f"sqlite:///{self.temp_dir.name}/task-garden-recaps.db"
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        Base.metadata.create_all(get_engine())
        self.client = TestClient(create_application())
        self.seed_data()

    def tearDown(self) -> None:
        self.client.close()
        get_engine().dispose()
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        os.environ.pop("TASK_GARDEN_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def add_project(self, name: str) -> Project:
        session = get_session_factory()()
        try:
            project = SqlAlchemyProjectRepository(session).add(
                Project(id=generate_id(), name=name, created_at=FIXED_NOW, updated_at=FIXED_NOW)
            )
            session.commit()
            return project
        finally:
            session.close()

    def add_task(
        self,
        *,
        title: str,
        created_at: datetime,
        completed_at: datetime,
        project_id: str | None,
        effort: str,
        priority: str,
        due_date: datetime | None = None,
    ) -> None:
        session = get_session_factory()()
        try:
            SqlAlchemyTaskRepository(session).add(
                Task(
                    id=generate_id(),
                    title=title,
                    status="completed",
                    priority=priority,
                    effort=effort,
                    energy="medium",
                    project_id=project_id,
                    created_at=created_at,
                    updated_at=completed_at,
                    due_date=due_date,
                    completed_at=completed_at,
                )
            )
            session.commit()
        finally:
            session.close()

    def seed_data(self) -> None:
        atlas = self.add_project("Atlas")
        garden = self.add_project("Garden Bench")
        ops = self.add_project("Ops")

        task_specs = [
            ("Year kickoff plan", datetime(2026, 1, 5, 18, 0, tzinfo=UTC), atlas.id, "large", "high", None),
            ("Close January loop", datetime(2026, 1, 6, 18, 0, tzinfo=UTC), atlas.id, "medium", "medium", None),
            ("Publish January brief", datetime(2026, 1, 7, 18, 0, tzinfo=UTC), ops.id, "large", "critical", None),
            ("February follow-up", datetime(2026, 2, 11, 18, 0, tzinfo=UTC), ops.id, "small", "medium", None),
            ("Repair backlog edge", datetime(2026, 2, 12, 18, 0, tzinfo=UTC), garden.id, "medium", "high", None),
            ("Atlas planning pass", datetime(2026, 4, 14, 18, 0, tzinfo=UTC), atlas.id, "medium", "high", None),
            ("Recover overdue vendor note", datetime(2026, 4, 15, 18, 0, tzinfo=UTC), ops.id, "small", "medium", datetime(2026, 4, 14, 9, 0, tzinfo=UTC)),
            ("Bench restore push", datetime(2026, 4, 16, 18, 0, tzinfo=UTC), garden.id, "large", "high", None),
            ("Atlas review polish", datetime(2026, 4, 17, 18, 0, tzinfo=UTC), atlas.id, "small", "medium", None),
            ("Inbox cleanup sweep", datetime(2026, 4, 18, 18, 0, tzinfo=UTC), None, "small", "low", None),
        ]
        for title, completed_at, project_id, effort, priority, due_date in task_specs:
            self.add_task(
                title=title,
                created_at=completed_at - timedelta(days=1),
                completed_at=completed_at,
                project_id=project_id,
                effort=effort,
                priority=priority,
                due_date=due_date,
            )

        with patch("app.services.garden.utcnow", return_value=FIXED_NOW):
            session = get_session_factory()()
            try:
                recompute_garden(
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
            finally:
                session.close()

    def metric_map(self, recap_payload: dict) -> dict[str, dict]:
        return {item["metric_key"]: item for item in recap_payload["metrics"]}

    def test_weekly_metric_generation(self) -> None:
        with patch("app.services.recaps.utcnow", return_value=FIXED_NOW):
            response = self.client.post("/recaps/generate-weekly")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        metrics = self.metric_map(payload)
        self.assertEqual(payload["period_type"], "weekly")
        self.assertEqual(metrics["total_tasks_completed"]["numeric_value"], 5.0)
        self.assertEqual(metrics["active_days"]["numeric_value"], 5.0)
        self.assertEqual(metrics["overdue_recovered_count"]["numeric_value"], 1.0)
        self.assertEqual(metrics["biggest_completed_task"]["text_value"], "Bench restore push")

    def test_monthly_metric_generation(self) -> None:
        with patch("app.services.recaps.utcnow", return_value=FIXED_NOW):
            response = self.client.post("/recaps/generate-monthly")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        metrics = self.metric_map(payload)
        self.assertEqual(payload["period_label"], "April 2026")
        self.assertEqual(metrics["total_tasks_completed"]["numeric_value"], 5.0)
        self.assertEqual(metrics["xp_gained"]["numeric_value"], 138.0)
        self.assertEqual(metrics["top_projects"]["json_value"]["names"][0], "Atlas")

    def test_yearly_metric_generation(self) -> None:
        with patch("app.services.recaps.utcnow", return_value=FIXED_NOW):
            response = self.client.post("/recaps/generate-yearly")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        metrics = self.metric_map(payload)
        self.assertEqual(payload["period_type"], "yearly")
        self.assertEqual(metrics["total_tasks_completed"]["numeric_value"], 10.0)
        self.assertEqual(metrics["longest_streak_days"]["numeric_value"], 5.0)
        self.assertEqual(metrics["garden_stage_change"]["text_value"], "neglected_desert->lush_oasis")

    def test_milestone_detection_and_highlight_cards(self) -> None:
        with patch("app.services.recaps.utcnow", return_value=FIXED_NOW):
            response = self.client.post("/recaps/generate-yearly")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        milestone_keys = {item["milestone_key"] for item in payload["milestones"]}
        self.assertIn("completed_10", milestone_keys)
        self.assertIn("longest_streak_reached", milestone_keys)
        card_titles = [item["title"] for item in payload["cards"]]
        self.assertIn("Look at all you accomplished", card_titles)
        self.assertIn("Garden transformation", card_titles)

    def test_recap_persistence_and_retrieval(self) -> None:
        with patch("app.services.recaps.utcnow", return_value=FIXED_NOW):
            generated = self.client.post("/recaps/generate-weekly")

        self.assertEqual(generated.status_code, 200)
        period_id = generated.json()["id"]

        recap_response = self.client.get(f"/recaps/{period_id}")
        self.assertEqual(recap_response.status_code, 200)
        self.assertEqual(recap_response.json()["id"], period_id)

        cards_response = self.client.get(f"/recaps/{period_id}/cards")
        self.assertEqual(cards_response.status_code, 200)
        self.assertGreaterEqual(len(cards_response.json()["items"]), 5)

    def test_recap_narrative_summary_builder_is_compact_and_deterministic(self) -> None:
        with patch("app.services.recaps.utcnow", return_value=FIXED_NOW):
            generated = self.client.post("/recaps/generate-yearly")

        recap = RecapPeriodResponse.model_validate(generated.json())
        summary_a = build_recap_narrative_summary(recap)
        summary_b = build_recap_narrative_summary(recap)
        self.assertEqual(summary_a, summary_b)
        self.assertEqual(recap_summary_hash(summary_a), recap_summary_hash(summary_b))
        self.assertIn("headline_metrics", summary_a)
        self.assertLessEqual(len(summary_a["top_projects"]), 3)
        self.assertLessEqual(len(summary_a["highlights"]), 4)
        self.assertLessEqual(len(summary_a["milestones"]), 3)

    def test_mock_narrative_generation_and_persistence(self) -> None:
        with patch("app.services.recaps.utcnow", return_value=FIXED_NOW):
            generated = self.client.post("/recaps/generate-weekly")
        period_id = generated.json()["id"]

        settings_response = self.client.patch("/settings", json={"recap_narrative_provider": "mock"})
        self.assertEqual(settings_response.status_code, 200)

        narrative_response = self.client.post(f"/recaps/{period_id}/generate-narrative")
        self.assertEqual(narrative_response.status_code, 200)
        narrative = narrative_response.json()
        self.assertEqual(narrative["generation_status"], "generated")
        self.assertEqual(narrative["provider_name"], "mock")
        self.assertTrue(narrative["narrative_text"])

        fetched = self.client.get(f"/recaps/{period_id}/narrative")
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.json()["generation_status"], "generated")

    def test_provider_off_persists_disabled_narrative_state(self) -> None:
        with patch("app.services.recaps.utcnow", return_value=FIXED_NOW):
            generated = self.client.post("/recaps/generate-monthly")
        period_id = generated.json()["id"]

        self.client.patch("/settings", json={"recap_narrative_provider": "off"})
        narrative_response = self.client.post(f"/recaps/{period_id}/generate-narrative")
        self.assertEqual(narrative_response.status_code, 200)
        narrative = narrative_response.json()
        self.assertEqual(narrative["generation_status"], "disabled")
        self.assertEqual(narrative["provider_name"], "off")
        self.assertEqual(narrative["error_metadata"]["reason"], "provider_off")

    def test_ollama_failure_does_not_silently_fallback(self) -> None:
        with patch("app.services.recaps.utcnow", return_value=FIXED_NOW):
            generated = self.client.post("/recaps/generate-yearly")
        period_id = generated.json()["id"]

        self.client.patch(
            "/settings",
            json={
                "recap_narrative_provider": "ollama",
                "recap_model": "llama3.1:8b",
                "ollama_base_url": "http://127.0.0.1:11434",
            },
        )

        with patch("app.providers.recap_ollama.httpx.post", side_effect=httpx.ConnectError("connect failed")):
            narrative_response = self.client.post(f"/recaps/{period_id}/generate-narrative")

        self.assertEqual(narrative_response.status_code, 200)
        narrative = narrative_response.json()
        self.assertEqual(narrative["generation_status"], "failed")
        self.assertEqual(narrative["provider_name"], "ollama")
        self.assertEqual(narrative["error_metadata"]["reason"], "provider_unavailable")
        self.assertNotEqual(narrative.get("model_name"), "deterministic-mock-recap")

    def test_recap_metrics_remain_available_when_narrative_generation_fails(self) -> None:
        with patch("app.services.recaps.utcnow", return_value=FIXED_NOW):
            generated = self.client.post("/recaps/generate-weekly")
        period_id = generated.json()["id"]

        self.client.patch(
            "/settings",
            json={
                "recap_narrative_provider": "ollama",
                "recap_model": "llama3.1:8b",
                "ollama_base_url": "http://127.0.0.1:11434",
            },
        )
        with patch(
            "app.providers.recap_ollama.httpx.post",
            side_effect=httpx.TimeoutException("timed out"),
        ):
            self.client.post(f"/recaps/{period_id}/generate-narrative")

        recap_response = self.client.get(f"/recaps/{period_id}")
        self.assertEqual(recap_response.status_code, 200)
        recap = recap_response.json()
        self.assertGreater(len(recap["metrics"]), 0)
        self.assertEqual(recap["narrative"]["generation_status"], "failed")


if __name__ == "__main__":
    unittest.main()
