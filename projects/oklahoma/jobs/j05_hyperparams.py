"""J05: sweep the knobs we hard-coded (EWM half-life, opponent shrink, rotation threshold, train window, ridge).

Each config rebuilds features (slow) so this is the most expensive job. Output: reports/jobs/j05_hyperparams.csv
Gate: adopt a config only if it beats the current default by > 0.001 mean nll AND wins in most seasons.
"""
from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

from jobs import common as C
from oklahoma import features as F, ingest
from oklahoma.features import STATS, build_features
from oklahoma.models import ContextGLMPlus2, log_pmf


def task(t: dict) -> dict:
    F.EWM_HALFLIFE, F.OPP_SHRINK, F.ROTATION_MIN = t["halflife"], t["opp_shrink"], t["rotation_min"]
    f = build_features(pd.read_parquet(ingest.GAMES_PATH))
    out = {}
    for market in t["markets"]:
        el = C.eligible(f, market)
        vals = []
        for s in t["seasons"]:
            train, test = C.split(el, s, t["window"])
            m = ContextGLMPlus2(market).fit(train)
            mu = m.predict_mean(test)
            vals.append(float(-log_pmf(test[market].to_numpy(), mu, m.alpha_for(mu)).mean()))
        out[f"nll_{market}"] = float(np.mean(vals)); out[f"seasons_{market}"] = vals
    return out


def main():
    ap = C.parser(__doc__); args = ap.parse_args()
    grid = dict(halflife=[3, 5, 8, 12], opp_shrink=[75.0, 150.0, 300.0], rotation_min=[8.0, 12.0, 16.0], window=[3, 5, 8])
    if args.quick:
        grid = dict(halflife=[5, 8], opp_shrink=[150.0], rotation_min=[12.0], window=[5])
    markets = ["points"] if args.quick else STATS
    tasks = [dict(zip(grid, v), markets=markets, seasons=C.seasons(args)) for v in itertools.product(*grid.values())]
    df = C.run_tasks("j05_hyperparams", tasks, task, args.workers)
    df["mean_nll"] = df[[f"nll_{m}" for m in markets]].mean(axis=1)
    df = df.sort_values("mean_nll")
    df.drop(columns=[c for c in df if c.startswith("seasons_")]).to_csv(C.OUT / "j05_hyperparams.csv", index=False)
    print(df[["halflife", "opp_shrink", "rotation_min", "window", "mean_nll"]].head(15).to_string(index=False))


if __name__ == "__main__":
    main()
