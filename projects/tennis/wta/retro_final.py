"""Retrospective (post-hoc, NOT bettable) run for the Beijing final Andreeva vs Zheng, 2026-10-11 11:30 UTC.
Inputs are the PRE-MATCH public numbers found via WebSearch snippets (no book logins).
"""
import json, numpy as np, wta_mc as m

def novig2(a, b):
    return a/(a+b), b/(a+b)
def am2p(o):  # american -> implied prob
    return 100/(o+100) if o > 0 else -o/(-o+100)
def am2dec(o):
    return 1+o/100 if o > 0 else 1+100/(-o)

# --- moneyline consensus (snippets: Sportskeeda & SportyTrader -175/+135; Matchstat 1.66/2.28; Tennistonic open 1.57/2.42; Polymarket 60/40)
srcs = {
 'Sportskeeda/SportyTrader (-175/+135)': novig2(am2p(-175), am2p(135)),
 'Matchstat dec (1.66/2.28)': novig2(1/1.66, 1/2.28),
 'Tennistonic open dec (1.57/2.42)': novig2(1/1.57, 1/2.42),
 'Polymarket (0.60/0.40)': (0.60, 0.40),
}
for k,v in srcs.items(): print(f"{k:42s} Andreeva {v[0]:.4f}  Zheng {v[1]:.4f}")
p_mkt = float(np.mean([v[0] for v in srcs.values()]))
p_mkt_main = srcs['Sportskeeda/SportyTrader (-175/+135)'][0]
p_model = 0.611   # StringTension Elo-based 2026 H2H model (found via search snippet; only independent model number available)
w = 0.3
p_blend = w*p_model + (1-w)*p_mkt
print(f"consensus novig Andreeva (avg of 4 srcs) {p_mkt:.4f}; main-line novig {p_mkt_main:.4f}; p_model {p_model}; p_blend {p_blend:.4f}")
for side, p, price in (('Andreeva ML -175', p_blend, am2dec(-175)), ('Zheng ML +135', 1-p_blend, am2dec(135))):
    be = 1/price
    print(f"{side}: p_blend {p:.3f}  break-even {be:.3f}  edge {p*price-1:+.3%}  quarter-Kelly f {max(0,(p*price-1)/(price-1))/4:.4f}")

# --- sim at p_blend and at p_market
res = {}
for label, p in (('p_blend', p_blend), ('p_market_main', p_mkt_main), ('p_model', p_model)):
    d = m.solve_symmetric(p, n=300000)
    r = m.simulate(m.MU+d, (1-m.MU)+d, m.MU-d, (1-m.MU)-d, n=600000, seed=5)
    s = m.summarize(r, ('Andreeva','Zheng'))
    res[label] = s
    print(f"\n== {label} p={p:.4f} gap d={d:.4f}")
    print({k: (round(v,4) if isinstance(v,float) else v) for k,v in s.items() if k in ('P_win_Andreeva','P_3sets','P_any_tiebreak','E_total','SD_total','E_games_Andreeva','E_games_Zheng','hold_Andreeva','hold_Zheng')})
    print('P(over):', {k: round(v,3) for k,v in s['P_over'].items()})
    print('P(Zheng games>x):', {k: round(v,3) for k,v in s['P_games_Zheng_over'].items()})
    print('P(Andreeva games>x):', {k: round(v,3) for k,v in s['P_games_Andreeva_over'].items()})
    print('Andreeva handicap cover:', {k: round(v,3) for k,v in s['P_handicap_cover_Andreeva'].items()})

# --- totals line: O21.5 -120 / U21.5 -110
po_novig = novig2(am2p(-120), am2p(-110))
print(f"\nTotals 21.5 market novig: over {po_novig[0]:.4f} under {po_novig[1]:.4f}")
s = res['p_blend']
p_over_model = s['P_over']['21.5']
p_over_blend = 0.3*p_over_model + 0.7*po_novig[0]
for side, p, price in (('Over 21.5 -120', p_over_blend, am2dec(-120)), ('Under 21.5 -110', 1-p_over_blend, am2dec(-110))):
    print(f"{side}: p_model {p_over_model if 'Over' in side else 1-p_over_model:.3f} p_blend {p:.3f} break-even {1/price:.3f} edge {p*price-1:+.3%}")
# Zheng +3.0 games (-115) / Andreeva -3.0 (-115) : integer line -> push possible; compute
r = m.simulate(*( [m.MU+m.solve_symmetric(p_blend,n=300000)]*0 ) , n=1) if False else None
d = m.solve_symmetric(p_blend, n=300000)
r = m.simulate(m.MU+d, (1-m.MU)+d, m.MU-d, (1-m.MU)-d, n=600000, seed=5)
diff = r['gamesA'] - r['gamesB']   # Andreeva - Zheng
pA_cov = float((diff > 3).mean()); pZ_cov = float((diff < 3).mean()); push = float((diff == 3).mean())
print(f"Game handicap 3.0: Andreeva -3.0 covers {pA_cov:.3f}, Zheng +3.0 covers {pZ_cov:.3f}, push {push:.3f}")
json.dump(res, open('retro_final_results.json','w'), indent=1, default=float)
