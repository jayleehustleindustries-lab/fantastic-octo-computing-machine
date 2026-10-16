"""Shared plumbing for the heavy jobs: cached features, resumable parallel task runner, quick mode."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import pandas as pd

from oklahoma import features as features_mod
from oklahoma import ingest
from oklahoma.features import build_features

ROOT = ingest.ROOT
OUT = ROOT / "reports" / "jobs"
FEATS = ROOT / "data" / "features.parquet"
FEATS_HASH = ROOT / "data" / "features.hash"


def _features_source_hash() -> str:
    """Fingerprint of oklahoma/features.py, so a feature change can never reuse a stale cache."""
    return hashlib.sha256(pathlib.Path(features_mod.__file__).read_bytes()).hexdigest()


def features() -> pd.DataFrame:
    """Build features once; reuse while the games file and the features.py source are unchanged.

    The parquet is only trusted if data/features.hash holds the current source hash (the old
    mtime-only check silently served columns computed by an older features.py)."""
    fresh = (FEATS.exists() and FEATS.stat().st_mtime >= ingest.GAMES_PATH.stat().st_mtime
             and FEATS_HASH.exists() and FEATS_HASH.read_text().strip() == _features_source_hash())
    if fresh:
        return pd.read_parquet(FEATS)
    f = build_features(pd.read_parquet(ingest.GAMES_PATH))
    f.to_parquet(FEATS, index=False)
    FEATS_HASH.write_text(_features_source_hash() + "\n")
    return f


def eligible(f: pd.DataFrame, market: str, min_prior: int = 5) -> pd.DataFrame:
    return f[(f["career_games"] >= min_prior) & f[f"line_proxy_{market}"].notna()]


def split(el: pd.DataFrame, season: int, window: int = 5):
    train = el[(el["season"] < season) & (el["season"] >= season - window)]
    test = el[el["season"] == season]
    assert train.empty or train["season"].max() < season
    return train, test


def parser(desc: str) -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--quick", action="store_true", help="smoke test: tiny slice, minutes not hours")
    ap.add_argument("--test-seasons", default="2021-2026")
    return ap


def seasons(args) -> list[int]:
    return [2025, 2026] if args.quick else ingest.parse_seasons(args.test_seasons)


def run_tasks(name: str, tasks: list[dict], fn, workers: int = 1) -> pd.DataFrame:
    """Run fn(task)->dict over tasks in parallel; append each result to a jsonl so a crash resumes."""
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}.jsonl"
    done = {}
    if path.exists():
        for line in path.read_text().splitlines():
            r = json.loads(line)
            done[r["_key"]] = r
    todo = [t for t in tasks if json.dumps(t, sort_keys=True) not in done]
    print(f"[{name}] {len(tasks)} tasks, {len(done)} already done, {len(todo)} to run, {workers} workers", flush=True)
    t0 = time.time()
    with path.open("a") as out, ProcessPoolExecutor(workers) as ex:
        futs = {ex.submit(fn, t): t for t in todo}
        for i, fu in enumerate(as_completed(futs), 1):
            t = futs[fu]
            r = {**t, **fu.result(), "_key": json.dumps(t, sort_keys=True)}
            out.write(json.dumps(r, default=float) + "\n"); out.flush()
            done[r["_key"]] = r
            if i % 10 == 0 or i == len(todo):
                print(f"[{name}] {i}/{len(todo)} done, {time.time() - t0:.0f}s", flush=True)
    keys = {json.dumps(t, sort_keys=True) for t in tasks}
    return pd.DataFrame([r for k, r in done.items() if k in keys]).drop(columns="_key")
