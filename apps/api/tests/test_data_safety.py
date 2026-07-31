import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.main import create_application


class DataSafetyApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.database_path = self.root / "task-garden.db"
        self.backup_directory = self.root / "backups"
        os.environ["TASK_GARDEN_DATABASE_URL"] = f"sqlite:///{self.database_path.as_posix()}"
        os.environ["TASK_GARDEN_BACKUP_DIRECTORY"] = str(self.backup_directory)
        os.environ["TASK_GARDEN_HOSTED_MODE"] = "false"
        os.environ["TASK_GARDEN_AUTO_CONFIGURE_LOCAL_DEFAULTS"] = "false"
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
        for key in (
            "TASK_GARDEN_DATABASE_URL",
            "TASK_GARDEN_BACKUP_DIRECTORY",
            "TASK_GARDEN_HOSTED_MODE",
            "TASK_GARDEN_SINGLE_USER_AUTH_TOKEN",
            "TASK_GARDEN_AUTO_CONFIGURE_LOCAL_DEFAULTS",
        ):
            os.environ.pop(key, None)
        self.temp_dir.cleanup()

    def create_task(self, title: str) -> dict[str, object]:
        response = self.client.post(
            "/tasks",
            json={
                "title": title,
                "status": "inbox",
                "priority": "medium",
                "effort": "small",
                "energy": "medium",
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_backup_and_restore_recover_the_selected_snapshot(self) -> None:
        original_task = self.create_task("Preserve this task")

        backup_response = self.client.post("/data-safety/backups")
        self.assertEqual(backup_response.status_code, 201)
        backup = backup_response.json()
        self.assertEqual(backup["backup_type"], "manual")
        self.assertEqual(backup["integrity_status"], "ok")
        self.assertTrue((self.backup_directory / backup["name"]).is_file())

        self.create_task("Remove this later task")
        self.assertEqual(len(self.client.get("/tasks").json()["items"]), 2)

        restore_response = self.client.post(
            "/data-safety/restore",
            json={"backup_name": backup["name"], "confirmation": "RESTORE"},
        )
        self.assertEqual(restore_response.status_code, 200)
        restore = restore_response.json()
        self.assertEqual(restore["restored_from"]["name"], backup["name"])
        self.assertEqual(restore["safety_backup"]["backup_type"], "pre_restore")
        safety_backup_path = self.backup_directory / restore["safety_backup"]["name"]
        connection = sqlite3.connect(safety_backup_path)
        try:
            safety_titles = [row[0] for row in connection.execute("SELECT title FROM tasks ORDER BY title")]
        finally:
            connection.close()
        self.assertIn("Remove this later task", safety_titles)

        restored_tasks = self.client.get("/tasks").json()["items"]
        self.assertEqual([task["id"] for task in restored_tasks], [original_task["id"]])

        status_response = self.client.get("/data-safety")
        self.assertEqual(status_response.status_code, 200)
        status_payload = status_response.json()
        self.assertTrue(status_payload["available"])
        self.assertEqual(len(status_payload["backups"]), 2)

    def test_restore_rejects_paths_and_requires_confirmation(self) -> None:
        traversal_response = self.client.post(
            "/data-safety/restore",
            json={"backup_name": "../outside.db", "confirmation": "RESTORE"},
        )
        self.assertEqual(traversal_response.status_code, 422)

        confirmation_response = self.client.post(
            "/data-safety/restore",
            json={"backup_name": "task-garden-manual-20260730-000000-000000.db", "confirmation": "restore"},
        )
        self.assertEqual(confirmation_response.status_code, 422)

    def test_invalid_sqlite_backup_is_visible_but_cannot_be_restored(self) -> None:
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        invalid_backup = self.backup_directory / "task-garden-manual-invalid.db"
        invalid_backup.write_text("not a sqlite database", encoding="utf-8")

        status_response = self.client.get("/data-safety")
        invalid_record = next(
            backup for backup in status_response.json()["backups"] if backup["name"] == invalid_backup.name
        )
        self.assertEqual(invalid_record["integrity_status"], "invalid")

        restore_response = self.client.post(
            "/data-safety/restore",
            json={"backup_name": invalid_backup.name, "confirmation": "RESTORE"},
        )
        self.assertEqual(restore_response.status_code, 422)

    def test_hosted_mode_reports_local_backup_as_unavailable(self) -> None:
        self.client.close()
        os.environ["TASK_GARDEN_HOSTED_MODE"] = "true"
        os.environ["TASK_GARDEN_SINGLE_USER_AUTH_TOKEN"] = "test-hosted-token"
        get_settings.cache_clear()
        self.client = TestClient(create_application())

        status_response = self.client.get("/data-safety")
        self.assertEqual(status_response.status_code, 200)
        self.assertFalse(status_response.json()["available"])
        self.assertIn("hosted mode", status_response.json()["reason"])

        create_response = self.client.post(
            "/data-safety/backups",
            headers={"Authorization": "Bearer test-hosted-token"},
        )
        self.assertEqual(create_response.status_code, 409)
