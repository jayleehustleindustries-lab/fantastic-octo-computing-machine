"""Reference grid: for a given pre-match P(win) of the favourite, model 3-set rate, E[total], P(total > L).
Use for tomorrow's Wuhan matches: take the no-vig/blended P(win), read off totals; compare with the posted total."""
import csv, numpy as np, wta_mc as m
rows = []
for p in (0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90):
    d = m.solve_symmetric(p, n=250000, seed=3)
    r = m.simulate(m.MU+d, (1-m.MU)+d, m.MU-d, (1-m.MU)-d, n=500000, seed=9)
    row = dict(p_fav=p, d=round(d,4), hold_fav=round(float(r['hA'].mean()),3), hold_dog=round(float(r['hB'].mean()),3),
               three_set=round(float((r['nsets']==3).mean()),3), tb_any=round(float((r['tbs']>0).mean()),3),
               E_total=round(float(r['total'].mean()),2), SD_total=round(float(r['total'].std()),2),
               E_fav_games=round(float(r['gamesA'].mean()),2), E_dog_games=round(float(r['gamesB'].mean()),2))
    for L in (18.5,19.5,20.5,21.5,22.5,23.5,24.5):
        row[f'over_{L}'] = round(float((r['total']>L).mean()),3)
    # fav wins in straight sets
    row['fav_2_0'] = round(float((r['winA'] & (r['nsets']==2)).mean()),3)
    rows.append(row)
with open('grid_pwin_totals.csv','w',newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
for r_ in rows: print(r_)
