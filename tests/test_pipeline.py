"""End-to-end renders with real ffmpeg and fake (free) providers."""
import asyncio
from pathlib import Path

import pytest

from commercial_engine import media
from commercial_engine.config import settings
from commercial_engine.jobs import enqueue
from commercial_engine.manifest import Scene
from commercial_engine.pipeline import Providers, Renderer
from commercial_engine.providers.base import ProviderError
from commercial_engine.state import Store
from commercial_engine.worker import run_once

from .conftest import HAS_FFMPEG, make_clip, make_mp3

pytestmark = pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg/ffprobe not installed")


class Fakes:
    def __init__(self, tmp: Path, *, wait_failures: int = 0):
        self.tmp = tmp
        self.calls = {"tts": 0, "upload": 0, "create": 0, "wait": 0}
        self.wait_failures = wait_failures
        self.presenter_clip = make_clip(tmp / "fake_heygen.mp4", 2.0, "1080x1920")

    async def synthesize(self, text):
        self.calls["tts"] += 1
        return make_mp3(1.0)

    async def upload(self, mp3):
        self.calls["upload"] += 1
        return "https://example.invalid/audio.mp3"

    async def create(self, *, audio_url, idempotency_key):
        self.calls["create"] += 1
        return f"hg_{self.calls['create']}"

    async def wait(self, video_id):
        self.calls["wait"] += 1
        if self.wait_failures:
            self.wait_failures -= 1
            raise ProviderError("worker crashed mid-poll")
        return "https://example.invalid/video.mp4"

    async def download(self, url):
        return self.presenter_clip.read_bytes()

    def providers(self) -> Providers:
        return Providers(
            synthesize=self.synthesize,
            voice_key=lambda: ("voice", "model"),
            heygen_upload=self.upload,
            heygen_create=self.create,
            heygen_wait=self.wait,
            heygen_download=self.download,
        )


def supply_footage(env, video_id):
    make_clip(Path(env["broll_dir"]) / f"{video_id}-02.mp4", 0.6)  # shorter than VO -> must loop
    make_clip(Path(env["screen_recordings_dir"]) / f"{video_id}-03.mp4", 3.0, "1170x2532")  # phone capture -> must crop


async def test_full_commercial_renders_and_stages(env, tmp_path):
    store = Store(settings.database_path)
    fakes = Fakes(tmp_path)
    supply_footage(env, "CK-03")  # CK-03 HUD has an apostrophe: "WHERE'S TRUCK 2?"
    [job] = enqueue(store, "jobcommand_v2.csv", ["CK-03"])

    result = await run_once(store, Renderer(store, fakes.providers()))
    assert result["status"] == "staged", result["error"]
    out = Path(result["output_path"])
    assert await media.is_valid_video(out)
    total = await media.duration(out)
    # 4 scenes x (1.0s VO + 0.25s tail) + 1.0s end card
    assert total == pytest.approx(4 * 1.25 + 1.0, abs=0.4)
    srt = Path(result["captions_path"]).read_text()
    assert "Three trucks, three group chats" in srt and "00:00:00,000 -->" in srt
    assert fakes.calls["create"] == 2  # two presenter scenes
    assert all(s["status"] == "done" for s in store.scenes(job["job_id"]))


async def test_missing_footage_fails_job_without_fake_output_then_retry_reuses_work(env, tmp_path):
    store = Store(settings.database_path)
    fakes = Fakes(tmp_path)
    make_clip(Path(env["broll_dir"]) / "CK-02-02.mp4", 1.0)  # screen recording deliberately missing
    [job] = enqueue(store, "jobcommand_v2.csv", ["CK-02"])
    renderer = Renderer(store, fakes.providers())

    result = await run_once(store, renderer)
    assert result["status"] == "failed"
    assert "CK-02-03" in result["error"] and result["output_path"] is None
    scenes = {s["scene_id"]: s for s in store.scenes(job["job_id"])}
    assert scenes["CK-02-03"]["status"] == "failed" and "screen recording" in scenes["CK-02-03"]["error"]
    assert scenes["CK-02-01"]["status"] == "done"  # siblings finished
    assert not list(Path(env["output_dir"]).rglob("*.mp4"))
    paid_tts, paid_create = fakes.calls["tts"], fakes.calls["create"]

    make_clip(Path(env["screen_recordings_dir"]) / "CK-02-03.mp4", 2.0)
    store.transition(job["job_id"], "queued", note="footage added")
    result = await run_once(store, renderer)
    assert result["status"] == "staged", result["error"]
    assert fakes.calls["tts"] == paid_tts  # every narration was cached
    assert fakes.calls["create"] == paid_create  # no second HeyGen render


async def test_heygen_crash_resumes_existing_video_instead_of_paying_again(env, tmp_path):
    store = Store(settings.database_path)
    fakes = Fakes(tmp_path, wait_failures=1)
    job, _ = store.create_job(manifest="x.csv", manifest_sha="x", video_id="CK-01", scene_ids=["CK-01-01"])
    renderer = Renderer(store, fakes.providers())
    scene = Scene("CK-01", 1, "presenter", "p", "MISSED CALL = JOB GONE", "hello")
    narration, key = await renderer.narration(scene)

    with pytest.raises(ProviderError):
        await renderer.presenter(job["id"], scene, narration, key)
    assert store.scene_meta(job["id"], "CK-01-01")["heygen_video_id"] == "hg_1"
    out = await renderer.presenter(job["id"], scene, narration, key)
    assert await media.is_valid_video(out)
    assert fakes.calls["create"] == 1 and fakes.calls["upload"] == 1


async def test_edited_manifest_after_enqueue_fails_closed(env, tmp_path):
    store = Store(settings.database_path)
    [job] = enqueue(store, "jobcommand_v2.csv", ["CK-01"])
    path = Path(env["manifests_dir"]) / "jobcommand_v2.csv"
    path.write_text(path.read_text().replace("Stop losing jobs", "Quit losing jobs"))
    result = await run_once(store, Renderer(store, Fakes(tmp_path).providers()))
    assert result["status"] == "failed" and "changed after this job was queued" in result["error"]


async def test_hud_with_colon_comma_quote_percent_burns(env, tmp_path):
    visual = make_clip(tmp_path / "v.mp4", 1.0)
    narration = tmp_path / "n.mp3"
    narration.write_bytes(make_mp3(1.0))
    out = await media.compose_scene(visual=visual, narration=narration, hud_text="9:30 PM, WHERE'S $1,200? 100%", seconds=1.0, out=tmp_path / "s.mp4")
    assert await media.is_valid_video(out)


def test_unsafe_graph_path_rejected(tmp_path):
    with pytest.raises(media.MediaError):
        media.graph_path(tmp_path / "bad name:x.txt")


def test_long_hud_shrinks_font():
    assert media.hud_font_size("SHORT") == settings.hud_font_size
    assert media.hud_font_size("X" * 32) < settings.hud_font_size


async def test_stub_file_is_not_a_valid_video(tmp_path):
    fake = tmp_path / "fake.mp4"
    fake.write_text("mock_mp4_binary")
    assert not await media.is_valid_video(fake)
