"""Shared retry-with-backoff helper. Used by every script in this pipeline
that talks to a network API (Supabase, Shopify) so a transient failure
(rate limit, timeout, dropped connection) doesn't kill an entire batch run.
"""
import time
from typing import Callable, TypeVar

T = TypeVar("T")


class RetryExhausted(Exception):
    """Raised when a call still fails after all retry attempts."""


def with_retries(
    fn: Callable[[], T],
    *,
    attempts: int = 4,
    base_delay_seconds: float = 1.0,
    retry_on: tuple[type[Exception], ...] = (Exception,),
    label: str = "operation",
) -> T:
    """Call fn(), retrying with exponential backoff (1s, 2s, 4s, 8s...) on
    any exception in retry_on. Re-raises the last exception, wrapped in
    RetryExhausted, if every attempt fails.
    """
    last_exc: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except retry_on as exc:  # noqa: BLE001 -- intentionally broad, caller narrows via retry_on
            last_exc = exc
            if attempt == attempts:
                break
            delay = base_delay_seconds * (2 ** (attempt - 1))
            print(f"  retry {attempt}/{attempts} for {label} after error ({exc}); waiting {delay:.0f}s")
            time.sleep(delay)

    raise RetryExhausted(f"{label} failed after {attempts} attempts: {last_exc}") from last_exc
