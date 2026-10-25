"""Queue commercials from a manifest. Validation happens here, before any job
exists, so a bad sheet costs nothing."""
from __future__ import annotations

from .manifest import ManifestError, parse_manifest, resolve_manifest_path
from .pipeline import file_sha
from .state import Store


def enqueue(store: Store, manifest: str, video_ids: list[str] | None = None) -> list[dict]:
    path = resolve_manifest_path(manifest)
    commercials = parse_manifest(path)
    wanted = set(video_ids or [])
    unknown = wanted - {c.video_id for c in commercials}
    if unknown:
        raise ManifestError([f"video_id not in manifest: {', '.join(sorted(unknown))}"])
    digest = file_sha(path)
    out = []
    for c in commercials:
        if wanted and c.video_id not in wanted:
            continue
        job, created = store.create_job(manifest=manifest, manifest_sha=digest, video_id=c.video_id, scene_ids=[s.scene_id for s in c.scenes])
        out.append({"job_id": job["id"], "video_id": c.video_id, "status": job["status"], "created": created})
    return out
