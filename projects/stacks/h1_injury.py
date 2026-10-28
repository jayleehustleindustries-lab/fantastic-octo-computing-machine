"""H1: do NFL players who carry an injury designation (and still play) under-hit their pick'em line?

Pre-registered before looking at results (Oct 22 2026):
- universe: REG weeks 2022-2025 (2026 reported separately as a fresh check), players who played;
- stand-in line = floor(trailing median of the prior <=8 games, >=3 required) + 0.5, same as corr.py;
- only line-worthy roles: QB pass_yds med>=150; WR/TE rec_yds med>=25 and receptions med>=2.5; RB rush_yds med>=25;
- groups from the public nflverse injury report for that week: Q = Questionable; LIMITED = not Q/D/Out but
  practice status Limited or DNP; NONE = not on the report;
- outcomes: MORE hit rate, dud rate (stat < half the trailing median), mean of stat / trailing mean;
- PASS = Q minus NONE MORE-hit diff < 0 with the 90% cluster-bootstrap CI (by game) entirely below 0 AND the sign
  holds in >= 3 of 4 seasons. Then: tag (INJ_TAG), ban from stacks, haircut = measured mean ratio.

usage: python h1_injury.py <nfl_props_dir> <injury_dir> <out.json>
"""
import json, sys
import numpy as np, pandas as pd

sys.path.insert(0, sys.argv[1])
from common import load_players  # noqa: E402

K, MINP, B, SEED = 8, 3, 2000, 7
MKTS = {"pass_yds": ("passing_yards", ["QB"], 150), "rec_yds": ("receiving_yards", ["WR", "TE"], 25),
        "receptions": ("receptions", ["WR", "TE"], 2.5), "rush_yds": ("rushing_yards", ["RB"], 25)}

pg = load_players()
fr = [pd.read_csv(f"{sys.argv[1]}/data/sp_{y}.csv", low_memory=False, usecols=["player_id", "season", "week",
                                                                               "season_type", "game_id"])
      for y in range(2022, 2027)]
gid = pd.concat(fr).query("season_type == 'REG'").drop(columns="season_type")
pg = pg.merge(gid, on=["player_id", "season", "week"], how="left").sort_values(["player_id", "season", "week"])

inj = pd.concat([pd.read_csv(f"{sys.argv[2]}/injuries_{y}.csv", low_memory=False) for y in range(2022, 2027)])
inj = inj[inj.game_type == "REG"].drop_duplicates(["season", "week", "gsis_id"], keep="last")
inj = inj.rename(columns={"gsis_id": "player_id"})[["season", "week", "player_id", "report_status", "practice_status"]]
pg = pg.merge(inj, on=["season", "week", "player_id"], how="left")
ps = pg.practice_status.fillna("")
pg["grp"] = np.where(pg.report_status.eq("Questionable"), "Q",
                     np.where(pg.report_status.isin(["Doubtful", "Out"]), "D_OUT",
                              np.where(ps.str.contains("Limited|Did Not", regex=True), "LIMITED", "NONE")))


def boot_diff(d, a, b, col):
    """90% CI for mean(col | grp a) - mean(col | grp b), resampling games."""
    rng = np.random.default_rng(SEED)
    g = d.groupby("game_id")
    sums = g.apply(lambda x: pd.Series({f"s{k}": x.loc[x.grp == k, col].sum() for k in (a, b)} |
                                       {f"n{k}": (x.grp == k).sum() for k in (a, b)}), include_groups=False)
    arr = sums.to_numpy(); n = len(arr); out = []
    for _ in range(B):
        t = arr[rng.integers(0, n, n)].sum(0)
        out.append(t[0] / t[2] - t[1] / t[3])
    return np.percentile(out, [5, 95]).round(4).tolist()


res = {}
for m, (col, pos, floor) in MKTS.items():
    d = pg[pg.pos.isin(pos)].copy()
    grp = d.groupby("player_id")[col]
    d["t_med"] = grp.transform(lambda s: s.shift(1).rolling(K, min_periods=MINP).median())
    d["t_mean"] = grp.transform(lambda s: s.shift(1).rolling(K, min_periods=MINP).mean())
    d = d[(d.t_med >= floor) & d.game_id.notna()]
    d["line"] = np.floor(d.t_med) + 0.5
    d["hit_more"] = (d[col] > d.line).astype(float)
    d["dud"] = (d[col] < 0.5 * d.t_med).astype(float)
    d["ratio"] = d[col] / d.t_mean
    out = {}
    for era, sub in (("2022-2025", d[d.season <= 2025]), ("2026", d[d.season == 2026])):
        row = {g: dict(n=int((sub.grp == g).sum()), more=round(sub.loc[sub.grp == g, "hit_more"].mean(), 4),
                       dud=round(sub.loc[sub.grp == g, "dud"].mean(), 4),
                       ratio=round(sub.loc[sub.grp == g, "ratio"].mean(), 4)) for g in ("NONE", "Q", "LIMITED")}
        if era == "2022-2025":
            row["Q_minus_NONE_more_ci90"] = boot_diff(sub, "Q", "NONE", "hit_more")
            row["Q_minus_NONE_dud_ci90"] = boot_diff(sub, "Q", "NONE", "dud")
            row["LIM_minus_NONE_more_ci90"] = boot_diff(sub, "LIMITED", "NONE", "hit_more")
            row["by_season_Q_minus_NONE_more"] = {
                int(s): round(x.loc[x.grp == "Q", "hit_more"].mean() - x.loc[x.grp == "NONE", "hit_more"].mean(), 4)
                for s, x in sub.groupby("season")}
        out[era] = row
    a = out["2022-2025"]
    neg = sum(v < 0 for v in a["by_season_Q_minus_NONE_more"].values())
    out["PASS"] = bool(a["Q_minus_NONE_more_ci90"][1] < 0 and neg >= 3)
    out["haircut_ratio_Q_over_NONE"] = round(a["Q"]["ratio"] / a["NONE"]["ratio"], 4)
    res[m] = out
    print(f"\n== {m} ==")
    for g in ("NONE", "Q", "LIMITED"):
        print(f"  {g:8s} n={a[g]['n']:6d}  MORE hit {a[g]['more']:.3f}  dud {a[g]['dud']:.3f}  "
              f"actual/trailing mean {a[g]['ratio']:.3f}")
    print(f"  Q-NONE MORE diff 90% CI {a['Q_minus_NONE_more_ci90']}  dud diff CI {a['Q_minus_NONE_dud_ci90']}  "
          f"LIMITED-NONE MORE CI {a['LIM_minus_NONE_more_ci90']}")
    print(f"  by season (Q-NONE MORE): {a['by_season_Q_minus_NONE_more']}  -> PASS={out['PASS']}")
    b = out["2026"]
    print(f"  2026 fresh: NONE n={b['NONE']['n']} more {b['NONE']['more']}  Q n={b['Q']['n']} more {b['Q']['more']}")
json.dump(res, open(sys.argv[3], "w"), indent=1)
