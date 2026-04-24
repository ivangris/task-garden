import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import importlib.util
import sys

from fastapi.testclient import TestClient
import httpx

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_engine, get_session_factory
from app.main import create_application
from app.providers.ollama_common import build_ollama_chat_url, normalize_ollama_base_url
from app.providers.local_stt import WhisperCppSTTProvider
from app.services.local_models import LocalModel
from app.repositories.sqlalchemy import (
    SqlAlchemyActivityEventRepository,
    SqlAlchemyExtractedTaskCandidateRepository,
    SqlAlchemyExtractionBatchRepository,
    SqlAlchemyRawEntryRepository,
    SqlAlchemySettingsRepository,
    SqlAlchemyTaskRepository,
    SqlAlchemyTranscriptSegmentRepository,
)

EVAL_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "eval_extraction_samples.py"
EVAL_SPEC = importlib.util.spec_from_file_location("eval_extraction_samples", EVAL_SCRIPT_PATH)
assert EVAL_SPEC and EVAL_SPEC.loader
eval_extraction_samples = importlib.util.module_from_spec(EVAL_SPEC)
sys.modules[EVAL_SPEC.name] = eval_extraction_samples
EVAL_SPEC.loader.exec_module(eval_extraction_samples)


class Phase1ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database_path = Path(self.temp_dir.name) / "test.db"
        os.environ["TASK_GARDEN_DATABASE_URL"] = f"sqlite:///{self.database_path.as_posix()}"
        os.environ["TASK_GARDEN_TASK_EXTRACTION_PROVIDER"] = "mock"
        os.environ["TASK_GARDEN_RECAP_NARRATIVE_PROVIDER"] = "mock"
        os.environ["TASK_GARDEN_STT_PROVIDER"] = "local_stub"
        os.environ["TASK_GARDEN_AUTO_CONFIGURE_LOCAL_DEFAULTS"] = "false"
        get_settings.cache_clear()
        get_engine.cache_clear()
        get_session_factory.cache_clear()
        engine = get_engine()
        Base.metadata.create_all(engine)
        self.client = TestClient(create_application())

    def rebuild_client(self) -> None:
        self.client.close()
        get_engine().dispose()
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
        os.environ.pop("TASK_GARDEN_STT_PROVIDER", None)
        os.environ.pop("TASK_GARDEN_STT_EXECUTABLE_PATH", None)
        os.environ.pop("TASK_GARDEN_STT_MODEL_PATH", None)
        os.environ.pop("TASK_GARDEN_TASK_EXTRACTION_PROVIDER", None)
        os.environ.pop("TASK_GARDEN_OLLAMA_BASE_URL", None)
        os.environ.pop("TASK_GARDEN_EXTRACTION_MODEL", None)
        os.environ.pop("TASK_GARDEN_AUTO_CONFIGURE_LOCAL_DEFAULTS", None)
        self.temp_dir.cleanup()

    def make_ollama_response(self, content: str, *, model: str = "llama3.1:8b", status_code: int = 200) -> httpx.Response:
        request = httpx.Request("POST", "http://127.0.0.1:11434/api/chat")
        return httpx.Response(
            status_code=status_code,
            request=request,
            json={
                "model": model,
                "message": {"role": "assistant", "content": content},
                "done": True,
                "done_reason": "stop",
                "eval_count": 123,
                "total_duration": 456,
            },
        )

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

    def test_archived_entry_is_removed_from_recent_entries(self) -> None:
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Temporary note"}).json()

        archive_response = self.client.delete(f"/entries/{entry['id']}")
        self.assertEqual(archive_response.status_code, 200)
        self.assertEqual(archive_response.json()["entry_status"], "archived")

        list_response = self.client.get("/entries")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.json()["items"], [])

        fetch_response = self.client.get(f"/entries/{entry['id']}")
        self.assertEqual(fetch_response.status_code, 200)
        self.assertEqual(fetch_response.json()["entry_status"], "archived")

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

    def test_settings_defaults_select_installed_ollama_chat_model(self) -> None:
        os.environ.pop("TASK_GARDEN_TASK_EXTRACTION_PROVIDER", None)
        os.environ.pop("TASK_GARDEN_RECAP_NARRATIVE_PROVIDER", None)
        os.environ.pop("TASK_GARDEN_STT_PROVIDER", None)
        os.environ["TASK_GARDEN_AUTO_CONFIGURE_LOCAL_DEFAULTS"] = "true"
        self.rebuild_client()
        with patch(
            "app.services.settings.discover_ollama_models",
            return_value=[
                LocalModel(name="nomic-embed-text:latest", usable_for_chat=False),
                LocalModel(name="gemma3:4b", usable_for_chat=True),
            ],
        ), patch("app.services.settings.resolve_whisper_cpp_paths", return_value=(None, None)), patch(
            "app.services.local_models.resolve_whisper_cpp_paths",
            return_value=(None, None),
        ):
            response = self.client.get("/settings")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["task_extraction_provider"], "ollama")
        self.assertEqual(payload["recap_narrative_provider"], "ollama")
        self.assertEqual(payload["extraction_model"], "gemma3:4b")
        self.assertEqual(payload["recap_model"], "gemma3:4b")
        self.assertNotEqual(payload["extraction_model"], "llama3.1:8b")
        self.assertEqual(payload["stt_provider"], "whisper_cpp")
        self.assertFalse(payload["stt_ready"])

    def test_stt_readiness_reports_missing_real_transcription_setup(self) -> None:
        check_response = self.client.post("/settings/providers/check", json={"kind": "stt"})

        self.assertEqual(check_response.status_code, 200)
        payload = check_response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["details"]["reason"], "testing_mode")

    def test_extraction_batch_and_candidates_are_persisted(self) -> None:
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Email Sam and draft project plan for Atlas tomorrow"}).json()

        extract_response = self.client.post(f"/entries/{entry['id']}/extract")
        self.assertEqual(extract_response.status_code, 201)
        extraction = extract_response.json()
        self.assertEqual(extraction["provider_name"], "mock")
        self.assertGreaterEqual(len(extraction["candidates"]), 1)

        fetch_response = self.client.get(f"/extractions/{extraction['id']}")
        self.assertEqual(fetch_response.status_code, 200)
        self.assertEqual(fetch_response.json()["id"], extraction["id"])

        session = get_session_factory()()
        try:
          batches = SqlAlchemyExtractionBatchRepository(session).list_for_entry(entry["id"])
          candidates = SqlAlchemyExtractedTaskCandidateRepository(session).list_for_extraction(extraction["id"])
          events = [event.event_type for event in SqlAlchemyActivityEventRepository(session).list_recent(limit=10)]
          self.assertEqual(len(batches), 1)
          self.assertEqual(len(candidates), len(extraction["candidates"]))
          self.assertIn("extraction_completed", events)
        finally:
          session.close()

    def test_confirm_flow_creates_tasks_only_for_accepted_candidates_and_persists_edits(self) -> None:
        entry = self.client.post(
            "/entries",
            json={"source_type": "typed", "raw_text": "Draft roadmap for Atlas and email vendor tomorrow"},
        ).json()
        extraction = self.client.post(f"/entries/{entry['id']}/extract").json()
        first, second = extraction["candidates"][:2]

        confirm_response = self.client.post(
            f"/extractions/{extraction['id']}/confirm",
            json={
                "candidates": [
                    {
                        "id": first["id"],
                        "decision": "accepted",
                        "title": "Draft Atlas roadmap v1",
                        "details": "Edited before confirmation",
                        "project_or_group": "Atlas",
                        "priority": first["priority"],
                        "effort": first["effort"],
                        "energy": first["energy"],
                        "labels": ["planning"],
                        "due_date": first["due_date"],
                        "parent_task_title": first["parent_task_title"],
                        "confidence": first["confidence"],
                        "source_excerpt": first["source_excerpt"],
                    },
                    {
                        "id": second["id"],
                        "decision": "rejected",
                        "title": second["title"],
                        "details": second["details"],
                        "project_or_group": second["project_or_group"],
                        "priority": second["priority"],
                        "effort": second["effort"],
                        "energy": second["energy"],
                        "labels": second["labels"],
                        "due_date": second["due_date"],
                        "parent_task_title": second["parent_task_title"],
                        "confidence": second["confidence"],
                        "source_excerpt": second["source_excerpt"],
                    },
                ]
            },
        )
        self.assertEqual(confirm_response.status_code, 200)
        payload = confirm_response.json()
        self.assertEqual(payload["accepted_count"], 1)
        self.assertEqual(payload["rejected_count"], 1)
        self.assertEqual(len(payload["created_task_ids"]), 1)

        session = get_session_factory()()
        try:
            tasks = SqlAlchemyTaskRepository(session).list_all()
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].title, "Draft Atlas roadmap v1")
            self.assertEqual(tasks[0].source_extraction_batch_id, extraction["id"])

            updated_candidates = SqlAlchemyExtractedTaskCandidateRepository(session).list_for_extraction(extraction["id"])
            status_by_id = {candidate.id: candidate.candidate_status for candidate in updated_candidates}
            self.assertEqual(status_by_id[first["id"]], "edited")
            self.assertEqual(status_by_id[second["id"]], "rejected")

            event_types = [event.event_type for event in SqlAlchemyActivityEventRepository(session).list_recent(limit=20)]
            self.assertIn("task_confirmed", event_types)
            self.assertIn("task_confirmed_from_extraction", event_types)
            self.assertIn("task_rejected", event_types)
        finally:
            session.close()

    def test_confirm_validation_rejects_partial_review(self) -> None:
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Call bank and update project notes"}).json()
        extraction = self.client.post(f"/entries/{entry['id']}/extract").json()
        first = extraction["candidates"][0]

        confirm_response = self.client.post(
            f"/extractions/{extraction['id']}/confirm",
            json={
                "candidates": [
                    {
                        "id": first["id"],
                        "decision": "accepted",
                        "title": first["title"],
                        "details": first["details"],
                        "project_or_group": first["project_or_group"],
                        "priority": first["priority"],
                        "effort": first["effort"],
                        "energy": first["energy"],
                        "labels": first["labels"],
                        "due_date": first["due_date"],
                        "parent_task_title": first["parent_task_title"],
                        "confidence": first["confidence"],
                        "source_excerpt": first["source_excerpt"],
                    }
                ]
            },
        )
        self.assertEqual(confirm_response.status_code, 400)

    def test_transcription_route_persists_transcript_and_segments(self) -> None:
        entry_response = self.client.post("/entries/audio", json={})
        self.assertEqual(entry_response.status_code, 201)
        entry = entry_response.json()

        transcribe_response = self.client.post(
            f"/entries/{entry['id']}/transcribe",
            files={"audio": ("voice-note.webm", b"fake-webm-audio", "audio/webm")},
        )
        self.assertEqual(transcribe_response.status_code, 200)
        payload = transcribe_response.json()
        self.assertEqual(payload["raw_entry"]["entry_status"], "transcribed")
        self.assertTrue(payload["raw_entry"]["raw_text"])
        self.assertEqual(payload["raw_entry"]["transcript_provider_name"], "local_stub")
        self.assertEqual(len(payload["segments"]), 1)

        session = get_session_factory()()
        try:
            stored_entry = SqlAlchemyRawEntryRepository(session).get(entry["id"])
            stored_segments = SqlAlchemyTranscriptSegmentRepository(session).list_for_entry(entry["id"])
            event_types = [event.event_type for event in SqlAlchemyActivityEventRepository(session).list_recent(limit=10)]
            self.assertIsNotNone(stored_entry)
            self.assertEqual(stored_entry.entry_status, "transcribed")
            self.assertEqual(stored_entry.transcript_provider_name, "local_stub")
            self.assertEqual(len(stored_segments), 1)
            self.assertIn("transcription_started", event_types)
            self.assertIn("transcription_completed", event_types)
        finally:
            session.close()

    def test_whisper_cpp_provider_converts_browser_webm_before_transcription(self) -> None:
        temp_path = Path(self.temp_dir.name)
        executable_path = temp_path / "whisper-cli.exe"
        model_path = temp_path / "ggml-base.en.bin"
        audio_path = temp_path / "voice-note.webm"
        executable_path.write_text("fake executable", encoding="utf-8")
        model_path.write_text("fake model", encoding="utf-8")
        audio_path.write_bytes(b"fake browser audio")

        def fake_run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
            if command[0] == "ffmpeg.exe":
                Path(command[-1]).write_bytes(b"converted wav")
                return subprocess.CompletedProcess(command, 0, stdout="", stderr="")
            transcript_path = Path(f"{command[-1]}.txt")
            transcript_path.write_text("Schedule the April 29 meeting.", encoding="utf-8")
            return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

        provider = WhisperCppSTTProvider(str(executable_path), str(model_path))
        with patch("app.providers.local_stt.shutil.which", return_value="ffmpeg.exe"), patch(
            "app.providers.local_stt.subprocess.run",
            side_effect=fake_run,
        ) as run_mock:
            result = provider.transcribe(str(audio_path))

        self.assertEqual(result.text, "Schedule the April 29 meeting.")
        self.assertTrue((temp_path / "voice-note.whisper.wav").exists())
        self.assertEqual(run_mock.call_args_list[0].args[0][0], "ffmpeg.exe")
        self.assertEqual(Path(run_mock.call_args_list[1].args[0][4]).name, "voice-note.whisper.wav")

    def test_transcription_uses_stub_fallback_when_whisper_cpp_is_unavailable(self) -> None:
        os.environ["TASK_GARDEN_STT_PROVIDER"] = "whisper_cpp"
        os.environ["TASK_GARDEN_STT_EXECUTABLE_PATH"] = str(Path(self.temp_dir.name) / "missing-whisper.exe")
        os.environ["TASK_GARDEN_STT_MODEL_PATH"] = str(Path(self.temp_dir.name) / "missing-model.bin")
        self.rebuild_client()

        entry = self.client.post("/entries/audio", json={}).json()
        transcribe_response = self.client.post(
            f"/entries/{entry['id']}/transcribe",
            files={"audio": ("voice-note.webm", b"fake-webm-audio", "audio/webm")},
        )
        self.assertEqual(transcribe_response.status_code, 409)
        self.assertIn("Local transcription is not configured", transcribe_response.json()["detail"])

    def test_transcript_backed_entry_flows_into_existing_extraction_workflow(self) -> None:
        entry = self.client.post("/entries/audio", json={}).json()
        transcribe_response = self.client.post(
            f"/entries/{entry['id']}/transcribe",
            files={"audio": ("voice-note.webm", b"fake-webm-audio", "audio/webm")},
        )
        self.assertEqual(transcribe_response.status_code, 200)

        extraction = self.client.post(f"/entries/{entry['id']}/extract").json()
        confirm_candidates = [
            {
                "id": candidate["id"],
                "decision": "accepted" if index == 0 else "rejected",
                "title": candidate["title"],
                "details": candidate["details"],
                "project_or_group": candidate["project_or_group"],
                "priority": candidate["priority"],
                "effort": candidate["effort"],
                "energy": candidate["energy"],
                "labels": candidate["labels"],
                "due_date": candidate["due_date"],
                "parent_task_title": candidate["parent_task_title"],
                "confidence": candidate["confidence"],
                "source_excerpt": candidate["source_excerpt"],
            }
            for index, candidate in enumerate(extraction["candidates"])
        ]
        confirm_response = self.client.post(
            f"/extractions/{extraction['id']}/confirm",
            json={"candidates": confirm_candidates},
        )
        self.assertEqual(confirm_response.status_code, 200)

        session = get_session_factory()()
        try:
            tasks = SqlAlchemyTaskRepository(session).list_all()
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].source_raw_entry_id, entry["id"])
        finally:
            session.close()

    def test_ollama_provider_selection_and_normalization(self) -> None:
        self.client.patch(
            "/settings",
            json={
                "task_extraction_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434/api",
                "extraction_model": "llama3.1:8b",
            },
        )
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Email Sam and draft Atlas roadmap tomorrow"}).json()
        structured_content = """
        {
          "summary": "Two likely tasks extracted.",
          "open_questions": ["Project assignment may need review."],
          "candidates": [
            {
              "title": "Email Sam",
              "details": "Share the latest update.",
              "project_or_group": "Atlas",
              "priority": "medium",
              "effort": "small",
              "energy": "low",
              "labels": ["follow-up", " communication "],
              "due_date": null,
              "parent_task_title": null,
              "confidence": 0.82,
              "source_excerpt": "Email Sam"
            },
            {
              "title": "Draft Atlas roadmap",
              "details": "Capture the next milestones.",
              "project_or_group": "Atlas",
              "priority": "high",
              "effort": "large",
              "energy": "high",
              "labels": ["planning"],
              "due_date": "2026-04-19T17:00:00+00:00",
              "parent_task_title": null,
              "confidence": 0.76,
              "source_excerpt": "draft Atlas roadmap tomorrow"
            }
          ]
        }
        """
        with patch("app.providers.ollama.httpx.post", return_value=self.make_ollama_response(structured_content)):
            extract_response = self.client.post(f"/entries/{entry['id']}/extract")

        self.assertEqual(extract_response.status_code, 201)
        extraction = extract_response.json()
        self.assertEqual(extraction["provider_name"], "ollama")
        self.assertEqual(extraction["model_name"], "llama3.1:8b")
        self.assertEqual(extraction["summary"], "Two likely tasks extracted.")
        self.assertEqual(extraction["candidates"][0]["labels"], ["follow-up", "communication"])
        self.assertIsNone(extraction["candidates"][0]["due_date"])

    def test_ollama_retries_json_mode_when_schema_format_is_not_supported(self) -> None:
        self.client.patch(
            "/settings",
            json={
                "task_extraction_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434",
                "extraction_model": "gemma3:4b",
            },
        )
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Schedule the meeting and draft the plan"}).json()
        request = httpx.Request("POST", "http://127.0.0.1:11434/api/chat")
        schema_failure = httpx.Response(
            status_code=500,
            request=request,
            json={"error": "failed to load model vocabulary required for format"},
        )
        json_success = self.make_ollama_response(
            """
            {
              "summary": "Two tasks found.",
              "open_questions": [],
              "candidates": [
                {
                  "title": "Schedule the meeting",
                  "details": null,
                  "project_or_group": null,
                  "priority": "medium",
                  "effort": "small",
                  "energy": "low",
                  "labels": [],
                  "due_date": null,
                  "parent_task_title": null,
                  "confidence": 0.8,
                  "source_excerpt": "Schedule the meeting"
                }
              ]
            }
            """,
            model="gemma3:4b",
        )

        with patch("app.providers.ollama.httpx.post", side_effect=[schema_failure, json_success]) as post_mock:
            extract_response = self.client.post(f"/entries/{entry['id']}/extract")

        self.assertEqual(extract_response.status_code, 201)
        self.assertEqual(extract_response.json()["provider_name"], "ollama")
        self.assertEqual(len(post_mock.call_args_list), 2)
        self.assertEqual(post_mock.call_args_list[0].kwargs["json"]["format"]["type"], "object")
        self.assertEqual(post_mock.call_args_list[1].kwargs["json"]["format"], "json")

    def test_ollama_base_url_normalization_and_route_construction(self) -> None:
        self.assertEqual(normalize_ollama_base_url("http://127.0.0.1:11434/api"), "http://127.0.0.1:11434")
        self.assertEqual(normalize_ollama_base_url("http://127.0.0.1:11434/api/chat/"), "http://127.0.0.1:11434")
        self.assertEqual(build_ollama_chat_url("http://127.0.0.1:11434/api"), "http://127.0.0.1:11434/api/chat")

    def test_ollama_normalization_restrains_due_date_and_cleans_title(self) -> None:
        self.client.patch(
            "/settings",
            json={
                "task_extraction_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434",
                "extraction_model": "llama3.1:8b",
            },
        )
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Clean up the launch notes and message Sam"}).json()
        structured_content = """
        {
          "summary": "Two possible tasks.",
          "open_questions": [],
          "candidates": [
            {
              "title": " 1. clean up the launch notes. ",
              "details": "  tighten the document  ",
              "project_or_group": null,
              "priority": "medium",
              "effort": "medium",
              "energy": "medium",
              "labels": [" General ", "planning", "planning"],
              "due_date": "2026-04-20T17:00:00+00:00",
              "parent_task_title": null,
              "confidence": 0.61,
              "source_excerpt": "clean up the launch notes"
            }
          ]
        }
        """
        with patch("app.providers.ollama.httpx.post", return_value=self.make_ollama_response(structured_content)):
            extract_response = self.client.post(f"/entries/{entry['id']}/extract")

        self.assertEqual(extract_response.status_code, 201)
        candidate = extract_response.json()["candidates"][0]
        self.assertEqual(candidate["title"], "Clean up the launch notes")
        self.assertEqual(candidate["details"], "tighten the document")
        self.assertEqual(candidate["labels"], ["planning"])
        self.assertIsNone(candidate["due_date"])

    def test_ollama_malformed_output_returns_clear_error(self) -> None:
        self.client.patch(
            "/settings",
            json={
                "task_extraction_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434",
                "extraction_model": "llama3.1:8b",
            },
        )
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Do a few things"}).json()

        with patch("app.providers.ollama.httpx.post", return_value=self.make_ollama_response('{"summary":"bad","candidates":[{"priority":"urgent"}]}')):
            extract_response = self.client.post(f"/entries/{entry['id']}/extract")

        self.assertEqual(extract_response.status_code, 502)
        self.assertIn("could not be reviewed safely", extract_response.json()["detail"])

    def test_ollama_timeout_returns_timeout_error(self) -> None:
        self.client.patch(
            "/settings",
            json={
                "task_extraction_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434",
                "extraction_model": "llama3.1:8b",
            },
        )
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Prepare the report"}).json()

        with patch(
            "app.providers.ollama.httpx.post",
            side_effect=httpx.TimeoutException("timed out", request=httpx.Request("POST", "http://127.0.0.1:11434/api/chat")),
        ):
            extract_response = self.client.post(f"/entries/{entry['id']}/extract")

        self.assertEqual(extract_response.status_code, 504)
        self.assertIn("timed out", extract_response.json()["detail"])
        self.assertIn("still saved", extract_response.json()["detail"])

    def test_ollama_http_failure_does_not_silently_fallback(self) -> None:
        self.client.patch(
            "/settings",
            json={
                "task_extraction_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434",
                "extraction_model": "llama3.1:8b",
            },
        )
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Prepare the report"}).json()

        with patch(
            "app.providers.ollama.httpx.post",
            side_effect=httpx.ConnectError("connection refused", request=httpx.Request("POST", "http://127.0.0.1:11434/api/chat")),
        ):
            extract_response = self.client.post(f"/entries/{entry['id']}/extract")

        self.assertEqual(extract_response.status_code, 503)
        self.assertIn("ollama", extract_response.json()["detail"])
        self.assertIn("retry after checking the local provider setup", extract_response.json()["detail"])

        session = get_session_factory()()
        try:
            stored_entry = SqlAlchemyRawEntryRepository(session).get(entry["id"])
            self.assertEqual(stored_entry.entry_status, "new")
            batches = SqlAlchemyExtractionBatchRepository(session).list_for_entry(entry["id"])
            self.assertEqual(len(batches), 0)
            event_types = [event.event_type for event in SqlAlchemyActivityEventRepository(session).list_recent(limit=10)]
            self.assertIn("extraction_failed", event_types)
        finally:
            session.close()

    def test_ollama_low_signal_response_returns_422(self) -> None:
        self.client.patch(
            "/settings",
            json={
                "task_extraction_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434",
                "extraction_model": "llama3.1:8b",
            },
        )
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Maybe think about next quarter"}).json()

        with patch(
            "app.providers.ollama.httpx.post",
            return_value=self.make_ollama_response('{"summary":"Not enough signal.","open_questions":[],"candidates":[]}'),
        ):
            extract_response = self.client.post(f"/entries/{entry['id']}/extract")

        self.assertEqual(extract_response.status_code, 422)
        self.assertIn("did not produce enough usable structure", extract_response.json()["detail"])

    def test_confirm_flow_still_works_with_ollama_candidates(self) -> None:
        self.client.patch(
            "/settings",
            json={
                "task_extraction_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434",
                "extraction_model": "llama3.1:8b",
            },
        )
        entry = self.client.post("/entries", json={"source_type": "typed", "raw_text": "Email Sam and draft Atlas roadmap tomorrow"}).json()
        structured_content = """
        {
          "summary": "Two likely tasks extracted.",
          "open_questions": [],
          "candidates": [
            {
              "title": "Email Sam",
              "details": "Share the latest update.",
              "project_or_group": "Atlas",
              "priority": "medium",
              "effort": "small",
              "energy": "low",
              "labels": ["follow-up"],
              "due_date": null,
              "parent_task_title": null,
              "confidence": 0.82,
              "source_excerpt": "Email Sam"
            },
            {
              "title": "Draft Atlas roadmap",
              "details": "Capture the next milestones.",
              "project_or_group": "Atlas",
              "priority": "high",
              "effort": "large",
              "energy": "high",
              "labels": ["planning"],
              "due_date": null,
              "parent_task_title": null,
              "confidence": 0.76,
              "source_excerpt": "draft Atlas roadmap tomorrow"
            }
          ]
        }
        """
        with patch("app.providers.ollama.httpx.post", return_value=self.make_ollama_response(structured_content)):
            extraction = self.client.post(f"/entries/{entry['id']}/extract").json()

        confirm_candidates = [
            {
                "id": candidate["id"],
                "decision": "accepted" if index == 0 else "rejected",
                "title": candidate["title"],
                "details": candidate["details"],
                "project_or_group": candidate["project_or_group"],
                "priority": candidate["priority"],
                "effort": candidate["effort"],
                "energy": candidate["energy"],
                "labels": candidate["labels"],
                "due_date": candidate["due_date"],
                "parent_task_title": candidate["parent_task_title"],
                "confidence": candidate["confidence"],
                "source_excerpt": candidate["source_excerpt"],
            }
            for index, candidate in enumerate(extraction["candidates"])
        ]
        confirm_response = self.client.post(
            f"/extractions/{extraction['id']}/confirm",
            json={"candidates": confirm_candidates},
        )
        self.assertEqual(confirm_response.status_code, 200)

    def test_provider_check_reports_normalized_ollama_url_and_missing_model(self) -> None:
        self.client.patch(
            "/settings",
            json={
                "task_extraction_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434/api",
                "extraction_model": "llama3.1:8b",
            },
        )
        request = httpx.Request("GET", "http://127.0.0.1:11434/api/tags")
        response = httpx.Response(status_code=200, request=request, json={"models": [{"name": "qwen2.5:7b"}]})

        with patch("app.services.provider_checks.httpx.get", return_value=response):
            check_response = self.client.post("/settings/providers/check", json={"kind": "task_extraction"})

        self.assertEqual(check_response.status_code, 200)
        payload = check_response.json()
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["normalized_base_url"], "http://127.0.0.1:11434")
        self.assertEqual(payload["details"]["reason"], "model_missing")

    def test_provider_check_reports_helpful_404_message(self) -> None:
        self.client.patch(
            "/settings",
            json={
                "task_extraction_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434/api",
                "extraction_model": "llama3.1:8b",
            },
        )
        request = httpx.Request("GET", "http://127.0.0.1:11434/api/tags")
        response = httpx.Response(status_code=404, request=request)

        with patch(
            "app.services.provider_checks.httpx.get",
            side_effect=httpx.HTTPStatusError("404", request=request, response=response),
        ):
            check_response = self.client.post("/settings/providers/check", json={"kind": "task_extraction"})

        self.assertEqual(check_response.status_code, 200)
        payload = check_response.json()
        self.assertFalse(payload["ok"])
        self.assertIn("Do not include /api or /api/chat", payload["message"])

    def test_eval_harness_sample_summary_flags_out_of_range_counts(self) -> None:
        sample = {
            "id": "sample-test",
            "expected_min_candidates": 2,
            "expected_max_candidates": 2,
            "expect_temporal_signal": False,
        }
        result = eval_extraction_samples.evaluate_sample(
            type(
                "Result",
                (),
                {
                    "candidates": [],
                    "open_questions": [],
                },
            )(),
            sample,
        )
        self.assertIn("below_min(0<2)", result["notes"])
        self.assertIn("no_candidates_no_questions", result["notes"])


if __name__ == "__main__":
    unittest.main()
