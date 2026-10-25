import shutil
import subprocess
from pathlib import Path

import pytest

from commercial_engine.config import settings

HAS_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def env(tmp_path, monkeypatch):
    """Point every path setting at a temp dir; copy the real manifest in."""
    dirs = {
        "manifests_dir": tmp_path / "manifests",
        "broll_dir": tmp_path / "broll",
        "screen_recordings_dir": tmp_path / "screen",
        "work_dir": tmp_path / "work",
        "output_dir": tmp_path / "out",
    }
    for key, path in dirs.items():
        path.mkdir()
        monkeypatch.setattr(settings, key, str(path))
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "db.sqlite"))
    monkeypatch.setattr(settings, "commercial_engine_api_key", "test-key")
    monkeypatch.setattr(settings, "provider_retry_base_seconds", 0.0)
    monkeypatch.setattr(settings, "end_card_seconds", 1.0)
    shutil.copy(REPO / "manifests" / "jobcommand_v2.csv", dirs["manifests_dir"] / "jobcommand_v2.csv")
    return dirs


def make_clip(path: Path, seconds: float = 1.0, size: str = "1280x720") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=s={size}:r=30:d={seconds}",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path)],
        check=True,
    )
    return path


def make_mp3(seconds: float = 1.0) -> bytes:
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", f"sine=f=440:d={seconds}", "-f", "mp3", "-"],
        check=True, capture_output=True,
    )
    return out.stdout
