"""Price NFL pick'em legs with a weekly NB projection and tag stack roles. Research only.

input CSV: player,stat,line,side   (side MORE/LESS; stat pass_yds|pass_tds|rush_yds|rec_yds|receptions)
output JSON legs for slips.py: p = blended P(win) = 0.3*model + 0.7*(1-push)*0.5, plus role/team/game.
Roles come from the model's own projection order within the team (prior-games usage), not tonight's result.
Players carrying INJ_TAG (projections from project_wk7.py on) are priced but marked; slips.py keeps them out of stacks.

usage: python nfl_legs.py <nfl_props_dir> <lines.csv> <out.json> <proj_raw.pkl> <gameday YYYY-MM-DD>
"""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1])
from common import p_over  # noqa: E402

W = 0.3
P = pd.read_pickle(sys.argv[4])
P = P[P.gameday == sys.argv[5]].copy()
if "inj_tag" not in P:
    P["inj_tag"] = False
rec = P[P.stat == "rec_yds"].sort_values("mu", ascending=False)
role = {}
for team, g in rec.groupby("team"):
    wr = g[g.pos == "WR"]["name"].tolist()
    te = g[g.pos == "TE"]["name"].tolist()
    for i, n in enumerate(wr[:2]):
        role[(team, n)] = f"WR{i + 1}"
    if te:
        role[(team, te[0])] = "TE1"
for team, g in P[P.stat == "pass_yds"].sort_values("mu", ascending=False).groupby("team"):
    role[(team, g["name"].iloc[0])] = "QB"
for team, g in P[P.stat == "rush_yds"].sort_values("mu", ascending=False).groupby("team"):
    role.setdefault((team, g["name"].iloc[0]), "RB1")

lines = pd.read_csv(sys.argv[2])
legs = []
for L in lines.itertuples():
    r = P[(P["name"] == L.player) & (P.stat == L.stat)]
    if r.empty:
        print(f"NOT FOUND in model: {L.player} {L.stat}")
        continue
    r = r.iloc[0]
    po = float(p_over(r.mu, r.alpha, L.line))
    push = float(p_over(r.mu, r.alpha, L.line - 1) - po) if float(L.line).is_integer() else 0.0
    pu = 1 - po - push
    pm = po if L.side == "MORE" else pu
    p = W * pm + (1 - W) * (1 - push) * 0.5
    rl = role.get((r.team, L.player), "OTHER")
    game = f"{r.team}@{r.opponent_team}" if r.is_home == 0 else f"{r.opponent_team}@{r.team}"
    legs.append(dict(player=L.player, market=L.stat, line=float(L.line), side=L.side, team=r.team, game=game,
                     inj_tag=bool(r.inj_tag),
                     role=f"{rl}_{L.stat}", proj=round(float(r.mu), 1), median=float(r["median"]),
                     p_model=round(pm, 4), p=round(p, 4), push=round(push, 4)))
json.dump(legs, open(sys.argv[3], "w"), indent=1)
for l in legs:
    print(f"{l['player']:22s} {l['market']:10s} {l['side']:4s} {l['line']:6.1f}  proj {l['proj']:6.1f}  model {l['p_model']:.3f}  blended {l['p']:.3f}  role {l['role']}")
