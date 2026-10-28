"""Same-game correlation for pick'em stacks (NFL + WNBA). Research only; nothing places bets.

Question: when two legs from the same game are both set at a 50/50 line, how often do they win TOGETHER,
compared with the independent product a pick'em payout assumes?

Leak-free by construction:
- roles (QB, WR1, WR2, TE1, RB1; WNBA top-2 scorers) come from PRIOR games only (trailing usage);
- the stand-in "pick'em line" for each leg is floor(trailing median of the prior <=8 / <=10 games) + 0.5;
- the only current-game information used is that the player appeared (actives are known pre-game).

Output per pair type: n games, Spearman rho of (stat - trailing mean), its latent-normal equivalent,
P(over,over), P(under,under), P(over,under), the lift vs independence, and a bootstrap 90% CI of P(same side),
where "same side" = the better of over/over and under/under as a slip would be built.

usage: python corr.py <nfl_props_dir> <oklahoma_dir> <out.json>
"""
import json, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr

NFL, OK, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
RNG = np.random.default_rng(7)


def trailing(df, key, col, k, minp):
    g = df.groupby(key)[col]
    mean = g.transform(lambda s: s.shift(1).rolling(k, min_periods=minp).mean())
    med = g.transform(lambda s: s.shift(1).rolling(k, min_periods=minp).median())
    return mean, np.floor(med) + 0.5


def summarize(name, a, b, la, lb, game, extra=None):
    """a, b: stats; la, lb: stand-in lines; game: cluster id for the bootstrap."""
    m = ~(np.isnan(a) | np.isnan(b) | np.isnan(la) | np.isnan(lb))
    a, b, la, lb, game = a[m], b[m], la[m], lb[m], game[m]
    oa, ob = a > la, b > lb
    oo, uu, ou = (oa & ob).mean(), (~oa & ~ob).mean(), (oa & ~ob).mean()
    pa, pb = oa.mean(), ob.mean()
    same = np.maximum(oo, uu)
    # cluster bootstrap over games
    g = pd.factorize(game)[0]
    ng = g.max() + 1
    idx = [np.flatnonzero(g == i) for i in range(ng)]
    boots = []
    for _ in range(400):
        pick = np.concatenate([idx[i] for i in RNG.integers(0, ng, ng)])
        boots.append(((oa[pick] & ob[pick]).mean(), (~oa[pick] & ~ob[pick]).mean()))
    boots = np.array(boots)
    rs = spearmanr(a - la, b - lb).correlation if len(a) > 10 else np.nan
    out = dict(pair=name, n=int(len(a)), p_a_over=round(pa, 3), p_b_over=round(pb, 3),
               p_over_over=round(oo, 3), p_under_under=round(uu, 3), p_over_under=round(ou, 3),
               indep_over_over=round(pa * pb, 3), lift_over_over=round(oo / (pa * pb), 3) if pa * pb else None,
               spearman=round(float(rs), 3), latent_rho=round(float(2 * np.sin(np.pi * rs / 6)), 3),
               ci90_over_over=[round(float(x), 3) for x in np.percentile(boots[:, 0], [5, 95])],
               ci90_under_under=[round(float(x), 3) for x in np.percentile(boots[:, 1], [5, 95])],
               same_side_best=round(float(same), 3))
    if extra:
        out.update(extra)
    return out


def trio(name, a, b, c, la, lb, lc, game):
    m = ~np.isnan(np.c_[a, b, c, la, lb, lc]).any(axis=1)
    a, b, c, la, lb, lc, game = a[m], b[m], c[m], la[m], lb[m], lc[m], game[m]
    o = (a > la) & (b > lb) & (c > lc)
    u = (a < la) & (b < lb) & (c < lc)
    g = pd.factorize(game)[0]
    ng = g.max() + 1
    idx = [np.flatnonzero(g == i) for i in range(ng)]
    bo, bu = [], []
    for _ in range(400):
        pick = np.concatenate([idx[i] for i in RNG.integers(0, ng, ng)])
        bo.append(o[pick].mean()); bu.append(u[pick].mean())
    pa, pb, pc = (a > la).mean(), (b > lb).mean(), (c > lc).mean()
    return dict(pair=name, n=int(len(a)), p_all_over=round(o.mean(), 3), p_all_under=round(u.mean(), 3),
                indep_all_over=round(pa * pb * pc, 3),
                ci90_all_over=[round(float(x), 3) for x in np.percentile(bo, [5, 95])],
                ci90_all_under=[round(float(x), 3) for x in np.percentile(bu, [5, 95])])


# ------------------------------------------------------------------ NFL
sys.path.insert(0, NFL)
import common  # noqa: E402

pg = common.load_players().sort_values(["player_id", "season", "week"]).reset_index(drop=True)
for c in ["attempts", "passing_yards", "passing_tds", "carries", "rushing_yards", "targets", "receptions", "receiving_yards"]:
    pg[c] = pg[c].fillna(0.0)
pg["gkey"] = pg.season.astype(str) + "-" + pg.week.astype(str) + "-" + pg.team
pg["game"] = pg.season.astype(str) + "-" + pg.week.astype(str) + "-" + pg[["team", "opponent_team"]].min(axis=1)
K, MINP = 8, 3
for col in ["attempts", "carries", "targets"]:
    pg[f"u_{col}"] = pg.groupby("player_id")[col].transform(lambda s: s.shift(1).rolling(K, min_periods=MINP).mean())
for col in ["passing_yards", "passing_tds", "rushing_yards", "receiving_yards", "receptions"]:
    pg[f"m_{col}"], pg[f"l_{col}"] = trailing(pg, "player_id", col, K, MINP)

# roles from prior usage among players who appeared
qb = pg[(pg.pos == "QB") & (pg.attempts > 0)].sort_values("u_attempts", ascending=False).drop_duplicates("gkey")
rb = pg[pg.pos == "RB"].sort_values("u_carries", ascending=False).drop_duplicates("gkey")
rec = pg[pg.pos.isin(["WR", "TE"])].sort_values("u_targets", ascending=False)
rec = rec[rec.u_targets.notna()]
rec["rk"] = rec.groupby("gkey").cumcount() + 1
wr1, wr2 = rec[rec.rk == 1], rec[rec.rk == 2]
te1 = pg[pg.pos == "TE"].sort_values("u_targets", ascending=False).drop_duplicates("gkey")
te1 = te1[te1.u_targets.notna()]


def j(left, right, lsuf, rsuf, on="gkey"):
    cols = ["gkey", "game", "passing_yards", "passing_tds", "rushing_yards", "receiving_yards", "receptions",
            "l_passing_yards", "l_passing_tds", "l_rushing_yards", "l_receiving_yards", "l_receptions", "name", "opponent_team", "team", "season", "week"]
    return left[cols].merge(right[cols], on=on, suffixes=(lsuf, rsuf))


nfl = []
for nm, other in (("WR1", wr1), ("WR2", wr2), ("TE1", te1)):
    x = j(qb, other, "_q", "_r")
    nfl.append(summarize(f"NFL QB pass_yds + {nm} rec_yds", x.passing_yards_q.values, x.receiving_yards_r.values,
                         x.l_passing_yards_q.values, x.l_receiving_yards_r.values, x.game_q.values))
x = j(qb, wr1, "_q", "_r")
nfl.append(summarize("NFL QB pass_tds + WR1 rec_yds", x.passing_tds_q.values, x.receiving_yards_r.values,
                     x.l_passing_tds_q.values, x.l_receiving_yards_r.values, x.game_q.values))
nfl.append(summarize("NFL QB pass_yds + WR1 receptions", x.passing_yards_q.values, x.receptions_r.values,
                     x.l_passing_yards_q.values, x.l_receptions_r.values, x.game_q.values))
x = j(qb, rb, "_q", "_r")
nfl.append(summarize("NFL QB pass_yds + RB1 rush_yds", x.passing_yards_q.values, x.rushing_yards_r.values,
                     x.l_passing_yards_q.values, x.l_rushing_yards_r.values, x.game_q.values))
x = j(wr1, wr2, "_a", "_b")
nfl.append(summarize("NFL WR1 rec_yds + WR2 rec_yds", x.receiving_yards_a.values, x.receiving_yards_b.values,
                     x.l_receiving_yards_a.values, x.l_receiving_yards_b.values, x.game_a.values))
nfl.append(summarize("NFL WR1 rec_yds + WR1 receptions (same player)", wr1.receiving_yards.values, wr1.receptions.values,
                     wr1.l_receiving_yards.values, wr1.l_receptions.values, wr1.game.values))
q2 = qb[["game", "gkey", "passing_yards", "l_passing_yards", "team"]]
x = q2.merge(q2, on="game", suffixes=("_a", "_b"))
x = x[x.team_a < x.team_b]
nfl.append(summarize("NFL QB pass_yds + OPP QB pass_yds", x.passing_yards_a.values, x.passing_yards_b.values,
                     x.l_passing_yards_a.values, x.l_passing_yards_b.values, x.game.values))
x = j(qb, wr1, "_q", "_r").merge(wr2[["gkey", "receiving_yards", "l_receiving_yards"]], on="gkey")
nfl_trios = [trio("NFL QB pass_yds + WR1 + WR2 rec_yds", x.passing_yards_q.values, x.receiving_yards_r.values, x.receiving_yards.values,
                  x.l_passing_yards_q.values, x.l_receiving_yards_r.values, x.l_receiving_yards.values, x.game_q.values)]
x = j(qb, wr1, "_q", "_r").merge(te1[["gkey", "receiving_yards", "l_receiving_yards"]], on="gkey")
nfl_trios.append(trio("NFL QB pass_yds + WR1 + TE1 rec_yds", x.passing_yards_q.values, x.receiving_yards_r.values, x.receiving_yards.values,
                      x.l_passing_yards_q.values, x.l_receiving_yards_r.values, x.l_receiving_yards.values, x.game_q.values))

# ------------------------------------------------------------------ WNBA
w = pd.read_parquet(f"{OK}/data/player_games.parquet")
w = w[w.season >= 2020].sort_values(["athlete_id", "tip"]).reset_index(drop=True)
for col in ["points", "rebounds", "assists"]:
    w[f"m_{col}"], w[f"l_{col}"] = trailing(w, "athlete_id", col, 10, 4)
w["u_min"] = w.groupby("athlete_id")["minutes"].transform(lambda s: s.shift(1).rolling(10, min_periods=4).mean())
w["u_pts"] = w["m_points"]
w["tkey"] = w.game_id.astype(str) + "-" + w.team_id.astype(str)
core = w[(w.u_min >= 20)]
wn = [summarize("WNBA same player points + rebounds", core.points.values, core.rebounds.values,
                core.l_points.values, core.l_rebounds.values, core.game_id.values),
      summarize("WNBA same player points + assists", core.points.values, core.assists.values,
                core.l_points.values, core.l_assists.values, core.game_id.values)]
top = w[w.u_pts.notna()].sort_values("u_pts", ascending=False)
top["rk"] = top.groupby("tkey").cumcount() + 1
t1, t2 = top[top.rk == 1], top[top.rk == 2]
x = t1.merge(t2, on="tkey", suffixes=("_a", "_b"))
wn.append(summarize("WNBA teammates top-2 scorers points", x.points_a.values, x.points_b.values,
                    x.l_points_a.values, x.l_points_b.values, x.game_id_a.values))
x = t1.merge(t1, on="game_id", suffixes=("_a", "_b"))
x = x[x.team_id_a < x.team_id_b]
wn.append(summarize("WNBA opposing top scorers points", x.points_a.values, x.points_b.values,
                    x.l_points_a.values, x.l_points_b.values, x.game_id.values))
playoff = w.season_type == 3
pc = core[playoff.loc[core.index]]
wn.append(summarize("WNBA PLAYOFFS same player points + rebounds", pc.points.values, pc.rebounds.values,
                    pc.l_points.values, pc.l_rebounds.values, pc.game_id.values))

res = dict(nfl_pairs=nfl, nfl_trios=nfl_trios, wnba_pairs=wn,
           break_even={"2-pick 3x per slip": 1 / 3, "3-pick 6x per slip": 1 / 6, "5-pick 20x per slip": 1 / 20})
json.dump(res, open(OUT, "w"), indent=1)
pd.set_option("display.width", 220)
for k in ("nfl_pairs", "wnba_pairs", "nfl_trios"):
    print(f"\n== {k}")
    print(pd.DataFrame(res[k]).to_string(index=False))
