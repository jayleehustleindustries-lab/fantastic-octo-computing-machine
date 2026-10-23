"""J04: walk-forward test of the 3PM model against a rate x minutes baseline. Output: reports/jobs/j04_threes.csv."""
from __future__ import annotations

import numpy as np
import pandas as pd

from jobs import common as C
from oklahoma import ingest, threes
from oklahoma.models import MU_FLOOR, log_pmf


def main():
    args = C.parser(__doc__).parse_args()
    f = C.features()
    g = pd.read_parquet(ingest.GAMES_PATH)
    d = f.merge(threes.three_features(g), on=["game_id", "athlete_id"], how="left")
    if "threes_made" not in d:   # features may already carry the box-score columns
        d = d.merge(g[["game_id", "athlete_id", "threes_made", "threes_attempted"]], on=["game_id", "athlete_id"], how="left")
    d = d[(d.career_games >= 5) & d.threes_made.notna()]
    rows = []
    for s in C.seasons(args):
        train, test = d[(d.season < s) & (d.season >= s - 5)], d[d.season == s]
        if train.empty or test.empty:
            continue
        m = threes.ThreesModel().fit(train)
        mu = m.predict_mean(test); y = test.threes_made.to_numpy()
        base = np.maximum((test.mk_pm_ewm.fillna(train.mk_pm_ewm.median()) * test.min_ewm).to_numpy(), MU_FLOOR)
        ba = np.sqrt(np.mean((y - base) ** 2))
        from oklahoma.models import fit_alpha
        a_b = fit_alpha(train.threes_made.to_numpy(), np.maximum((train.mk_pm_ewm.fillna(train.mk_pm_ewm.median()) * train.min_ewm).to_numpy(), MU_FLOOR))
        rows.append({"season": s, "n": len(test), "nll_model": float(-log_pmf(y, mu, m.alpha_).mean()),
                     "nll_baseline": float(-log_pmf(y, base, a_b).mean()),
                     "mae_model": float(np.abs(y - mu).mean()), "mae_baseline": float(np.abs(y - base).mean())})
    out = pd.DataFrame(rows).round(4); out["gain"] = (out.nll_baseline - out.nll_model).round(4)
    C.OUT.mkdir(parents=True, exist_ok=True); out.to_csv(C.OUT / "j04_threes.csv", index=False); print(out.to_string(index=False))


if __name__ == "__main__":
    main()
