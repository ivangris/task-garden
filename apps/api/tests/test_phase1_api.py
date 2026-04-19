import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.main import create_application
from app.repositories.sqlalchemy import SqlAlchemyActivityEventRepository


class Phase1ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        os.environ["TASK_GARDEN_DATABASE_URL"] = f"sqlite:///{self.database_path.as_posix()}"
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

    def test_entry_creation_persists_and_logs_activity(self) -> None:
        create_response = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Plan the next sprint"})
        self.assertEqual(create_response.status_code, 201)
        entry = create_response.json()

        fetch_response = self.client.get(f"/entries/{entry['id']}")
        self.assertEqual(fetch_response.status_code, 200)
        self.assertEqual(fetch_response.json()["raw_text"], "Plan the next sprint")

        list_response = self.client.get("/entries")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["items"]), 1)

        session = get_session_factory()()
        try:
            events = SqlAlchemyActivityEventRepository(session).list_recent()
            self.assertEqual(events[0].event_type, "raw_entry_created")
            self.assertEqual(events[0].entity_type, "raw_entry")
        finally:
            session.close()

    def test_task_lifecycle_routes_and_activity_logging(self) -> None:
        project_response = self.client.post("/projects", json={"name": "Desk reset"})
        self.assertEqual(project_response.status_code, 201)
        project_id = project_response.json()["id"]

        create_response = self.client.post(
            "/tasks",
            json={
                "title": "Clear the inbox",
                "project_id": project_id,
                "status": "inbox",
                "priority": "high",
                "effort": "small",
                "energy": "medium",
            },
        )
        self.assertEqual(create_response.status_code, 201)
        task_id = create_response.json()["id"]

        patch_response = self.client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["status"], "in_progress")

        complete_response = self.client.post(f"/tasks/{task_id}/complete")
        self.assertEqual(complete_response.status_code, 200)
        self.assertEqual(complete_response.json()["status"], "completed")

        reopen_response = self.client.post(f"/tasks/{task_id}/reopen")
        self.assertEqual(reopen_response.status_code, 200)
        self.assertEqual(reopen_response.json()["status"], "inbox")

        session = get_session_factory()()
        try:
            event_types = [event.event_type for event in SqlAlchemyActivityEventRepository(session).list_recent(limit=10)]
            self.assertIn("project_created", event_types)
            self.assertIn("task_created", event_types)
            self.assertIn("task_updated", event_types)
            self.assertIn("task_completed", event_types)
            self.assertIn("task_reopened", event_types)
        finally:
            session.close()

    def test_settings_patch_persists(self) -> None:
        patch_response = self.client.patch(
            "/settings",
            json={
                "local_only_mode": True,
                "cloud_enabled": False,
                "stt_model": "whisper-test",
                "extraction_model": "local-extractor-test",
            },
        )
        self.assertEqual(patch_response.status_code, 200)

        get_response = self.client.get("/settings")
        self.assertEqual(get_response.status_code, 200)
        payload = get_response.json()
        self.assertEqual(payload["stt_model"], "whisper-test")
        self.assertEqual(payload["extraction_model"], "local-extractor-test")


if __name__ == "__main__":
    unittest.main()
