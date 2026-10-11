"""J06: model minutes directly (quantile gradient boosting + CQR band). Minutes drive most big misses (Game 1: Gray/Hayes/Loyd).

Compares p10/p50/p90 minutes (oklahoma/minutes.MinutesModel) to the min_ewm baseline: MAE of the median,
and coverage of the conformalized 10-90 band, overall and for bench / starters (by starter_prev) / playoffs.
The earlier run read the game's own `starter` flag (known only at tip); that leaky version is kept in
reports/jobs/j06_minutes_leaky.csv. This one uses starter_prev only.
Gate: MAE gain >= 0.30 min in >= 5 of 6 seasons AND pooled 10-90 coverage 78-82% with every season in 76-84%.

Seeds: a fit's seed changes the early-stopping validation split, and the 5-of-6 season gain sits close to the
0.30 line, so a single seed can pass or fail by luck. `--seeds N` runs seeds 0..N-1 (seed 0 is the old single
run), averages every per-season and pooled metric across them, and applies the gate to the averages. The per-seed
pooled numbers and per-seed gate results are written next to it so the spread is visible.
Output: reports/jobs/j06_minutes.csv (per season, seed-averaged), j06_minutes_summary.csv (pooled, seed-averaged),
j06_minutes_seeds.csv (one row per seed, with its per-season gains), j06_minutes_gate.json (--quick writes *_quick files so a smoke test
never overwrites the full run).
"""
from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from itertools import repeat

import numpy as np
import pandas as pd

from jobs import common as C
from oklahoma.minutes import MinutesModel


def season_row(s: int, train: pd.DataFrame, test: pd.DataFrame, max_iter: int, seed: int = 0) -> tuple[dict, pd.DataFrame]:
    model = MinutesModel(max_iter=max_iter, seed=seed).fit(train)
    q = model.predict(test)
    y = test["minutes"].to_numpy()
    base = test["min_ewm"].fillna(test["min_ewm"].median()).to_numpy()
    inside = ((y >= q["min_p10"]) & (y <= q["min_p90"])).to_numpy()
    sub = {"bench": ~test["starter_prev"].to_numpy(), "starters": test["starter_prev"].to_numpy(),
           "playoffs": test["playoffs"].to_numpy()}
    row = {"season": s, "n": len(test), "mae_gbm": np.abs(y - q["min_p50"]).mean(), "mae_baseline": np.abs(y - base).mean(),
           "coverage_10_90": inside.mean(), "below_p10": (y < q["min_p10"]).mean(), "above_p90": (y > q["min_p90"]).mean(),
           "cqr_shift": model.shift_, "oof_raw_coverage": model.oof_raw_coverage_}
    for name, m in sub.items():
        row[f"n_{name}"] = int(m.sum())
        row[f"cov_{name}"] = inside[m].mean() if m.any() else np.nan
    rows = test[["game_id", "athlete_id", "season", "starter_prev", "playoffs"]].assign(
        minutes=y, min_ewm=base, **q.to_dict("series"))
    return row, rows


def gate(per_season: pd.DataFrame, pooled_cov: float) -> dict:
    n_gain = int((per_season["mae_gain"] >= 0.30).sum())
    ok_gain = n_gain >= 5 if len(per_season) == 6 else n_gain == len(per_season)
    ok_pooled = bool(0.78 <= pooled_cov <= 0.82)
    ok_seasons = bool(per_season["coverage_10_90"].between(0.76, 0.84).all())
    return {"seasons_with_gain_ge_0.30": n_gain, "n_seasons": len(per_season), "pooled_coverage": round(float(pooled_cov), 4),
            "gain_ok": bool(ok_gain), "pooled_coverage_ok": ok_pooled, "season_coverage_ok": ok_seasons,
            "passed": bool(ok_gain and ok_pooled and ok_seasons)}


def run_seed(seed: int, seasons: list[int], quick: bool) -> tuple[pd.DataFrame, dict]:
    """Walk-forward over `seasons` with one seed -> (per-season table, pooled metrics)."""
    f = C.features(); f = f[(f.career_games >= 5)]
    rows, preds = [], []
    for s in seasons:
        train, test = f[(f.season < s) & (f.season >= s - 5)], f[f.season == s]
        assert train["season"].max() < s                      # walk-forward: never train on the scored season
        if quick:
            train = train.sample(min(len(train), 4000), random_state=1)
        row, p = season_row(s, train, test, max_iter=60 if quick else 250, seed=seed)
        rows.append(row); preds.append(p)
        print(f"[j06] seed {seed} season {s} done", flush=True)
    out = pd.DataFrame(rows); out["mae_gain"] = out.mae_baseline - out.mae_gbm
    allp = pd.concat(preds)
    inside = (allp.minutes >= allp.min_p10) & (allp.minutes <= allp.min_p90)
    pooled = {"mae_gbm": np.abs(allp.minutes - allp.min_p50).mean(), "mae_baseline": np.abs(allp.minutes - allp.min_ewm).mean(),
              "coverage_10_90": inside.mean(), "n": len(allp)}
    pooled["mae_gain"] = pooled["mae_baseline"] - pooled["mae_gbm"]
    for name, m in {"bench": ~allp.starter_prev, "starters": allp.starter_prev, "playoffs": allp.playoffs}.items():
        pooled[f"cov_{name}"] = inside[m].mean(); pooled[f"n_{name}"] = int(m.sum())
    return out, {k: float(v) for k, v in pooled.items()}


def combine(results: list[tuple[pd.DataFrame, dict]]) -> tuple[pd.DataFrame, dict, pd.DataFrame, dict]:
    """Average the per-seed (per-season table, pooled metrics) pairs -> (per-season, pooled, per-seed table, gate).

    The gate is applied to the seed-averaged numbers; the per-seed table shows each seed's pooled numbers and
    whether that seed alone would have passed."""
    out = pd.concat([r[0] for r in results]).groupby("season", as_index=False).mean()
    out = out.astype({c: int for c in out.columns if c == "n" or c.startswith("n_")})   # counts are identical across seeds
    pooled = pd.DataFrame([r[1] for r in results]).mean().to_dict()
    per_seed = []
    for seed, (tab, pool) in enumerate(results):
        gs = gate(tab, pool["coverage_10_90"])
        by_season = {f"gain_{int(r.season)}": r.mae_gain for r in tab.itertuples()}
        per_seed.append({"seed": seed, **{k: pool[k] for k in ("mae_gbm", "mae_baseline", "mae_gain", "coverage_10_90")},
                         "seasons_with_gain_ge_0.30": gs["seasons_with_gain_ge_0.30"], "passed": gs["passed"], **by_season})
    per_seed = pd.DataFrame(per_seed)
    g = {**gate(out, pooled["coverage_10_90"]), "n_seeds": len(results), "seeds_passing": int(per_seed["passed"].sum()),
         "pooled_mae_gain_by_seed": [round(float(x), 4) for x in per_seed["mae_gain"]],
         "pooled_coverage_by_seed": [round(float(x), 4) for x in per_seed["coverage_10_90"]]}
    out["n_seeds"] = pooled["n_seeds"] = len(results)
    return out, pooled, per_seed, g


def main():
    ap = C.parser(__doc__)
    ap.add_argument("--seeds", type=int, default=1, help="average over seeds 0..N-1 (the gate is applied to the averages)")
    args = ap.parse_args()
    seasons, seeds = C.seasons(args), list(range(args.seeds))
    workers = min(args.workers, len(seeds))
    if workers > 1:                                           # seeds are independent, so they parallelise cleanly
        with ProcessPoolExecutor(workers) as ex:
            results = list(ex.map(run_seed, seeds, repeat(seasons), repeat(args.quick)))
    else:
        results = [run_seed(sd, seasons, args.quick) for sd in seeds]
    out, pooled, per_seed, g = combine(results)

    C.OUT.mkdir(parents=True, exist_ok=True)
    tag = "_quick" if args.quick else ""
    out.round(3).to_csv(C.OUT / f"j06_minutes{tag}.csv", index=False)
    pd.DataFrame([pooled]).round(4).to_csv(C.OUT / f"j06_minutes_summary{tag}.csv", index=False)
    per_seed.round(4).to_csv(C.OUT / f"j06_minutes_seeds{tag}.csv", index=False)
    (C.OUT / f"j06_minutes_gate{tag}.json").write_text(json.dumps(g, indent=2) + "\n")
    print(out.round(3).to_string(index=False))
    print("per seed:\n" + per_seed.round(4).to_string(index=False))
    print(f"pooled (mean of {len(seeds)} seeds):", {k: round(float(v), 4) for k, v in pooled.items()})
    print("gate:", g)


if __name__ == "__main__":
    main()
