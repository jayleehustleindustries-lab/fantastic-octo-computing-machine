import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user-fantastic-octo-computing-machine/fd837da0-fc17-5f70-a6ad-c31478ee2717/scratchpad/nfl/props')
from common import *

W = 0.30
P = pd.read_pickle(BASE + '/proj_final.pkl').reset_index(drop=True)
E = pd.read_csv(BASE + '/edge_check_all_sides.csv')
params = json.load(open(BASE + '/params_final.json'))

# thresholds on the posted line at which a pick'em/sportsbook leg would clear break-even after blending (p_market=0.5)
def need_p(be, pm=0.5): return (be - (1 - W) * pm) / W
THR = {'sb110': need_p(1 / 1.9091), 'pk3': need_p(6 ** (-1 / 3)), 'pk2': need_p(3 ** -0.5)}
grid = np.arange(0.5, 700.5, 1.0)
cols = {k: [] for k in ['over_max_sb', 'under_min_sb', 'over_max_pk3', 'under_min_pk3', 'over_max_pk2', 'under_min_pk2']}
for _, r in P.iterrows():
    po = p_over(r.mu, r.alpha, grid)
    for key, thr in THR.items():
        ok_o = grid[po >= thr]; ok_u = grid[(1 - po) >= thr]
        cols['over_max_' + ('sb' if key == 'sb110' else key)].append(ok_o.max() if len(ok_o) else np.nan)
        cols['under_min_' + ('sb' if key == 'sb110' else key)].append(ok_u.min() if len(ok_u) else np.nan)
for k, v in cols.items(): P[k] = v
# enrich projections.csv with thresholds
proj = pd.read_csv(BASE + '/projections.csv')
key = P[['name', 'team', 'stat']].copy()
for k in cols: key[k] = P[k].values
proj = proj.merge(key, on=['name', 'team', 'stat'], how='left')
proj.to_csv(BASE + '/projections.csv', index=False)

STEP = {'pass_yds': 10, 'rush_yds': 5, 'rec_yds': 5, 'receptions': 1}
def grid5(r):
    if r.stat == 'pass_tds': ls = [0.5, 1.5, 2.5]
    else:
        c = np.floor(r['median']) + 0.5
        ls = [c + STEP[r.stat] * k for k in (-2, -1, 0, 1, 2)]
    return ' / '.join(f'{l:g}: {p_over(r.mu, r.alpha, l):.0%}' for l in ls if l > 0)
def fmt(x): return '-' if pd.isna(x) else f'{x:g}'

L = []
a = L.append
a('# NFL player-prop projections - Sunday Oct 11 2026 (nflverse "Week 5") - Dabble / Underdog / bet365 comparison')
a('')
a('Generated Sun Oct 11 2026 ~13:30 UTC from public data only (nflverse player stats + schedule/consensus lines, public news snippets). No sportsbook / DFS app was logged into or scraped.')
a('')
a('## 0. Read this first')
a('')
a('* **Week label:** the task said "Week 6", but nflverse (and every public article found) calls today\'s Sunday Oct 11 slate **Week 5**; Week 6 starts Thu Oct 15. I projected the 13 games on the board **today** (plus Monday BUF@LA, flagged `Mon`). Kickoffs: PHI@JAX 13:30 UTC (London - starts before most people read this), nine 17:00 UTC games, 20:05/20:25 UTC games, BAL@ATL 00:20 UTC.')
a('* **Public lines were thin.** WebFetch is blocked in this sandbox and search returns snippets only. I found real 2026-Week-5 consensus numbers for only ~10 props (table in section 2). **No public Dabble / Underdog / bet365 lines were found** - not fabricated. Prices not seen are marked ASSUMED.')
a('* **Bottom line: the market looks efficient against this model.** After the Benter blend (w=0.30) only 4 of the ~10 priced props clear the -110 break-even, each by 1.7% to 3.4% edge, **none clears a pick\'em per-leg bar** (3-pick 55.0%, 2-pick 57.7%). Treat everything as small-stakes ($1) and low confidence.')
a('* For anything you see in the Dabble/Underdog app, use the **lookup columns in section 3**: each projection lists the posted-line cut-offs at which More/Less would clear the bar after blending (p_market = 0.5 for pick\'em).')
a('')
a('## 1. Method and validation')
a('')
a('**Model (per stat):** player mean = exponentially-weighted (half-life in games, fitted) average of his own games across 2022-2026, shrunk toward a role prior (QB / RB1 / WR-TE rank 1-2); times a log-linear (quasi-Poisson GLM) adjustment for opponent defence (shrunk EWMA of stat allowed to that position group), team implied total (from consensus total & spread) and spread; distribution = Negative Binomial with dispersion from method of moments. All features are causal (only games before the target game). Role set backtested = starting QB, RB1, top-2 WR/TE by prior target share (among players who actually appeared).')
a('')
a('**Fitted (final, trained 2023 to 2026 wk5-TNF):** ' + '; '.join(f"{s}: half-life {p['hl']} games, shrink k={p['k']}, GLM [int, log opp, log implied, spread/7] = {np.round(p['beta'], 2).tolist()}, NB alpha={np.exp(p['a'][0]):.3f}" for s, p in params.items()))
a('')
a('**Out-of-sample test = 2025 weeks 6-18** (fit on 2023, 2024, 2025 wk1-5; features strictly pre-game). n = 369 QB, 381 RB1, 768 WR/TE-slots.')
a('')
a('| Stat | MAE model | MAE EWMA-only | MAE naive EWMA | P(over at median-line) pred / obs | -10% line pred / obs | +10% line pred / obs | mean(proj) vs mean(actual) |')
a('|---|---|---|---|---|---|---|---|')
a('| Pass yds | 59.2 | 62.4 | 63.5 | 49.7% / 51.2% | 61.7% / 61.8% | 39.0% / 39.6% | 224.5 vs 215.0 |')
a('| Pass TDs | 0.96 | 0.97 | 1.01 | 0.5: 75.2% / 75.1% ; 1.5: 42.4% / 43.6% ; 2.5: 19.1% / 18.2% | - | - | 1.47 vs 1.43 |')
a('| Rush yds (RB1) | 28.5 | 29.0 | 29.2 | 49.4% / 52.2% | 57.0% / 58.3% | 43.4% / 47.5% | 62.4 vs 64.2 |')
a('| Rec yds (top-2 WR/TE) | 26.9 | 27.4 | 26.9 | 49.3% / 46.0% | 56.2% / 52.0% | 44.1% / 41.9% | 54.6 vs 51.6 |')
a('| Receptions | 1.81 | 1.83 | 1.82 | 41.5% / 36.1% (line = floor(med)+.5) | 58.8% / 55.6% | 27.0% / 22.5% | 4.46 vs 4.18 |')
a('')
a('* Pooled over all stats and offset lines (-20% to +20%): model log-loss 0.6310 vs 0.6410 for EWMA-only (no opp/script adj). Model-preferred-side buckets: p>=0.55 -> predicted 66.1%, hit 65.7% (n=10,421); p>=0.66 -> 76.7% vs 77.7% (n=3,875); p>=0.76 -> 82.7% vs 83.4% (n=1,824). **QB and RB probabilities are well calibrated.**')
a('* **Known weakness:** receiving yards / receptions were over-projected ~6% in the 2025 test window (league-wide receiving fell ~6% vs 2023-24), so receiving *Over* probabilities there were ~3-5 pts too high. The 2026 year-to-date actual/projection ratio is 0.99 (rec yds) and 0.98 (receptions), 1.02 (pass yds), 1.01 (rush yds), so no correction was applied, but treat receiving Overs with extra caution.')
a('* **Not validated against the market:** no historical prop lines are available publicly, so w (model weight) could not be fitted; w = 0.30 is the assumed Benter weight. The validation shows the model is calibrated to *outcomes*, not that it beats closing lines - the market is probably sharper, which is why the blended edges are small.')
a('')
a('## 2. Publicly reported lines vs model (both sides, after blending)')
a('')
a('p_blend = 0.30 x p_model + 0.70 x p_market(no-vig). Break-even = 1/decimal price. Edge = p_blend x decimal - 1. "Pick\'em 3-leg OK" = p_blend >= 55.0%.')
a('')
a('| Player | Game | Market | Side | Line | Price | Mean/Median | p_model | p_market | p_blend | Break-even | Edge | 3-leg bar | Line reliability / source |')
a('|---|---|---|---|---|---|---|---|---|---|---|---|---|---|')
for _, r in E.sort_values('edge', ascending=False).iterrows():
    a(f"| {r.player} | {r.team} vs {r.opp} | {r.stat} | {r.side} | {r.line:g} | {r.price:+.0f} | {r.mean_proj:g} / {r['median']:g} | {r.p_model:.1%} | {r.p_market_nv:.1%} | {r.p_blend:.1%} | {r.break_even:.1%} | {r.edge:+.1%} | {('n/a (priced market)' if abs(r.p_market_nv - 0.5) > 0.02 else ('yes' if r.pickem3_leg_ok else 'no'))} | {r.reliability}: {r.source} |")
a('')
a('Notes: Daniels uses his projection with the two injury-shortened 2026 games (dislocated elbow) dropped from his history (raw model said 186 mean; adjusted 194). Hurts, Goff, St. Brown, Olave have no edge on either side. Wilson UNDER 70 clears only if the under is priced +100 or better (assumed) - not recommended. Allen over 249.5 and Stafford 280.5 are Monday-night lines, not evaluated.')
a('')
a('## 3. Projection tables (for comparing any Dabble / Underdog line)')
a('')
a('Columns: **Mean/Median/SD** = model; **P(over)** at five lines around the median; **More clears if line <=** / **Less clears if line >=** = the posted-line cut-off at which the leg beats the break-even after blending, for a 3-pick pick\'em (needs p_model>=66.8%), 2-pick pick\'em (>=75.8%) and a -110 sportsbook prop (>=57.9%). "-" = no line qualifies. `lowdata` = fewer than ~6 effective games of history. Status flags come from public injury news (Oct 7-11) - **re-check inactives ~90 min before kickoff**.')
a('')
order = [('pass_yds', 'Passing yards (starting QB)'), ('pass_tds', 'Passing TDs (starting QB)'), ('rush_yds', 'Rushing yards (RB1 / RB2)'),
         ('rec_yds', 'Receiving yards (top-2 WR/TE; 3rd = next up)'), ('receptions', 'Receptions (top-2 WR/TE; 3rd = next up)')]
for stat, title in order:
    a(f'### {title}')
    a('')
    a('| Player | Game (day, kick ET) | Mean | Med | SD | P(over) at lines | More <= (3pk/2pk/-110) | Less >= (3pk/2pk/-110) | Status |')
    a('|---|---|---|---|---|---|---|---|---|')
    S = P[P.stat == stat].copy()
    S['gk'] = S.day.map({'Sun': 0, 'Mon': 1}) * 1000
    S = S.sort_values(['day', 'gametime', 'team', 'tier', 'name'])
    for _, r in S.iterrows():
        game = f"{r.team} v {r.opponent_team} ({r.day} {r.gametime})"
        flags = r.status + (' [lowdata]' if r.lowdata else '')
        a(f"| {r['name']} ({r.pos}, {r.tier}) | {game} | {r.mu:.1f} | {r['median']:g} | {np.sqrt(r.mu + r.alpha * r.mu ** 2):.1f} | {grid5(r)} | {fmt(r.over_max_pk3)} / {fmt(r.over_max_pk2)} / {fmt(r.over_max_sb)} | {fmt(r.under_min_pk3)} / {fmt(r.under_min_pk2)} / {fmt(r.under_min_sb)} | {flags} |")
    a('')
a('## 4. Status / news used (public, search-snippet level, verify before betting)')
a('')
for t in ['Lamar Jackson ruled OUT (ankle) - Tyler Huntley starts for BAL at ATL (Fox Sports / AJC Oct 9).',
          'PHI at JAX (London): DeVonta Smith OUT, Saquon Barkley OUT (hamstrings); Dallas Goedert back; Dontayvion Wicks no designation (Inquirer / PhillyVoice / RotoBaller Oct 9). Bigsby becomes lead back - projection understates volume.',
          'WAS: Jayden Daniels expected to start after elbow dislocation (backup Mariota MCL); Stefon Diggs OUT; Terry McLaurin trending to play.',
          'MIA: De\'Von Achane reported out for the season (ACL) per one low-reliability snippet - excluded; Ollie Gordon II listed as lead back (volume understated).',
          'CIN: Ja\'Marr Chase (concussion in Wk4) and Tee Higgins (adductor) limited - status unresolved; CIN -7/-7.5, total ~42.5-43.5.',
          'LV: Ashton Jeanty questionable (ankle/foot). NE: A.J. Brown on reserve list - excluded.',
          'All injury items are from search snippets dated Oct 7-9; Sunday inactives were not yet available at generation time.']:
    a('* ' + t)
a('')
a('## 5. Sources (search snippets; pages themselves could not be fetched)')
a('')
for t in ['Hurts lines & PHI/JAX: https://www.inquirer.com/eagles/eagles-jaguars-week-5-nfl-odds-prop-bets-20261008.html ; https://www.phillyvoice.com/eagles-jaguars-week-5-betting-odds-money-lines-points-spread-jalen-hurts-trevor-lawrence-london/',
          'Stroud / Ward lines: https://www.sportsbettingdime.com/?p=840997 ; https://www.rotoballer.com/?p=1961726',
          'Goff 280.5 (StackedFantasy): https://www.stackedfantasy.com/nfl/news/insights/1016778 ; projection https://www.dimers.com/nfl/news/jared-goff-projected-fantasy-stats-nfl-week-5-2026-ac',
          'Daniels 210.5: https://www.legalsportsreport.com/nfl/nfl-player-prop-odds-week-5-props-for-weekend-matchups-mnf/ (snippet mislabeled the opponent; treat as low reliability)',
          'Wilson over 70: https://www.fantasylife.com/articles/betting/nfl-player-props-week-5 ; St. Brown/Olave 80/70: https://www.squawka.com (editorial picks)',
          'Chase Brown 65.5: https://www.fantasyalarm.com/articles/nfl/predictions/bengals-vs-dolphins-predictions-picks-odds-nfl-week-5-10-11-2026/196620',
          'Lamar out: https://www.thefantasyfootballers.com/news/641531/lamar-jackson-officially-ruled-out-for-week-5/',
          'Data: https://github.com/nflverse/nflverse-data/releases (stats_player_week_YYYY.csv, games.csv)']:
    a('* ' + t)
a('')
a('## 6. Reproduce')
a('')
a('`cd /tmp/claude-0/-home-user-fantastic-octo-computing-machine/fd837da0-fc17-5f70-a6ad-c31478ee2717/scratchpad/nfl/props` then run (python = scratchpad/oklahoma/.venv): `backtest.py` (validation) -> `project.py` (fit + candidates) -> `DROP="Jayden Daniels:2026" OUT_SUFFIX=_daniels project.py` (Daniels adj.) -> `final.py` (exclusions, edges) -> `report.py`. Files: `projections.csv` (mean/median/SD/alpha + cut-offs), `projection_lines.csv` (P(over) grid), `edge_check_all_sides.csv`, `backtest_results.txt`.')
open(BASE + '/report.md', 'w').write('\n'.join(L))
print('wrote report.md', len(L), 'lines')
print(E[E.edge > 0][['player', 'stat', 'side', 'line', 'price', 'p_model', 'p_blend', 'break_even', 'edge', 'quarter_kelly_pct_bankroll']].to_string())
print(THR)
