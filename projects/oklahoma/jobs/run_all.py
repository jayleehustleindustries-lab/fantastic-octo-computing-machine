"""Run the heavy jobs in order, resumable. Usage:
    python -m jobs.run_all --quick            # 5-minute smoke test of everything
    python -m jobs.run_all --workers 8        # the real run
    python -m jobs.run_all --only j01,j05     # a subset
A job whose output csv already exists is skipped unless --force. Logs: reports/jobs/run.log
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time

from jobs import common as C

ORDER = [  # (id, module, output file that marks it done)
    ("backtest", "oklahoma.backtest", "../backtest_rows.parquet"),
    ("j03", "jobs.j03_bootstrap", "j03_bootstrap.csv"),
    ("j04", "jobs.j04_threes", "j04_threes.csv"),
    ("j06", "jobs.j06_minutes", "j06_minutes.csv"),
    ("j02", "jobs.j02_joint_calibration", "j02_joint.csv"),
    ("j01", "jobs.j01_ablation", "j01_ablation_summary.csv"),
    ("j07", "jobs.j07_gbm_mean", "j07_gbm.csv"),
    ("j05", "jobs.j05_hyperparams", "j05_hyperparams.csv"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--workers", type=int, default=3); ap.add_argument("--quick", action="store_true")
    ap.add_argument("--force", action="store_true"); ap.add_argument("--only", default="")
    a = ap.parse_args()
    C.OUT.mkdir(parents=True, exist_ok=True); log = (C.OUT / "run.log").open("a")
    only = set(a.only.split(",")) - {""}
    for jid, mod, out in ORDER:
        if only and jid not in only:
            continue
        if not a.quick and not a.force and (C.OUT / out).exists():
            print(f"skip {jid} (output exists)"); continue
        cmd = [sys.executable, "-m", mod] + (["--quick"] if a.quick and jid != "backtest" else [])
        if jid not in ("backtest", "j03", "j04", "j06", "j07"):
            cmd += ["--workers", str(a.workers)]
        if jid == "backtest" and a.quick:
            cmd += ["--test-seasons", "2025-2026", "--models", "context_glm,context_glm_plus,context_glm_plus2,season_avg"]
        t0 = time.time(); print(f"== {jid}: {' '.join(cmd)}", flush=True)
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
        print(f"   {'ok' if r.returncode == 0 else 'FAILED'} in {time.time() - t0:.0f}s", flush=True)
        if r.returncode != 0:
            print(f"   see {C.OUT / 'run.log'}; fix and re-run (finished jobs are skipped)"); sys.exit(1)


if __name__ == "__main__":
    main()
