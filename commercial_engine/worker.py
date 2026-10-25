"""Worker process: claim queued jobs one at a time and render them.

Scene-level parallelism lives inside the renderer (per-provider semaphores);
run more workers only if your provider rate limits allow it.
"""
from __future__ import annotations

import asyncio
import logging

from .config import settings
from .pipeline import Renderer
from .state import Store

log = logging.getLogger("commercial_engine.worker")


async def run_once(store: Store, renderer: Renderer | None = None) -> dict | None:
    store.reclaim_stale(settings.stale_claim_seconds)
    job = store.claim_next()
    if not job:
        return None
    log.info("rendering %s (%s)", job["id"], job["video_id"])
    result = await (renderer or Renderer(store)).render(job)
    log.info("job %s -> %s %s", job["id"], result["status"], result.get("error") or result.get("output_path") or "")
    return result


async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    store = Store(settings.database_path)
    renderer = Renderer(store)
    while True:
        if not await run_once(store, renderer):
            await asyncio.sleep(settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    asyncio.run(main())
