"""J01: leave-one-feature-group-out ablation. Which inputs earn their place, per market and season?

Decision gate: a group whose removal raises nll by < 0.0005 in most market-seasons is a candidate to drop
(simpler model, less overfit). Output: reports/jobs/j01_ablation.csv
"""
from __future__ import annotations

import numpy as np

from jobs import common as C
from oklahoma.features import STATS
from oklahoma.models import ContextGLMPlus2, log_pmf

# column index in ContextGLMPlus2._design
GROUPS = {
    "none": [], "teammates_out": [11, 12], "schedule": [13, 15], "returning": [14], "hot_streak": [16],
    "usage": [17], "pace": [18], "opp_defense": [5], "home": [6], "playoffs": [7], "rookie": [8],
    "rest_b2b": [9], "career_games": [10], "minutes_l5": [4], "career_rate": [2], "season_rate": [1],
}


def _model(market: str, drop: list[int]):
    class A(ContextGLMPlus2):
        def _design(self, df):
            X = super()._design(df)
            return X[:, [i for i in range(X.shape[1]) if i not in drop]]
    return A(market)


def task(t: dict) -> dict:
    f = C.features()
    el = C.eligible(f, t["market"])
    train, test = C.split(el, t["season"])
    m = _model(t["market"], GROUPS[t["group"]]).fit(train)
    mu = m.predict_mean(test)
    nll = float(-log_pmf(test[t["market"]].to_numpy(), mu, m.alpha_for(mu)).mean())
    return {"nll": nll, "n": int(len(test))}


def main():
    ap = C.parser(__doc__); args = ap.parse_args()
    groups = list(GROUPS)[:3] if args.quick else list(GROUPS)
    markets = ["points"] if args.quick else STATS
    tasks = [{"market": m, "season": s, "group": g} for m in markets for s in C.seasons(args) for g in groups]
    C.features()   # build once before forking
    df = C.run_tasks("j01_ablation", tasks, task, args.workers)
    base = df[df.group == "none"].set_index(["market", "season"])["nll"]
    df["delta_nll"] = df.apply(lambda r: r.nll - base[(r.market, r.season)], axis=1)
    summ = df[df.group != "none"].groupby(["group", "market"]).agg(mean_delta=("delta_nll", "mean"),
                                                                  seasons_worse=("delta_nll", lambda s: int((s > 0.0005).sum())),
                                                                  n=("delta_nll", "size")).round(5)
    df.to_csv(C.OUT / "j01_ablation.csv", index=False)
    print(summ.to_string()); summ.to_csv(C.OUT / "j01_ablation_summary.csv")


if __name__ == "__main__":
    main()
