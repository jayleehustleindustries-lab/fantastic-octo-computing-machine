"""J03: game-clustered bootstrap. How much of each model gain is real, and is calibration really off?

Resamples whole games (players in one game are not independent). Reports CIs for
 (1) mean nll difference between models, (2) calibration slope of p_over. Needs reports/backtest_rows.parquet.
Gate: a model claim stands only if its 95% CI excludes zero.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from jobs import common as C


def weighted_logit_slope(x, y, w, iters=12):
    """Newton for logistic regression y ~ a + b*x with row weights. Returns (a, b)."""
    X = np.column_stack([np.ones_like(x), x]); beta = np.array([0.0, 1.0])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(X @ beta))); g = X.T @ (w * (y - p))
        H = (X * (w * p * (1 - p))[:, None]).T @ X + 1e-9 * np.eye(2)
        beta = beta + np.linalg.solve(H, g)
    return beta


def main():
    ap = C.parser(__doc__); ap.add_argument("--reps", type=int, default=2000); args = ap.parse_args()
    reps = 100 if args.quick else args.reps
    r = pd.read_parquet(C.ROOT / "reports" / "backtest_rows.parquet")
    if args.quick:
        r = r[r.season.isin(C.seasons(args))]
    rng = np.random.default_rng(5); out = []
    for market, d in r.groupby("market"):
        pv = d.pivot_table(index=["season", "game_id", "athlete_id"], columns="model", values="nll")
        games = pv.index.get_level_values("game_id").to_numpy()
        gid, inv = np.unique(games, return_inverse=True); G = len(gid)
        for a, b in [("context_glm_plus2", "context_glm_plus"), ("context_glm_plus", "context_glm"), ("context_glm_plus2", "season_avg")]:
            if a not in pv or b not in pv:
                continue
            diff = (pv[a] - pv[b]).to_numpy()
            s = np.bincount(inv, weights=diff, minlength=G); n = np.bincount(inv, minlength=G).astype(float)
            idx = rng.integers(0, G, (reps, G))
            boot = s[idx].sum(1) / n[idx].sum(1)
            out.append({"market": market, "comparison": f"{a} - {b}", "mean_nll_diff": diff.mean(),
                        "ci_lo": np.quantile(boot, .025), "ci_hi": np.quantile(boot, .975)})
        m = d[d.model == "context_glm_plus2"].sort_values(["season", "game_id", "athlete_id"])
        x = np.log(m.p_over.clip(1e-4, 1 - 1e-4) / (1 - m.p_over.clip(1e-4, 1 - 1e-4))).to_numpy(); y = m.went_over.to_numpy(float)
        ginv = np.unique(m.game_id.to_numpy(), return_inverse=True)[1]; G2 = ginv.max() + 1
        slopes = []
        for _ in range(reps // 4):
            cnt = np.bincount(rng.integers(0, G2, G2), minlength=G2)
            slopes.append(weighted_logit_slope(x, y, cnt[ginv].astype(float))[1])
        out.append({"market": market, "comparison": "calibration_slope", "mean_nll_diff": np.mean(slopes),
                    "ci_lo": np.quantile(slopes, .025), "ci_hi": np.quantile(slopes, .975)})
    df = pd.DataFrame(out).round(4); C.OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(C.OUT / "j03_bootstrap.csv", index=False); print(df.to_string(index=False))


if __name__ == "__main__":
    main()
