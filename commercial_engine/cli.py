"""Operator CLI.

  python -m commercial_engine.cli validate jobcommand_v2.csv
  python -m commercial_engine.cli enqueue jobcommand_v2.csv [--video CK-01]
  python -m commercial_engine.cli render-next
  python -m commercial_engine.cli status JOB_ID
  python -m commercial_engine.cli approve JOB_ID --by "Your Name"
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .config import settings
from .jobs import enqueue
from .manifest import ManifestError, parse_manifest, resolve_manifest_path
from .state import IllegalTransition, Store
from .worker import run_once


def _missing_footage(manifest: str) -> list[str]:
    missing = []
    for c in parse_manifest(resolve_manifest_path(manifest)):
        for s in c.scenes:
            folder = {"broll": settings.broll_dir, "screen_recording": settings.screen_recordings_dir}.get(s.source)
            if folder and not (Path(folder) / f"{s.scene_id}.mp4").is_file():
                missing.append(f"{s.source}: {folder}/{s.scene_id}.mp4")
    return missing


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="commercial_engine")
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate"); v.add_argument("manifest")
    e = sub.add_parser("enqueue"); e.add_argument("manifest"); e.add_argument("--video", action="append")
    sub.add_parser("render-next")
    s = sub.add_parser("status"); s.add_argument("job_id")
    a = sub.add_parser("approve"); a.add_argument("job_id"); a.add_argument("--by", required=True); a.add_argument("--note")
    args = ap.parse_args(argv)

    try:
        if args.cmd == "validate":
            commercials = parse_manifest(resolve_manifest_path(args.manifest))
            for c in commercials:
                print(f"{c.video_id}  {c.concept_name}  [{c.trade}]  " + " | ".join(f"{x.scene_num}:{x.source}" for x in c.scenes))
            missing = _missing_footage(args.manifest)
            for m in missing:
                print(f"  MISSING {m}")
            print("OK" if not missing else f"manifest valid; {len(missing)} footage file(s) still needed before render")
            return 0
        store = Store(settings.database_path)
        if args.cmd == "enqueue":
            print(json.dumps(enqueue(store, args.manifest, args.video), indent=2))
        elif args.cmd == "render-next":
            result = asyncio.run(run_once(store))
            print(json.dumps(result, indent=2, default=str) if result else "no queued jobs")
            return 0 if not result or result["status"] != "failed" else 1
        elif args.cmd == "status":
            print(json.dumps({"job": store.get_job(args.job_id), "scenes": store.scenes(args.job_id)}, indent=2, default=str))
        elif args.cmd == "approve":
            print(json.dumps(store.approve(args.job_id, approved_by=args.by, note=args.note), indent=2, default=str))
    except ManifestError as exc:
        for p in exc.problems:
            print(f"ERROR {p}", file=sys.stderr)
        return 2
    except IllegalTransition as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
