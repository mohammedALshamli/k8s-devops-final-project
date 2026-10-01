import os
import tempfile
import pytest

from app import create_app
from models import db, Task


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

    with app.app_context():
        db.engine.dispose()

    os.close(db_fd)
    try:
        os.unlink(db_path)
    except PermissionError:
        pass


def test_create_task_default_priority(client):
    resp = client.post("/api/tasks", json={"title": "Write report"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["title"] == "Write report"
    assert data["priority"] == "medium"
    assert data["done"] is False


def test_create_task_with_explicit_priority(client):
    resp = client.post("/api/tasks", json={"title": "Fix outage", "priority": "high"})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["priority"] == "high"


def test_create_task_rejects_invalid_priority(client):
    resp = client.post("/api/tasks", json={"title": "Bad task", "priority": "urgent"})
    assert resp.status_code == 400


def test_list_tasks(client):
    client.post("/api/tasks", json={"title": "Task A"})
    client.post("/api/tasks", json={"title": "Task B", "priority": "low"})
    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2


def test_update_task_priority(client):
    create_resp = client.post("/api/tasks", json={"title": "Task C"})
    task_id = create_resp.get_json()["id"]

    update_resp = client.put(f"/api/tasks/{task_id}", json={"priority": "high", "done": True})
    assert update_resp.status_code == 200
    data = update_resp.get_json()
    assert data["priority"] == "high"
    assert data["done"] is True
