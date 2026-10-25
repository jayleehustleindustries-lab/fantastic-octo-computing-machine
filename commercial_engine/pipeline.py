"""Render one commercial: scenes in parallel (capped per provider), narration
first so it sets each scene's length, then stitch + end card + captions.

Every artifact is content-addressed, so a retry after a failure only pays for
the scenes that didn't finish. A failed scene never produces a fake file and
never lets the job reach ``staged``.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Awaitable, Callable

from .config import settings
from .manifest import Commercial, ManifestError, Scene, parse_manifest, resolve_manifest_path
from .media import compose_scene, concat, duration, end_card, is_valid_video, write_srt
from .providers import broll as broll_source, elevenlabs, heygen
from .providers.base import ProviderError, with_retries
from .state import FAILED, STAGED, Store

log = logging.getLogger("commercial_engine.pipeline")


def sha(*parts: object) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(str(p).encode())
        h.update(b"\x1f")
    return h.hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


@dataclass
class Providers:
    """Injectable provider calls (tests swap these for fakes)."""

    synthesize: Callable[[str], Awaitable[bytes]] = elevenlabs.synthesize
    voice_key: Callable[[], tuple[str, str]] = elevenlabs.cache_key_parts
    heygen_upload: Callable[[bytes], Awaitable[str]] = heygen.upload_audio
    heygen_create: Callable[..., Awaitable[str]] = heygen.create_video
    heygen_wait: Callable[[str], Awaitable[str]] = heygen.wait_for_video
    heygen_download: Callable[[str], Awaitable[bytes]] = heygen.download
    broll: Callable[[Scene], Path] = broll_source.resolve
    screen_recording: Callable[[Scene], Path] = broll_source.screen_recording


class Renderer:
    def __init__(self, store: Store, providers: Providers | None = None):
        self.store = store
        self.p = providers or Providers()
        self.sem_tts = asyncio.Semaphore(settings.elevenlabs_concurrency)
        self.sem_heygen = asyncio.Semaphore(settings.heygen_concurrency)
        self.sem_ffmpeg = asyncio.Semaphore(settings.ffmpeg_concurrency)
        self.work = settings.path("work_dir")

    async def _retry(self, fn, label: str):
        return await with_retries(fn, attempts=settings.provider_max_attempts, base_delay=settings.provider_retry_base_seconds, label=label)

    # --- steps ----------------------------------------------------------

    async def narration(self, scene: Scene) -> tuple[Path, str]:
        voice_id, model_id = self.p.voice_key()
        key = sha("vo", scene.voiceover_script, voice_id, model_id)
        path = self.work / "vo" / f"{key}.mp3"
        if path.is_file() and path.stat().st_size > 0:
            return path, key
        async with self.sem_tts:
            audio = await self._retry(lambda: self.p.synthesize(scene.voiceover_script), f"ElevenLabs {scene.scene_id}")
        write_atomic(path, audio)
        return path, key

    async def presenter(self, job_id: str, scene: Scene, narration: Path, narration_key: str) -> Path:
        out = self.work / "presenter" / f"{sha('heygen', settings.heygen_avatar_id, narration_key, settings.video_width, settings.video_height)}.mp4"
        if await is_valid_video(out):
            return out
        meta = self.store.scene_meta(job_id, scene.scene_id)
        video_id = meta.get("heygen_video_id") if meta.get("heygen_narration_key") == narration_key else None
        async with self.sem_heygen:
            if not video_id:
                audio_url = await self._retry(lambda: self.p.heygen_upload(narration.read_bytes()), f"HeyGen upload {scene.scene_id}")
                idem = f"{job_id}:{scene.scene_id}:{narration_key[:16]}"
                video_id = await self._retry(lambda: self.p.heygen_create(audio_url=audio_url, idempotency_key=idem), f"HeyGen create {scene.scene_id}")
                # Persist before polling: a crash resumes this render, it doesn't buy another.
                self.store.update_scene(job_id, scene.scene_id, meta_patch={"heygen_video_id": video_id, "heygen_narration_key": narration_key})
            url = await self.p.heygen_wait(video_id)
            data = await self._retry(lambda: self.p.heygen_download(url), f"HeyGen download {scene.scene_id}")
        write_atomic(out, data)
        if not await is_valid_video(out):
            out.unlink(missing_ok=True)
            raise ProviderError(f"HeyGen video {video_id} downloaded but is not a valid video")
        return out

    async def visual(self, job_id: str, scene: Scene, narration: Path, narration_key: str) -> Path:
        if scene.source == "presenter":
            return await self.presenter(job_id, scene, narration, narration_key)
        path = self.p.broll(scene) if scene.source == "broll" else self.p.screen_recording(scene)
        if not await is_valid_video(path):
            raise ProviderError(f"{path} is not a valid video file")
        return path

    async def scene(self, job_id: str, scene: Scene) -> tuple[Path, float] | None:
        sid = scene.scene_id
        try:
            self.store.update_scene(job_id, sid, status="rendering", error=None)
            narration, nkey = await self.narration(scene)
            seconds = await duration(narration) + settings.scene_tail_seconds
            visual = await self.visual(job_id, scene, narration, nkey)
            key = sha("scene", nkey, file_sha(visual), scene.hud_overlay_text, seconds, settings.video_width, settings.video_height, settings.video_fps, settings.hud_box_color, settings.hud_font_size)
            out = self.work / "scenes" / f"{sid}-{key[:16]}.mp4"
            if not await is_valid_video(out):
                async with self.sem_ffmpeg:
                    await compose_scene(visual=visual, narration=narration, hud_text=scene.hud_overlay_text, seconds=seconds, out=out)
            final_seconds = await duration(out)
            self.store.update_scene(job_id, sid, status="done", output_path=str(out), meta_patch={"seconds": round(final_seconds, 3)})
            return out, final_seconds
        except Exception as exc:  # recorded per scene; siblings keep going
            log.exception("scene %s failed", sid)
            self.store.update_scene(job_id, sid, status="failed", error=f"{type(exc).__name__}: {exc}")
            return None

    # --- job ------------------------------------------------------------

    def load_commercial(self, job: dict) -> Commercial:
        path = resolve_manifest_path(job["manifest"])
        if file_sha(path) != job["manifest_sha"]:
            raise ManifestError([f"{job['manifest']} changed after this job was queued; queue a new job for the new copy"])
        for c in parse_manifest(path):
            if c.video_id == job["video_id"]:
                return c
        raise ManifestError([f"{job['video_id']} not found in {job['manifest']}"])

    async def render(self, job: dict) -> dict:
        job_id = job["id"]
        try:
            commercial = self.load_commercial(job)
        except ManifestError as exc:
            return self.store.transition(job_id, FAILED, note="manifest", error=str(exc))

        results = await asyncio.gather(*(self.scene(job_id, s) for s in commercial.scenes))
        failed = [s.scene_id for s, r in zip(commercial.scenes, results) if r is None]
        if failed:
            return self.store.transition(job_id, FAILED, note="scene failures", error=f"failed scenes: {', '.join(failed)} (see GET /commercials/{job_id})")

        try:
            card = self.work / "end_cards" / f"{sha('card', settings.brand_name, settings.cta_text, settings.cta_url, settings.end_card_seconds, settings.video_width, settings.video_height, settings.video_fps)[:16]}.mp4"
            if not await is_valid_video(card):
                await end_card(card)
            out_dir = settings.path("output_dir") / commercial.video_id
            stem = f"{commercial.video_id}-{job_id[:8]}"
            final = await concat([r[0] for r in results] + [card], out_dir / f"{stem}.mp4")
            cues, t = [], 0.0
            for s, (_, secs) in zip(commercial.scenes, results):
                cues.append((t, t + secs, s.voiceover_script))
                t += secs
            srt = write_srt(cues, out_dir / f"{stem}.srt")
        except Exception as exc:
            log.exception("assembly failed for %s", job_id)
            return self.store.transition(job_id, FAILED, note="assembly", error=f"{type(exc).__name__}: {exc}")
        return self.store.transition(job_id, STAGED, note="rendered; awaiting approval", output_path=str(final), captions_path=str(srt), error=None)
