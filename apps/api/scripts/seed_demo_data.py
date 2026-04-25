from __future__ import annotations

import argparse
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[3]
    default_db = repo_root / "data" / "sqlite" / "task-garden-demo.db"
    parser = argparse.ArgumentParser(description="Seed deterministic Task Garden demo data.")
    parser.add_argument("--database-url", default=f"sqlite:///{default_db.as_posix()}")
    parser.add_argument("--reset", action="store_true", help="Delete the target SQLite demo database before seeding.")
    return parser.parse_args()


def sqlite_path_from_url(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite:///"):
        return None
    return Path(database_url.removeprefix("sqlite:///"))


def iso_days_from_now(days: int) -> str:
    value = datetime.now(timezone.utc) + timedelta(days=days)
    return value.replace(hour=12, minute=0, second=0, microsecond=0).isoformat()


def main() -> None:
    args = parse_args()
    db_path = sqlite_path_from_url(args.database_url)
    if args.reset and db_path is not None and db_path.exists():
        db_path.unlink()
    if db_path is not None:
        db_path.parent.mkdir(parents=True, exist_ok=True)

    os.environ["TASK_GARDEN_DATABASE_URL"] = args.database_url
    os.environ["TASK_GARDEN_TASK_EXTRACTION_PROVIDER"] = "mock"
    os.environ["TASK_GARDEN_RECAP_NARRATIVE_PROVIDER"] = "mock"
    os.environ["TASK_GARDEN_STT_PROVIDER"] = "local_stub"
    os.environ["TASK_GARDEN_AUTO_CONFIGURE_LOCAL_DEFAULTS"] = "false"

    from fastapi.testclient import TestClient

    from app.db.base import Base
    from app.db.session import get_engine
    from app.main import create_application

    Base.metadata.create_all(get_engine())
    client = TestClient(create_application())

    def post(path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        response = client.post(path, json=payload or {})
        response.raise_for_status()
        return response.json()

    def get(path: str) -> dict[str, Any]:
        response = client.get(path)
        response.raise_for_status()
        return response.json()

    home = post("/projects", {"name": "Home reset", "description": "Household and life admin."})
    atlas = post("/projects", {"name": "Atlas launch", "description": "Focused project work for the demo."})

    post(
        "/entries",
        {
            "source_type": "audio_transcript",
            "raw_text": "Follow up with Sam, clean up the launch notes, pay the invoice, and prep the Friday review.",
        },
    )
    post(
        "/entries",
        {
            "source_type": "typed",
            "raw_text": "Garden demo seed note: schedule maintenance, draft project plan, and close the overdue loop.",
        },
    )

    tasks = [
        ("Inbox: sort captured notes", None, None, "inbox", "medium", "small"),
        ("Today: send the Sam update", atlas["id"], 0, "planned", "high", "small"),
        ("This week: draft the Atlas review", atlas["id"], 3, "planned", "medium", "medium"),
        ("Overdue: pay the vendor invoice", home["id"], -4, "in_progress", "high", "small"),
        ("Backlog: reorganize project notes", atlas["id"], None, "inbox", "low", "medium"),
        ("Completed: clear desk capture", home["id"], -1, "completed", "medium", "small"),
        ("Completed: send April summary", atlas["id"], -2, "completed", "high", "medium"),
    ]

    for title, project_id, due_offset, status, priority, effort in tasks:
        task = post(
            "/tasks",
            {
                "title": title,
                "project_id": project_id,
                "due_date": iso_days_from_now(due_offset) if due_offset is not None else None,
                "status": "inbox" if status == "completed" else status,
                "priority": priority,
                "effort": effort,
                "energy": "medium",
            },
        )
        if status == "completed":
            post(f"/tasks/{task['id']}/complete")

    get("/recommendations/current")
    post("/planning/weekly-preview")
    post("/garden/recompute")
    weekly = post("/recaps/generate-weekly")
    monthly = post("/recaps/generate-monthly")
    yearly = post("/recaps/generate-yearly")

    client.close()
    print(f"Seeded demo database: {args.database_url}")
    print(f"Projects: {home['name']}, {atlas['name']}")
    print(f"Recaps: weekly={weekly['id']} monthly={monthly['id']} yearly={yearly['id']}")
    if db_path is not None:
        print(f"Start API with: TASK_GARDEN_DATABASE_URL={args.database_url}")


if __name__ == "__main__":
    main()
