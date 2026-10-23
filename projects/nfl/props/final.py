"""Apply news-based exclusions, expand line grids, compute edges for publicly reported lines."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user-fantastic-octo-computing-machine/fd837da0-fc17-5f70-a6ad-c31478ee2717/scratchpad/nfl/props')
from common import *

W = 0.30
P = pd.read_pickle(BASE + '/proj_raw.pkl')
# Daniels: 2026 history = two injury-shortened games (dislocated elbow) -> use projection with 2026 rows dropped (project.py DROP env)
_alt = pd.read_pickle(BASE + '/proj_raw_daniels.pkl')
for _, a in _alt[_alt.name == 'Jayden Daniels'].iterrows():
    m = (P.name == 'Jayden Daniels') & (P.stat == a.stat)
    for c in ['mu', 'median', 'alpha', 'eff_n']:
        P.loc[m, c] = a[c]

# ---- news-based status (public reports found via WebSearch, Oct 7-11 2026; see report for sources)
OUT = {('DeVonta Smith', 'PHI'): 'OUT (hamstring, per Eagles injury report coverage Oct 9)',
       ('Saquon Barkley', 'PHI'): 'OUT (hamstring, Oct 9)',
       ("De'Von Achane", 'MIA'): 'OUT - reported season-ending ACL (YouWager.lv snippet; low-confidence source)',
       ('Stefon Diggs', 'WAS'): 'OUT (hamstring, RotoBaller Oct 9)',
       ('A.J. Brown', 'NE'): 'OUT - on reserve list per Raiders-Patriots previews'}
FLAG = {('Ashton Jeanty', 'LV'): 'QUESTIONABLE (ankle/foot, not seen at Fri practice)',
        ("Ja'Marr Chase", 'CIN'): 'QUESTIONABLE/limited (concussion in Wk4)',
        ('Tee Higgins', 'CIN'): 'QUESTIONABLE/limited (adductor)',
        ('Jayden Daniels', 'WAS'): 'Expected to play after elbow dislocation (2026 injury-shortened games excluded from his history); backup Mariota hurt (MCL)',
        ('Terry McLaurin', 'WAS'): 'Likely to play (hamstring, returned to practice Fri)',
        ('Dallas Goedert', 'PHI'): 'Back from MCL sprain, no designation',
        ('Tyler Huntley', 'BAL'): 'Starting for injured Lamar Jackson (ankle) - small-sample QB',
        ('Tank Bigsby', 'PHI'): 'Lead back with Barkley out - projection understates volume',
        ('Ollie Gordon II', 'MIA'): 'Lead back with Achane out - projection understates volume'}
P['status'] = [OUT.get((n, t), FLAG.get((n, t), '')) for n, t in zip(P.name, P.team)]
P['out'] = [(n, t) in OUT for n, t in zip(P.name, P.team)]
P = P[~P.out].copy()
P['day'] = np.where(P.gameday == '2026-10-12', 'Mon', 'Sun')
P['kick_ET'] = P.gametime
P['lowdata'] = ((P.eff_n < 6) & P.stat.isin(['rec_yds', 'receptions', 'rush_yds'])) | ((P.eff_n < 4.5) & (P.stat.isin(['pass_yds', 'pass_tds'])))

# keep final roles: QB, RB1/RB2 (flag), WR/TE top-2 healthy + 3rd/4th retained as "next up" if a top guy is out
keep = []
for (t, stat), g in P.groupby(['team', 'stat']):
    role = STATS[stat]['role']
    if role == 'QB':
        keep += list(g.index)
    elif role == 'RB':
        keep += list(g.sort_values('sub').index[:2])
    else:
        keep += list(g.sort_values('sub').index[:3])
P = P.loc[keep].copy()
P['rank_now'] = P.groupby(['team', 'stat']).sub.rank(method='first')
P['tier'] = np.where(P.pos == 'QB', 'QB', np.where(P.stat.eq('rush_yds'), np.where(P.rank_now == 1, 'RB1', 'RB2'), np.where(P.rank_now <= 2, 'Top2', 'Next')))

STEP = {'pass_yds': 10, 'rush_yds': 5, 'rec_yds': 5, 'receptions': 1}
rows = []
for _, r in P.iterrows():
    if r.stat == 'pass_tds':
        lines = [0.5, 1.5, 2.5]
    else:
        c = np.floor(r['median']) + 0.5
        lines = [c + STEP[r.stat] * k for k in range(-3, 4)]
        lines = [l for l in lines if l > 0]
    for L in lines:
        po = float(p_over(r.mu, r.alpha, L))
        rows.append(dict(name=r['name'], team=r.team, opp=r.opponent_team, day=r.day, stat=r.stat, tier=r.tier, line=L,
                         p_over=round(po, 4), p_under=round(1 - po, 4)))
G = pd.DataFrame(rows)
P['sd'] = np.sqrt(P.mu + P.alpha * P.mu ** 2)
out = P[['name', 'team', 'opponent_team', 'day', 'kick_ET', 'pos', 'tier', 'stat', 'mu', 'median', 'sd', 'alpha', 'eff_n', 'g26', 'avg26', 'last2',
         'spread_team', 'total', 'imp', 'status', 'lowdata']].copy()
out = out.rename(columns={'mu': 'mean_proj', 'opponent_team': 'opp', 'spread_team': 'team_spread', 'imp': 'implied_total', 'kick_ET': 'kick_ET(nflverse)'})
out = out.round(3).sort_values(['day', 'team', 'stat', 'tier'])
out.to_csv(BASE + '/projections.csv', index=False)
G.to_csv(BASE + '/projection_lines.csv', index=False)
P.to_pickle(BASE + '/proj_final.pkl')

# ---------------------------------------------------------------- edges for publicly-reported lines
# each: player, team, stat, line, over_price, under_price (American; None=unknown), venue, source, reliability
L = [
 ('Jalen Hurts', 'PHI', 'pass_yds', 193.5, -112, -112, 'FanDuel (consensus ~189.5-193.5)', 'Inquirer 10/8 (FD 193.5 / DK 189.5, ~-112/-114)', 'Medium'),
 ('Jalen Hurts', 'PHI', 'pass_tds', 0.5, -225, 175, 'FanDuel (DK over -197)', 'Inquirer 10/8; UNDER price not found -> +175 ASSUMED', 'Medium'),
 ('C.J. Stroud', 'HOU', 'pass_yds', 243.5, -110, -110, 'consensus (FD opened 239.5 -114)', 'SportsBettingDime line-move piece 10/9 (243.5 current); prices ASSUMED -110/-110', 'Medium'),
 ('Cam Ward', 'TEN', 'pass_yds', 193.5, -110, -110, 'consensus (opened 181.5)', 'SportsBettingDime 10/9 (193.5 current); prices ASSUMED', 'Medium'),
 ('Jared Goff', 'DET', 'pass_yds', 280.5, -110, -110, 'consensus', 'StackedFantasy snippet; prices ASSUMED', 'Low'),
 ('Jayden Daniels', 'WAS', 'pass_yds', 210.5, -110, -110, 'DraftKings', 'Legal Sports Report snippet (opponent mislabeled in snippet); prices ASSUMED', 'Low'),
 ('Michael Wilson', 'ARI', 'rec_yds', 70.0, -130, 100, 'FanDuel', 'FantasyLife pick article (over 70 -130); UNDER price ASSUMED +100', 'Medium'),
 ('Amon-Ra St. Brown', 'DET', 'rec_yds', 80.0, -110, -110, 'unknown book', 'Squawka editorial pick (over 80); prices ASSUMED', 'Low'),
 ('Chris Olave', 'NO', 'rec_yds', 70.0, -110, -110, 'unknown book', 'Squawka editorial pick (over 70); prices ASSUMED', 'Low'),
 ('Chase Brown', 'CIN', 'rush_yds', 65.5, -110, -110, 'unknown book', 'FantasyAlarm expert pick (over 65.5); prices ASSUMED', 'Low'),
]
def dec(a): return 1 + (a / 100 if a > 0 else 100 / -a)
def imp(a): return 1 / dec(a)
res = []
for (n, t, s, line, po, pu, venue, src, rel) in L:
    r = P[(P['name'] == n) & (P.team == t) & (P.stat == s)]
    if len(r) == 0:
        res.append(dict(player=n, note='no projection (player excluded/not found)')); continue
    r = r.iloc[0]
    pov = float(p_over(r.mu, r.alpha, line)); ppush = float(p_push(r.mu, r.alpha, line)); pun = 1 - pov - ppush
    # no-vig market
    io, iu = imp(po), imp(pu)
    nv_o = io / (io + iu); nv_u = 1 - nv_o
    for side, pm_raw, pmk, price in (('OVER', pov, nv_o, po), ('UNDER', pun, nv_u, pu)):
        pm = pm_raw / (1 - ppush)
        pb = W * pm + (1 - W) * pmk
        d = dec(price); be = 1 / d
        edge = pb * d - 1
        kelly = max(0.0, edge / (d - 1)); qk = 0.25 * kelly
        res.append(dict(player=n, team=t, opp=r.opponent_team, day=r.day, stat=s, side=side, line=line, price=price, venue=venue, source=src, reliability=rel,
                        mean_proj=round(r.mu, 1), median=r['median'], p_model=round(pm, 4), p_market_nv=round(pmk, 4), p_blend=round(pb, 4),
                        break_even=round(be, 4), edge=round(edge, 4), quarter_kelly_pct_bankroll=round(100 * qk, 2),
                        pickem3_leg_ok=bool(pb >= 6 ** (-1 / 3)), pickem2_leg_ok=bool(pb >= 3 ** (-0.5))))
R = pd.DataFrame(res)
R.to_csv(BASE + '/edge_check_all_sides.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_columns', 40)
print(R[['player', 'team', 'day', 'stat', 'side', 'line', 'price', 'mean_proj', 'median', 'p_model', 'p_market_nv', 'p_blend', 'break_even', 'edge', 'pickem3_leg_ok', 'reliability']].to_string(index=False))
