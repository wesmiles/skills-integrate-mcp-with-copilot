import importlib
from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(ROOT / "src"))

import app as app_module


def test_activity_signups_persist_across_app_restarts(monkeypatch, tmp_path):
    db_path = tmp_path / "activities.db"
    monkeypatch.setattr(app_module, "DB_PATH", db_path)
    app_module.init_db()

    client = TestClient(app_module.app)
    response = client.post(
        "/activities/Chess Club/signup?email=student@example.com"
    )

    assert response.status_code == 200
    assert "student@example.com" in response.json()["message"]

    monkeypatch.setattr(app_module, "DB_PATH", db_path)
    app_module.activities = app_module.load_activities()
    importlib.reload(app_module)
    monkeypatch.setattr(app_module, "DB_PATH", db_path)
    app_module.activities = app_module.load_activities()
    app_module.init_db()

    client = TestClient(app_module.app)
    activities = client.get("/activities").json()

    assert "student@example.com" in activities["Chess Club"]["participants"]


def test_database_seed_populates_default_activities(monkeypatch, tmp_path):
    db_path = tmp_path / "activities.db"
    monkeypatch.setattr(app_module, "DB_PATH", db_path)
    app_module.init_db()

    client = TestClient(app_module.app)
    activities = client.get("/activities").json()

    assert "Chess Club" in activities
    assert "Programming Class" in activities
    assert len(activities["Chess Club"]["participants"]) >= 2
