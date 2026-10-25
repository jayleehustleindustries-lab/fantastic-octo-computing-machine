"""B-roll sources for the pain scenes.

Only the ``files`` provider ships: it uses pre-supplied clips at
``BROLL_DIR/{scene_id}.mp4`` (generate them in whatever tool you've verified,
e.g. your Make self-healing shot scenario) and fails closed when one is missing.
A generator adapter (Grok Imagine, Veo, ...) plugs in here once its API,
output durations and commercial-use terms are confirmed.
"""
from __future__ import annotations

from pathlib import Path

from ..config import settings
from ..manifest import Scene
from .base import ProviderNotConfigured


def resolve(scene: Scene) -> Path:
    provider = settings.broll_provider
    if provider != "files":
        raise ProviderNotConfigured(f"BROLL_PROVIDER={provider!r} is not implemented; use 'files'")
    path = Path(settings.broll_dir) / f"{scene.scene_id}.mp4"
    if not path.is_file():
        raise ProviderNotConfigured(f"missing B-roll clip {path} for {scene.scene_id} (prompt: {scene.visual_prompt[:80]})")
    return path


def screen_recording(scene: Scene) -> Path:
    path = Path(settings.screen_recordings_dir) / f"{scene.scene_id}.mp4"
    if not path.is_file():
        raise ProviderNotConfigured(f"missing screen recording {path} for {scene.scene_id}: record the real jobcommand.app flow ({scene.visual_prompt[:80]})")
    return path
