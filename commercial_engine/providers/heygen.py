"""HeyGen stock presenter: lip-sync a stock avatar to our ElevenLabs narration.

Flow: upload the scene MP3 as a HeyGen asset -> create a video whose voice is
that audio -> poll until completed -> download. The provider ``video_id`` is
persisted by the caller *before* polling so a crash resumes polling instead of
paying for a second render (Media-state-engine pattern).

Endpoint shapes follow Media-state-engine's ``/v3/videos`` client plus HeyGen's
asset upload endpoint; verify against your HeyGen plan before the first paid run.
"""
from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from ..config import settings
from .base import ProviderError, ProviderNotConfigured, raise_for_status

DONE = {"completed", "success", "succeeded"}
FAILED = {"failed", "error"}


def _require() -> tuple[str, str]:
    if not settings.heygen_api_key:
        raise ProviderNotConfigured("HeyGen is not configured: set HEYGEN_API_KEY")
    if not settings.heygen_avatar_id:
        raise ProviderNotConfigured("HeyGen stock avatar not set: set HEYGEN_AVATAR_ID")
    return settings.heygen_api_key, settings.heygen_api_url.rstrip("/")


def _data(body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise ProviderError("HeyGen returned a non-object response")
    data = body.get("data", body)
    if not isinstance(data, dict):
        raise ProviderError("HeyGen response has no data object")
    return data


async def upload_audio(mp3: bytes) -> str:
    api_key, _ = _require()
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{settings.heygen_upload_url.rstrip('/')}/v1/asset",
            headers={"X-Api-Key": api_key, "Content-Type": "audio/mpeg"},
            content=mp3,
        )
    raise_for_status("HeyGen upload", response)
    data = _data(response.json())
    url = data.get("url")
    if not url:
        raise ProviderError("HeyGen upload response has no url")
    return str(url)


async def create_video(*, audio_url: str, idempotency_key: str) -> str:
    api_key, base = _require()
    payload = {
        "video_inputs": [
            {
                "character": {"type": "avatar", "avatar_id": settings.heygen_avatar_id},
                "voice": {"type": "audio", "audio_url": audio_url},
                "background": {"type": "color", "value": settings.heygen_background_color},
            }
        ],
        "dimension": {"width": settings.video_width, "height": settings.video_height},
    }
    headers = {"X-Api-Key": api_key, "Content-Type": "application/json", "Accept": "application/json", "Idempotency-Key": idempotency_key}
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(f"{base}/v3/videos", headers=headers, json=payload)
    raise_for_status("HeyGen", response)
    data = _data(response.json())
    video_id = data.get("video_id") or data.get("id")
    if not video_id:
        raise ProviderError("HeyGen response did not include video_id")
    return str(video_id)


async def wait_for_video(video_id: str) -> str:
    """Poll until done; return the downloadable video URL."""
    api_key, base = _require()
    deadline = time.monotonic() + settings.heygen_timeout_seconds
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            response = await client.get(f"{base}/v3/videos/{video_id}", headers={"X-Api-Key": api_key, "Accept": "application/json"})
            raise_for_status("HeyGen status", response)
            data = _data(response.json())
            status = str(data.get("status", "")).lower()
            if status in DONE:
                url = data.get("video_url")
                if not url:
                    raise ProviderError(f"HeyGen video {video_id} completed without video_url")
                return str(url)
            if status in FAILED:
                raise ProviderError(f"HeyGen video {video_id} failed: {data.get('error')}")
            if time.monotonic() > deadline:
                raise ProviderError(f"HeyGen video {video_id} timed out after {settings.heygen_timeout_seconds:.0f}s", retryable=False)
            await asyncio.sleep(settings.heygen_poll_interval_seconds)


async def download(url: str) -> bytes:
    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        response = await client.get(url)
    raise_for_status("HeyGen download", response)
    return response.content
