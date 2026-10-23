import sys, pandas as pd, numpy as np
sys.path.insert(0, 'props')
from common import p_over
P = pd.read_csv('props/projections.csv')
P = P[P.day == 'Sun'].copy()
games = {}
order = ['PHI','CHI','CIN','CLE','HOU','IND','LV','MIN','NYG','DEN','DET','SF','BAL']
P['game'] = P.apply(lambda r: ' / '.join(sorted([r.team, r.opp])), axis=1)
STAT = {'pass_yds':'Pass yds','pass_tds':'Pass TDs','rush_yds':'Rush yds','rec_yds':'Rec yds','receptions':'Receptions'}
W = 0.3
def blend(p): return W*p + (1-W)*0.5
def f(x): return '—' if pd.isna(x) else f'{x:g}'
kick = {}
out = ['# Dabble / Underdog NFL cheat sheet — Sun Oct 11, 2026', '',
 'Use: open a player\'s line in the app and compare it with this row.',
 '- **More ✅** only if the app line is **at or below** the "More if ≤" number.',
 '- **Less ✅** only if the app line is **at or above** the "Less if ≥" number.',
 '- Anything between the two numbers is a **pass**.',
 '- 3-pick numbers: at the cutoff the leg hits ~55% after the Benter blend (= 3-pick break-even). 2-pick numbers: ~58% (= 2-pick break-even). Each half-point beyond the cutoff adds roughly 0.5–1.5 points of hit%.',
 '- Receiving (Rec yds, Receptions) Mores ran 3–5 points too high in the 2025 test. For receiving **More**, require the line to be at least 5 yds (or 0.5 catch) below the cutoff.',
 '- Pass TDs: 0.5 / 1.5 lines are nearly always priced right; skip unless the cutoff says otherwise.', '']
for (tm, opp), g in P.groupby(['kick_ET(nflverse)','game'], sort=True):
    pass
for game, g in sorted(P.groupby('game'), key=lambda x: (x[1]['kick_ET(nflverse)'].iloc[0], x[0])):
    k = g['kick_ET(nflverse)'].iloc[0]
    out.append(f'## {game} — kick {k} ET'); out.append('')
    out.append('| Player | Stat | Median | 3-pick More if ≤ | 3-pick Less if ≥ | 2-pick More if ≤ | 2-pick Less if ≥ |')
    out.append('|---|---|---|---|---|---|---|')
    g = g.copy(); g['so'] = g.stat.map({k:i for i,k in enumerate(STAT)})
    for _, r in g.sort_values(['team','pos','name','so']).iterrows():
        nm = f"{r['name']} ({r.team} {r.pos})"
        if r.stat == 'pass_tds': continue
        out.append(f"| {nm} | {STAT[r.stat]} | {f(r['median'])} | {f(r.over_max_pk3)} | {f(r.under_min_pk3)} | {f(r.over_max_pk2)} | {f(r.under_min_pk2)} |")
    out.append('')
out += ['## How the hit % is computed', '',
 '- Model: recency-weighted negative-binomial GLM per stat (opponent defence, team implied total, spread), tested on 2025 weeks 6–18 (well calibrated for QB/RB; receiving Overs high).',
 '- Leg hit % = 0.3 × model P(side) + 0.7 × 50% (a pick\'em line is treated as a coin-flip market price).',
 '- Slip hit % = product of the legs (legs from the same game are correlated; never stack a QB More with his WR More in the same slip).',
 '- 3-pick break-even 55.0%/leg (6x), 2-pick 57.7%/leg (3x), 5-pick 54.9%/leg (20x).',
 '- Injuries/inactives after ~13:30 UTC are NOT reflected. Check that the player is active before you use a row.']
open('dabble_cheatsheet_2026-10-11.md','w').write('\n'.join(out))
print(len(out))
