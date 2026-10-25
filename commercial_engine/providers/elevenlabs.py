"""ElevenLabs text-to-speech: one narrator voice for every scene."""
from __future__ import annotations

import httpx

from ..config import settings
from .base import ProviderNotConfigured, raise_for_status


async def synthesize(text: str) -> bytes:
    """Return MP3 bytes for ``text``. Raises before any request if unconfigured."""
    if not settings.elevenlabs_api_key or not settings.elevenlabs_voice_id:
        raise ProviderNotConfigured("ElevenLabs is not configured: set ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID")
    url = f"{settings.elevenlabs_url.rstrip('/')}/{settings.elevenlabs_voice_id}"
    headers = {
        "xi-api-key": settings.elevenlabs_api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(url, headers=headers, json={"text": text, "model_id": settings.elevenlabs_model_id})
    raise_for_status("ElevenLabs", response)
    if not response.content:
        raise ProviderNotConfigured("ElevenLabs returned an empty audio body")
    return response.content


def cache_key_parts() -> tuple[str, str]:
    return settings.elevenlabs_voice_id, settings.elevenlabs_model_id
