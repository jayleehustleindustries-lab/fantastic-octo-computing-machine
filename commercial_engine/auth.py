"""Bearer / X-API-Key auth that fails closed when no key is configured."""
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException

from .config import settings


def require_api_key(authorization: str | None = Header(default=None), x_api_key: str | None = Header(default=None)) -> None:
    expected = (settings.commercial_engine_api_key or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="COMMERCIAL_ENGINE_API_KEY is not set; API is locked")
    supplied = x_api_key or ""
    if authorization and authorization.lower().startswith("bearer "):
        supplied = authorization[7:]
    if not supplied or not hmac.compare_digest(supplied.strip(), expected):
        raise HTTPException(status_code=401, detail="invalid or missing API key")
