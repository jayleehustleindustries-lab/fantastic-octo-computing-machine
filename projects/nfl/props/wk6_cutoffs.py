"""Week 6 Dabble/Underdog cutoffs (blended 0.3 model + 0.7 line). Research only."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, sys.argv[1]); from common import p_over
W = 0.3; BE = {"pk3": 6 ** (-1/3), "pk2": 3 ** -0.5}
P = pd.read_pickle(sys.argv[1] + '/proj_raw_wk6.pkl')
keep = []
for (t, stat), g in P.groupby(['team', 'stat']):
    n = {'pass_yds': 1, 'pass_tds': 1, 'rush_yds': 2}.get(stat, 3)
    keep += list(g.sort_values('sub').index[:n]) if 'sub' in g and g['sub'].notna().any() else list(g.index[:n])
P = P.loc[keep].copy()
STEP = {'pass_yds': 0.5, 'rush_yds': 0.5, 'rec_yds': 0.5, 'receptions': 0.5, 'pass_tds': 0.5}
def cut(r, side, be):
    lines = np.arange(0.5, max(5, r['mu'] * 3), 1.0)
    ok = []
    for L in lines:
        po = float(p_over(r.mu, r.alpha, L)); p = po if side == 'more' else 1 - po
        if W * p + (1 - W) * 0.5 >= be: ok.append(L)
    if not ok: return np.nan
    return max(ok) if side == 'more' else min(ok)
rows = []
for _, r in P.iterrows():
    rows.append(dict(game=f"{r.team} vs {r.opponent_team}", day=r.gameday, kick=r.gametime, name=r['name'], pos=r.pos, stat=r.stat,
                     proj=round(r.mu, 1), median=r['median'], g26=r.g26, more_pk3=cut(r, 'more', BE['pk3']), less_pk3=cut(r, 'less', BE['pk3']),
                     more_pk2=cut(r, 'more', BE['pk2']), less_pk2=cut(r, 'less', BE['pk2'])))
D = pd.DataFrame(rows).sort_values(['day', 'kick', 'game', 'stat', 'proj'], ascending=[True, True, True, True, False])
D.to_csv(sys.argv[1] + '/wk6_cutoffs.csv', index=False)
pd.set_option('display.width', 220)
print(D[D.day == '2026-10-15'].drop(columns=['day']).to_string(index=False))
print('\nrows total', len(D), 'games', D.game.nunique() // 2)
