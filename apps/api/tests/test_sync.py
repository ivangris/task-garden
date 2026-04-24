import os
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.main import create_application
from app.repositories.sqlalchemy import SqlAlchemyProjectRepository


FIXED_NOW = datetime(2026, 4, 19, 12, 0, tzinfo=UTC)


class SyncTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "sync-test.db"
        os.environ["TASK_GARDEN_DATABASE_URL"] = f"sqlite:///{self.database_path.as_posix()}"
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        Base.metadata.create_all(get_engine())
        self.client = TestClient(create_application())

    def tearDown(self) -> None:
        self.client.close()
        get_engine().dispose()
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        os.environ.pop("TASK_GARDEN_DATABASE_URL", None)
        self.temp_dir.cleanup()

    def register_device(self, device_id: str = "device-desktop-a") -> dict:
        response = self.client.post(
            "/sync/register-device",
            json={
                "device_id": device_id,
                "device_name": "Desk",
                "platform": "windows",
                "app_version": "0.1.0",
            },
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_device_registration_and_status(self) -> None:
        device = self.register_device()

        status_response = self.client.get("/sync", params={"device_id": device["id"]})
        self.assertEqual(status_response.status_code, 200)
        payload = status_response.json()
        self.assertEqual(payload["provider_name"], "local_only")
        self.assertFalse(payload["sync_enabled"])
        self.assertEqual(payload["registered_device_count"], 1)
        self.assertEqual(payload["current_device"]["id"], device["id"])

    def test_change_event_creation_and_pull_cursor_handling(self) -> None:
        device = self.register_device()
        headers = {"X-Task-Garden-Device-Id": device["id"]}

        task_response = self.client.post(
            "/tasks",
            json={
                "title": "Review sync plan",
                "status": "inbox",
                "priority": "medium",
                "effort": "small",
                "energy": "medium",
            },
            headers=headers,
        )
        self.assertEqual(task_response.status_code, 201)

        first_pull = self.client.get("/sync/pull", params={"device_id": device["id"], "limit": 10})
        self.assertEqual(first_pull.status_code, 200)
        first_payload = first_pull.json()
        self.assertEqual(len(first_payload["items"]), 1)
        self.assertEqual(first_payload["items"][0]["entity_type"], "task")
        self.assertEqual(first_payload["items"][0]["device_id"], device["id"])
        first_cursor = first_payload["next_cursor"]
        self.assertGreater(first_cursor, 0)

        settings_response = self.client.patch(
            "/settings",
            json={"sync_base_url": "http://127.0.0.1:9000"},
            headers=headers,
        )
        self.assertEqual(settings_response.status_code, 200)

        second_pull = self.client.get("/sync/pull", params={"device_id": device["id"], "cursor": first_cursor, "limit": 10})
        self.assertEqual(second_pull.status_code, 200)
        second_payload = second_pull.json()
        self.assertEqual(len(second_payload["items"]), 1)
        self.assertEqual(second_payload["items"][0]["entity_type"], "settings")
        self.assertEqual(second_payload["cursor"], first_cursor)
        self.assertGreater(second_payload["next_cursor"], first_cursor)

    def test_push_contract_applies_project_snapshot(self) -> None:
        self.register_device("device-laptop-b")

        changed_at = FIXED_NOW.isoformat()
        push_response = self.client.post(
            "/sync/push",
            json={
                "device_id": "device-laptop-b",
                "changes": [
                    {
                        "event_id": "11111111-1111-1111-1111-111111111111",
                        "entity_type": "project",
                        "entity_id": "project-remote-1",
                        "change_type": "upserted",
                        "changed_at": changed_at,
                        "device_id": "device-laptop-b",
                        "payload": {
                            "id": "project-remote-1",
                            "name": "Remote Project",
                            "description": "Created on another device",
                            "color_token": "sage",
                            "is_archived": False,
                            "created_at": changed_at,
                            "updated_at": changed_at,
                        },
                    }
                ],
            },
        )
        self.assertEqual(push_response.status_code, 200)
        payload = push_response.json()
        self.assertEqual(payload["accepted_count"], 1)
        self.assertEqual(payload["duplicate_count"], 0)
        self.assertEqual(payload["applied_count"], 1)

        session = get_session_factory()()
        try:
            project = SqlAlchemyProjectRepository(session).get("project-remote-1")
            self.assertIsNotNone(project)
            self.assertEqual(project.name, "Remote Project")
        finally:
            session.close()

    def test_pull_requires_registered_device(self) -> None:
        response = self.client.get("/sync/pull", params={"device_id": "missing-device"})
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
