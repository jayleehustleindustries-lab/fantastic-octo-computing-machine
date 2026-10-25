"""Job state machine + SQLite store.

Mirrors Media-state-engine's guarantees on a single-node store: every status
change validates an allowed edge, writes an ``events`` row and updates the job
in one transaction (``BEGIN IMMEDIATE`` serialises writers). Nothing reaches
``approved`` except through :func:`approve`.
"""
from __future__ import annotations

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

QUEUED = "queued"
RENDERING = "rendering"
STAGED = "staged"  # rendered, awaiting human approval
APPROVED = "approved"
FAILED = "failed"

ALLOWED = {
    QUEUED: {RENDERING, FAILED},
    RENDERING: {STAGED, FAILED, QUEUED},  # QUEUED = stale-claim reclaim
    STAGED: {APPROVED, QUEUED},  # QUEUED = re-render after review notes
    FAILED: {QUEUED},  # retry; finished scenes are reused
    APPROVED: set(),
}
ACTIVE = (QUEUED, RENDERING, STAGED)

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  manifest TEXT NOT NULL,
  manifest_sha TEXT NOT NULL,
  video_id TEXT NOT NULL,
  status TEXT NOT NULL,
  error TEXT,
  output_path TEXT,
  captions_path TEXT,
  claimed_at REAL,
  approved_by TEXT,
  approved_at REAL,
  approval_note TEXT,
  created_at REAL NOT NULL,
  updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status);
CREATE TABLE IF NOT EXISTS scenes (
  job_id TEXT NOT NULL REFERENCES jobs(id),
  scene_id TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  output_path TEXT,
  error TEXT,
  meta TEXT NOT NULL DEFAULT '{}',
  updated_at REAL NOT NULL,
  PRIMARY KEY (job_id, scene_id)
);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT NOT NULL,
  from_status TEXT,
  to_status TEXT NOT NULL,
  note TEXT,
  at REAL NOT NULL
);
"""


class IllegalTransition(RuntimeError):
    pass


class JobNotFound(LookupError):
    pass


class Store:
    def __init__(self, path: str):
        self.path = path
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(path, isolation_level=None, check_same_thread=False, timeout=30)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(SCHEMA)

    @contextmanager
    def tx(self) -> Iterator[sqlite3.Connection]:
        self._conn.execute("BEGIN IMMEDIATE")
        try:
            yield self._conn
        except BaseException:
            self._conn.execute("ROLLBACK")
            raise
        else:
            self._conn.execute("COMMIT")

    # --- jobs -----------------------------------------------------------

    def create_job(self, *, manifest: str, manifest_sha: str, video_id: str, scene_ids: list[str]) -> tuple[dict, bool]:
        """Create a queued job, or return the active one for the same content.

        Returns ``(job, created)``. Same manifest content + video_id while a job
        is still active is a duplicate, not a second paid render.
        """
        now = time.time()
        with self.tx() as c:
            existing = c.execute(
                f"SELECT * FROM jobs WHERE manifest_sha=? AND video_id=? AND status IN ({','.join('?' * len(ACTIVE))}) ORDER BY created_at DESC LIMIT 1",
                (manifest_sha, video_id, *ACTIVE),
            ).fetchone()
            if existing:
                return dict(existing), False
            job_id = str(uuid.uuid4())
            c.execute(
                "INSERT INTO jobs (id, manifest, manifest_sha, video_id, status, created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
                (job_id, manifest, manifest_sha, video_id, QUEUED, now, now),
            )
            c.executemany(
                "INSERT INTO scenes (job_id, scene_id, updated_at) VALUES (?,?,?)",
                [(job_id, sid, now) for sid in scene_ids],
            )
            c.execute("INSERT INTO events (job_id, from_status, to_status, note, at) VALUES (?,?,?,?,?)", (job_id, None, QUEUED, "created", now))
            row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        return dict(row), True

    def get_job(self, job_id: str) -> dict:
        row = self._conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise JobNotFound(job_id)
        return dict(row)

    def list_jobs(self, limit: int = 50) -> list[dict]:
        return [dict(r) for r in self._conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,))]

    def transition(self, job_id: str, to_status: str, *, note: str | None = None, expect: str | None = None, **fields: Any) -> dict:
        now = time.time()
        with self.tx() as c:
            row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            if not row:
                raise JobNotFound(job_id)
            current = row["status"]
            if expect is not None and current != expect:
                raise IllegalTransition(f"job {job_id} is {current}, expected {expect}")
            if to_status not in ALLOWED.get(current, set()):
                raise IllegalTransition(f"{current} -> {to_status} is not allowed")
            sets = {"status": to_status, "updated_at": now, **fields}
            c.execute(
                f"UPDATE jobs SET {', '.join(f'{k}=?' for k in sets)} WHERE id=?",
                (*sets.values(), job_id),
            )
            c.execute("INSERT INTO events (job_id, from_status, to_status, note, at) VALUES (?,?,?,?,?)", (job_id, current, to_status, note, now))
            return dict(c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())

    def claim_next(self) -> dict | None:
        """Atomically move the oldest queued job to rendering."""
        now = time.time()
        with self.tx() as c:
            row = c.execute("SELECT id FROM jobs WHERE status=? ORDER BY created_at LIMIT 1", (QUEUED,)).fetchone()
            if not row:
                return None
            c.execute("UPDATE jobs SET status=?, claimed_at=?, updated_at=?, error=NULL WHERE id=?", (RENDERING, now, now, row["id"]))
            c.execute("INSERT INTO events (job_id, from_status, to_status, note, at) VALUES (?,?,?,?,?)", (row["id"], QUEUED, RENDERING, "claimed", now))
            return dict(c.execute("SELECT * FROM jobs WHERE id=?", (row["id"],)).fetchone())

    def reclaim_stale(self, stale_seconds: int) -> int:
        """Return crashed ``rendering`` claims to the queue."""
        cutoff = time.time() - stale_seconds
        ids = [r["id"] for r in self._conn.execute("SELECT id FROM jobs WHERE status=? AND claimed_at < ?", (RENDERING, cutoff))]
        for job_id in ids:
            try:
                self.transition(job_id, QUEUED, note="stale claim reclaimed", expect=RENDERING)
            except IllegalTransition:
                pass
        return len(ids)

    def approve(self, job_id: str, *, approved_by: str, note: str | None = None) -> dict:
        if not (approved_by or "").strip():
            raise IllegalTransition("approved_by is required")
        return self.transition(
            job_id,
            APPROVED,
            note="approved",
            expect=STAGED,
            approved_by=approved_by.strip(),
            approved_at=time.time(),
            approval_note=note,
        )

    # --- scenes ---------------------------------------------------------

    def scenes(self, job_id: str) -> list[dict]:
        rows = self._conn.execute("SELECT * FROM scenes WHERE job_id=? ORDER BY scene_id", (job_id,))
        out = []
        for r in rows:
            d = dict(r)
            d["meta"] = json.loads(d["meta"] or "{}")
            out.append(d)
        return out

    def scene_meta(self, job_id: str, scene_id: str) -> dict:
        row = self._conn.execute("SELECT meta FROM scenes WHERE job_id=? AND scene_id=?", (job_id, scene_id)).fetchone()
        return json.loads(row["meta"]) if row else {}

    def update_scene(self, job_id: str, scene_id: str, *, meta_patch: dict | None = None, **fields: Any) -> None:
        with self.tx() as c:
            row = c.execute("SELECT meta FROM scenes WHERE job_id=? AND scene_id=?", (job_id, scene_id)).fetchone()
            if not row:
                raise JobNotFound(f"{job_id}/{scene_id}")
            sets = dict(fields)
            if meta_patch:
                meta = json.loads(row["meta"] or "{}")
                meta.update(meta_patch)
                sets["meta"] = json.dumps(meta)
            sets["updated_at"] = time.time()
            c.execute(
                f"UPDATE scenes SET {', '.join(f'{k}=?' for k in sets)} WHERE job_id=? AND scene_id=?",
                (*sets.values(), job_id, scene_id),
            )

    def events(self, job_id: str) -> list[dict]:
        return [dict(r) for r in self._conn.execute("SELECT * FROM events WHERE job_id=? ORDER BY id", (job_id,))]
