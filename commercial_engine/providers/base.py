"""Shared provider errors + bounded retry for transient failures."""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, TypeVar

import httpx

log = logging.getLogger("commercial_engine.providers")
T = TypeVar("T")


class ProviderError(RuntimeError):
    """Expected provider failure. ``retryable`` decides whether to try again."""

    def __init__(self, message: str, *, retryable: bool = False, status_code: int | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


class ProviderNotConfigured(ProviderError):
    pass


def raise_for_status(provider: str, response: httpx.Response) -> None:
    if response.is_success:
        return
    code = response.status_code
    if code in (401, 403):
        raise ProviderError(f"{provider} rejected the API key (HTTP {code})", status_code=code)
    retryable = code == 429 or code >= 500
    body = response.text[:300]
    raise ProviderError(f"{provider} HTTP {code}: {body}", retryable=retryable, status_code=code)


async def with_retries(fn: Callable[[], Awaitable[T]], *, attempts: int, base_delay: float, label: str) -> T:
    """Retry only retryable provider errors and network errors, with backoff."""
    last: BaseException | None = None
    for attempt in range(1, max(1, attempts) + 1):
        try:
            return await fn()
        except ProviderError as exc:
            if not exc.retryable:
                raise
            last = exc
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            last = exc
        if attempt < attempts:
            delay = base_delay * (2 ** (attempt - 1))
            log.warning("%s attempt %d failed (%s); retrying in %.1fs", label, attempt, last, delay)
            await asyncio.sleep(delay)
    raise ProviderError(f"{label} failed after {attempts} attempts: {last}")
