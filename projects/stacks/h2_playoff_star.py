"""H2: does the production WNBA points model under-project each team's top scorer in PLAYOFF games?

Pre-registered before looking at results (Oct 22 2026):
- rows: walk-forward backtest predictions (reports/backtest_rows.parquet, model context_glm_plus2si, points);
- rank = player's place on her team that game by trailing mean points over her prior <=10 games (no future data);
- test seasons 2021-2025 playoffs; 2026 playoffs reported separately as a fresh check;
- PASS needs all of: playoff rank-1 mean residual (actual - mu) > 0 with the 90% cluster-bootstrap CI (by game)
  clear of zero; positive in >= 4 of 5 seasons; AND a multiplicative bump mu*(1+b), with b fitted only on
  earlier seasons' playoff rank-1 rows, lowers NB NLL on the next season's playoff rank-1 rows in >= 4 of the
  4 scoreable seasons (2022-2025) and in aggregate (the j08 gate shape).
- regular-season rank-1 residual is shown as the control: a bias that is not playoff-specific is a different fix.

usage: python h2_playoff_star.py <oklahoma_dir> <out.json>
"""
import json, sys
import numpy as np, pandas as pd
from scipy import stats

OK = sys.argv[1]
B, SEED, MODEL = 2000, 11, "context_glm_plus2si"

pg = pd.read_parquet(f"{OK}/data/player_games.parquet").sort_values(["athlete_id", "tip"])
pg["t_pts"] = pg.groupby("athlete_id")["points"].transform(lambda s: s.shift(1).rolling(10, min_periods=3).mean())
pg["rank"] = pg.groupby(["game_id", "team_id"])["t_pts"].rank(ascending=False, method="first")
bt = pd.read_parquet(f"{OK}/reports/backtest_rows.parquet")
bt = bt[(bt.model == MODEL) & (bt.market == "points")]
d = bt.merge(pg[["game_id", "athlete_id", "rank"]], on=["game_id", "athlete_id"], how="left").dropna(subset=["rank"])
d["resid"] = d.actual - d.mu
d["grp"] = np.where(d["rank"] == 1, "rank1", np.where(d["rank"] == 2, "rank2", "rest"))


def ci(x, games):
    rng = np.random.default_rng(SEED)
    g = pd.DataFrame({"x": x.to_numpy(), "g": games.to_numpy()}).groupby("g")["x"].agg(["sum", "size"]).to_numpy()
    n = len(g)
    return np.percentile([(t := g[rng.integers(0, n, n)].sum(0))[0] / t[1] for _ in range(B)], [5, 95]).round(3).tolist()


def nll(y, mu, alpha):
    n = 1.0 / alpha
    return float(-stats.nbinom.logpmf(y, n, n / (n + mu)).mean())


out = {}
for po, name in ((True, "playoffs"), (False, "regular")):
    s = d[(d.playoffs == po) & d.season.between(2021, 2025)]
    out[name] = {g: dict(n=int((s.grp == g).sum()), mean_resid=round(s.loc[s.grp == g, "resid"].mean(), 3),
                         over_rate=round(s.loc[s.grp == g, "went_over"].mean(), 3),
                         p_over=round(s.loc[s.grp == g, "p_over"].mean(), 3)) for g in ("rank1", "rank2", "rest")}
    r1 = s[s.grp == "rank1"]
    out[name]["rank1_ci90"] = ci(r1.resid, r1.game_id)
    out[name]["rank1_by_season"] = {int(k): round(v, 3) for k, v in r1.groupby("season").resid.mean().items()}

# walk-forward bump: b from earlier playoff rank-1 rows only (ratio of sums - 1), scored on the next season
p1 = d[d.playoffs & (d.grp == "rank1")]
gate = {}
for season in range(2022, 2026):
    tr, te = p1[p1.season < season], p1[p1.season == season]
    b = tr.actual.sum() / tr.mu.sum() - 1
    gate[season] = dict(b=round(b, 4), n=len(te), nll_base=round(nll(te.actual, te.mu, te.alpha), 4),
                        nll_bump=round(nll(te.actual, te.mu * (1 + b), te.alpha), 4))
agg_base = np.mean([v["nll_base"] for v in gate.values()])
agg_bump = np.mean([v["nll_bump"] for v in gate.values()])
wins = sum(v["nll_bump"] < v["nll_base"] for v in gate.values())
po = out["playoffs"]
pos = sum(v > 0 for v in po["rank1_by_season"].values())
out["walk_forward_gate"] = gate
out["PASS"] = bool(po["rank1_ci90"][0] > 0 and pos >= 4 and wins >= 4 and agg_bump < agg_base)
f26 = d[d.playoffs & (d.season == 2026)]
out["fresh_2026_playoffs"] = {g: dict(n=int((f26.grp == g).sum()), mean_resid=round(f26.loc[f26.grp == g, "resid"].mean(), 3))
                              for g in ("rank1", "rank2", "rest")}

for name in ("playoffs", "regular"):
    o = out[name]
    print(f"== {name} 2021-2025 ==")
    for g in ("rank1", "rank2", "rest"):
        print(f"  {g:6s} n={o[g]['n']:6d}  mean actual-proj {o[g]['mean_resid']:+.2f}  over rate {o[g]['over_rate']:.3f} "
              f"vs model p_over {o[g]['p_over']:.3f}")
    print(f"  rank1 90% CI {o['rank1_ci90']}  by season {o['rank1_by_season']}")
print("walk-forward bump gate:", gate)
print(f"aggregate NLL base {agg_base:.4f} vs bump {agg_bump:.4f}; bump wins {wins}/4 seasons -> PASS={out['PASS']}")
print("2026 playoffs fresh:", out["fresh_2026_playoffs"])
json.dump(out, open(sys.argv[2], "w"), indent=1)
