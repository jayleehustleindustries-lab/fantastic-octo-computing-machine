import pytest
from fastapi.testclient import TestClient

from commercial_engine import api
from commercial_engine.config import settings
from commercial_engine.state import Store

AUTH = {"Authorization": "Bearer test-key"}


@pytest.fixture
def client(env):
    store = Store(settings.database_path)
    api.app.dependency_overrides[api.get_store] = lambda: store
    yield TestClient(api.app), store
    api.app.dependency_overrides.clear()


def test_fails_closed_without_configured_key(client, monkeypatch):
    c, _ = client
    monkeypatch.setattr(settings, "commercial_engine_api_key", "")
    assert c.post("/commercials", json={"manifest": "jobcommand_v2.csv"}, headers=AUTH).status_code == 503


def test_rejects_bad_key(client):
    c, _ = client
    assert c.get("/commercials", headers={"X-API-Key": "nope"}).status_code == 401
    assert c.get("/commercials").status_code == 401


def test_enqueue_is_202_and_idempotent(client):
    c, _ = client
    r = c.post("/commercials", json={"manifest": "jobcommand_v2.csv", "video_ids": ["CK-02"]}, headers=AUTH)
    assert r.status_code == 202
    [job] = r.json()["jobs"]
    assert job["video_id"] == "CK-02" and job["status"] == "queued" and job["created"]
    again = c.post("/commercials", json={"manifest": "jobcommand_v2.csv", "video_ids": ["CK-02"]}, headers=AUTH).json()["jobs"][0]
    assert again["job_id"] == job["job_id"] and not again["created"]
    detail = c.get(f"/commercials/{job['job_id']}", headers=AUTH).json()
    assert [s["scene_id"] for s in detail["scenes"]] == ["CK-02-01", "CK-02-02", "CK-02-03", "CK-02-04"]


def test_bad_manifest_is_422_with_problems(client):
    c, _ = client
    r = c.post("/commercials", json={"manifest": "../etc/passwd"}, headers=AUTH)
    assert r.status_code == 422 and r.json()["detail"]["problems"]
    r = c.post("/commercials", json={"manifest": "jobcommand_v2.csv", "video_ids": ["CK-99"]}, headers=AUTH)
    assert r.status_code == 422


def test_approve_and_retry_rules(client):
    c, store = client
    job_id = c.post("/commercials", json={"manifest": "jobcommand_v2.csv", "video_ids": ["CK-01"]}, headers=AUTH).json()["jobs"][0]["job_id"]
    assert c.post(f"/commercials/{job_id}/approve", json={"approved_by": "Jay"}, headers=AUTH).status_code == 409
    store.claim_next()
    assert c.post(f"/commercials/{job_id}/retry", headers=AUTH).status_code == 409  # never re-queue a live render
    store.transition(job_id, "staged")
    r = c.post(f"/commercials/{job_id}/approve", json={"approved_by": "Jay"}, headers=AUTH)
    assert r.status_code == 200 and r.json()["job"]["status"] == "approved"
    assert c.get("/commercials/nope", headers=AUTH).status_code == 404
