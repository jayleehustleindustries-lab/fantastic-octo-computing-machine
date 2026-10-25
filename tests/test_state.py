import time

import pytest

from commercial_engine.state import IllegalTransition, Store


@pytest.fixture
def store(tmp_path):
    return Store(str(tmp_path / "s.db"))


def new(store, sha="abc"):
    job, created = store.create_job(manifest="m.csv", manifest_sha=sha, video_id="CK-01", scene_ids=["CK-01-01", "CK-01-02"])
    return job, created


def test_duplicate_active_job_is_not_recreated(store):
    a, created_a = new(store)
    b, created_b = new(store)
    assert created_a and not created_b and a["id"] == b["id"]
    c, created_c = new(store, sha="changed-copy")
    assert created_c and c["id"] != a["id"]


def test_happy_path_and_approval_gate(store):
    job, _ = new(store)
    with pytest.raises(IllegalTransition):
        store.approve(job["id"], approved_by="me")  # queued can't be approved
    claimed = store.claim_next()
    assert claimed["id"] == job["id"] and claimed["status"] == "rendering"
    assert store.claim_next() is None
    store.transition(job["id"], "staged")
    with pytest.raises(IllegalTransition):
        store.approve(job["id"], approved_by="  ")
    done = store.approve(job["id"], approved_by="Jay", note="ship it")
    assert done["status"] == "approved" and done["approved_by"] == "Jay"
    with pytest.raises(IllegalTransition):
        store.transition(job["id"], "queued")  # approved is terminal
    assert [e["to_status"] for e in store.events(job["id"])] == ["queued", "rendering", "staged", "approved"]


def test_illegal_skip(store):
    job, _ = new(store)
    with pytest.raises(IllegalTransition):
        store.transition(job["id"], "staged")


def test_failed_job_can_be_requeued_and_failure_frees_dedupe(store):
    job, _ = new(store)
    store.claim_next()
    store.transition(job["id"], "failed", error="boom")
    again, created = new(store)
    assert created  # failed jobs don't block a fresh enqueue
    store.transition(job["id"], "queued")


def test_stale_claim_reclaimed(store):
    job, _ = new(store)
    store.claim_next()
    assert store.reclaim_stale(3600) == 0
    store._conn.execute("UPDATE jobs SET claimed_at=? WHERE id=?", (time.time() - 7200, job["id"]))
    assert store.reclaim_stale(3600) == 1
    assert store.get_job(job["id"])["status"] == "queued"


def test_scene_meta_merges(store):
    job, _ = new(store)
    store.update_scene(job["id"], "CK-01-01", meta_patch={"a": 1})
    store.update_scene(job["id"], "CK-01-01", meta_patch={"b": 2}, status="done")
    assert store.scene_meta(job["id"], "CK-01-01") == {"a": 1, "b": 2}
