"""Production: fit on all data through 2026 wk5 TNF, project Sunday Oct 11 2026 (nflverse 'Week 5') games."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user-fantastic-octo-computing-machine/fd837da0-fc17-5f70-a6ad-c31478ee2717/scratchpad/nfl/props')
from common import *

SEASON, WEEK = 2026, 5
games = load_games()
pgh = load_players()
import os
SUF = os.environ.get('OUT_SUFFIX', '')
for item in filter(None, os.environ.get('DROP', '').split(',')):
    nm, sn = item.split(':'); pgh = pgh[~((pgh.name == nm) & (pgh.season == int(sn)))]
today = games[(games.season == SEASON) & (games.week == WEEK) & (games.gameday >= '2026-10-11')]
teams = set(today.team)

# ---- candidate pool: players whose latest team is one of today's teams and who played in 2026
lat = pgh[pgh.season == SEASON].sort_values(['player_id', 'week']).groupby('player_id').tail(1)
lat = lat[lat.team.isin(teams)][['player_id', 'name', 'pos', 'team']]
# add today's named starting QBs even without 2026 snaps
allq = pgh.sort_values(['player_id', 'season', 'week']).groupby('player_id').tail(1)[['player_id', 'name', 'pos', 'team']]
qbn = today[['team', 'qb_name']].dropna()
extra = []
for _, r in qbn.iterrows():
    hit = allq[(allq.name == r.qb_name) & (allq.pos == 'QB')]
    if len(hit) == 0:
        print('QB NOT FOUND in nflverse history:', r.team, r.qb_name)
        continue
    h = hit.iloc[0]
    extra.append(dict(player_id=h.player_id, name=h['name'], pos='QB', team=r.team))
cand = pd.concat([lat, pd.DataFrame(extra)], ignore_index=True).drop_duplicates(['player_id', 'team'])
cand = cand.merge(today[['team', 'opp']], on='team').rename(columns={'opp': 'opponent_team'})
cand['season'] = SEASON; cand['week'] = WEEK
for c in ['attempts', 'passing_yards', 'passing_tds', 'carries', 'rushing_yards', 'targets', 'receptions', 'receiving_yards']:
    cand[c] = np.nan
cand['position'] = cand.pos

pg = assign_roles(build(pg=pgh, games=games, extra_rows=cand))
hist = pg.season.lt(SEASON) | (pg.week < WEEK) | pg.receiving_yards.notna() | pg.attempts.notna() | pg.carries.notna()
hist = pg.receptions.notna() | pg.passing_yards.notna() | pg.rushing_yards.notna()
up = (pg.season == SEASON) & (pg.week == WEEK) & ~hist
# restrict training to rows from 2023 on (roles need history)
train = hist & (pg.season >= 2023)

# manual roles for upcoming rows
pg.loc[up, 'role'] = ''; pg.loc[up, 'rrank'] = 0
starters = set(zip(qbn.team, qbn.qb_name))
for i in pg.index[up]:
    if pg.at[i, 'pos'] == 'QB' and (pg.at[i, 'team'], pg.at[i, 'name']) in starters:
        pg.at[i, 'role'] = 'QB'; pg.at[i, 'rrank'] = 1
u = pg[up].copy()
# RB: top 2 by u_car ; WR/TE: top 4 by u_tgt
for t, g in u[u.pos == 'RB'].groupby('team'):
    for r, (i, row) in enumerate(g.sort_values('u_car', ascending=False).head(2).iterrows(), start=1):
        pg.at[i, 'role'] = 'RB'; pg.at[i, 'rrank'] = 1; pg.at[i, 'sub'] = r
for t, g in u[u.pos.isin(['WR', 'TE'])].groupby('team'):
    for r, (i, row) in enumerate(g.sort_values('u_tgt', ascending=False).head(4).iterrows(), start=1):
        pg.at[i, 'role'] = 'WRTE'; pg.at[i, 'rrank'] = min(r, 2); pg.at[i, 'sub'] = r

models = {}
rows = []
for stat, cfg in STATS.items():
    m = StatModel(stat).fit(pg, train)
    models[stat] = m
    mu, mu0, alpha, den = m.predict(pg)
    sel = up & (pg.role == cfg['role'])
    d = pg[sel].copy()
    d['stat'] = stat; d['mu'] = mu[sel.values]; d['mu0'] = mu0[sel.values]; d['alpha'] = alpha[sel.values]; d['eff_n'] = den[sel.values]
    d['median'] = median_nb(d.mu.values, d.alpha.values)
    rows.append(d)
    print(stat, m.params['hl'], m.params['k'], np.round(m.beta, 3), 'alpha', np.round(np.exp(m.a[0]), 3), 'n', m.params['n_train'])
P = pd.concat(rows)
json.dump({s: m.params for s, m in models.items()}, open(BASE + f'/params_final{SUF}.json', 'w'), indent=1)

# 2026 YTD context
cur = pgh[pgh.season == SEASON]
def ytd(pid, col):
    x = cur[cur.player_id == pid][col]
    return (len(x), x.mean() if len(x) else np.nan, x.tail(2).mean() if len(x) else np.nan)
ctx = []
for _, r in P.iterrows():
    n, avg, l2 = ytd(r.player_id, STATS[r.stat]['col'])
    ctx.append((n, avg, l2))
P['g26'] = [c[0] for c in ctx]; P['avg26'] = [c[1] for c in ctx]; P['last2'] = [c[2] for c in ctx]
P = P.merge(today[['team', 'gameday', 'gametime']].drop_duplicates(), on='team', how='left')
P.to_pickle(BASE + f'/proj_raw{SUF}.pkl')
keep = ['name', 'team', 'opponent_team', 'pos', 'role', 'rrank', 'sub', 'stat', 'mu', 'median', 'alpha', 'eff_n', 'g26', 'avg26', 'last2',
        'is_home', 'spread_team', 'total', 'imp', 'gameday', 'gametime', 'u_att', 'u_car', 'u_tgt']
P[keep].round(3).to_csv(BASE + f'/proj_candidates{SUF}.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_rows', 500)
for stat in STATS:
    print('\n#####', stat)
    print(P[P.stat == stat][['team', 'opponent_team', 'name', 'pos', 'rrank', 'sub', 'mu', 'median', 'g26', 'avg26', 'last2', 'eff_n']].sort_values(['team', 'rrank', 'sub']).round(2).to_string(index=False))
