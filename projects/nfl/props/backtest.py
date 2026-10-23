"""Out-of-sample validation: fit on 2023-2024 + 2025 wk1-5, test on 2025 weeks 6-18."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user-fantastic-octo-computing-machine/fd837da0-fc17-5f70-a6ad-c31478ee2717/scratchpad/nfl/props')
from common import *

pg = assign_roles(build())
pg.to_pickle(BASE + '/pg_hist.pkl')
train = ((pg.season == 2023) | (pg.season == 2024) | ((pg.season == 2025) & (pg.week <= 5)))
test = (pg.season == 2025) & (pg.week >= 6) & (pg.week <= 18)
out_lines = []
allrows = []


def lines_for(stat, med):
    if stat in ('pass_yds', 'rush_yds', 'rec_yds'):
        res = []
        for dd in (-0.20, -0.10, 0.0, 0.10, 0.20):
            res.append((f'{dd:+.0%}', np.floor(med * (1 + dd)) + 0.5))
        return res
    if stat == 'pass_tds':
        return [('0.5', np.full_like(med, 0.5)), ('1.5', np.full_like(med, 1.5)), ('2.5', np.full_like(med, 2.5))]
    return [(f'{j:+d}', np.floor(med) + 0.5 + j) for j in (-2, -1, 0, 1, 2)]


summary = {}
for stat, cfg in STATS.items():
    m = StatModel(stat).fit(pg, train)
    mu, mu0, alpha, den = m.predict(pg)
    col = cfg['col']; role = cfg['role']
    sel = test & (pg.role == role) & pg[col].notna()
    d = pg[sel].copy(); y = d[col].values.astype(float)
    mu_s, mu0_s, al_s = mu[sel.values], mu0[sel.values], alpha[sel.values]
    # naive baseline: season-agnostic ewma with same dispersion params (no opp/script adj)
    al0 = np.clip(np.exp(m.a[0] + m.a[1] * np.log(mu0_s / m.mbar)), 1e-3, 5)
    # simple "last-N season avg" baseline: unshrunk ew mean hl=8
    num, den8 = ew_all(pg, col, 8)
    naive = np.where(den8 > 0, num / np.maximum(den8, 1e-9), np.nan)[sel.values]
    ok = ~np.isnan(naive)
    mae_full = np.mean(np.abs(y - mu_s)); mae_p = np.mean(np.abs(y - mu0_s)); mae_n = np.mean(np.abs(y[ok] - naive[ok]))
    rm_full = np.sqrt(np.mean((y - mu_s) ** 2)); rm_p = np.sqrt(np.mean((y - mu0_s) ** 2)); rm_n = np.sqrt(np.mean((y[ok] - naive[ok]) ** 2))
    yc = np.maximum(y, 0); ll_full = np.mean(nb_ll(yc, mu_s, al_s)); ll_p = np.mean(nb_ll(yc, mu0_s, al0))
    med = median_nb(mu_s, al_s)
    frac_gt_med = np.mean(y > med); frac_eq = np.mean(y == med)
    hdr = (f'\n=== {stat} (role {role}) | n_train={m.params["n_train"]} n_test={len(y)} | hl={m.hl} k={m.k} '
           f'beta={np.round(m.beta, 3).tolist()} alpha(mu=mbar)={np.exp(m.a[0]):.3f} slope={m.a[1]:.2f}\n'
           f'MAE full={mae_full:.2f} shrunk-ewma-only={mae_p:.2f} naive-ewma={mae_n:.2f} | RMSE full={rm_full:.2f} ewma-only={rm_p:.2f} naive={rm_n:.2f}\n'
           f'NB mean log-lik: full={ll_full:.4f} ewma-only={ll_p:.4f}  | mean(y)={y.mean():.2f} mean(mu)={mu_s.mean():.2f}\n'
           f'P(y > model median): {frac_gt_med:.3f}  P(y == median): {frac_eq:.3f}  P(y < median): {1 - frac_gt_med - frac_eq:.3f}')
    out_lines.append(hdr)
    rows = []
    for lab, L in lines_for(stat, med.astype(float)):
        p = p_over(mu_s, al_s, L); pp = p_over(mu0_s, al0, L)
        over = (y > L).astype(float)  # half-point lines mostly; whole lines: push -> counts as 'not over'
        push = (y == L)
        keep = ~push
        rows.append(dict(stat=stat, offset=lab, n=int(keep.sum()), pred=float(p[keep].mean()), obs=float(over[keep].mean()),
                         brier=float(np.mean((p[keep] - over[keep]) ** 2)), brier_ewma_only=float(np.mean((pp[keep] - over[keep]) ** 2))))
        allrows.append(pd.DataFrame(dict(stat=stat, offset=lab, p=p[keep], pp=pp[keep], over=over[keep])))
    t = pd.DataFrame(rows)
    out_lines.append(t.round(4).to_string(index=False))
    summary[stat] = m.params
    # fit-quality by week
    d['mu'] = mu_s; d['y'] = y
    d.to_pickle(BASE + f'/test_{stat}.pkl')

A = pd.concat(allrows)
A['side_p'] = np.where(A.p >= 0.5, A.p, 1 - A.p)
A['side_hit'] = np.where(A.p >= 0.5, A.over, 1 - A.over)
bins = [0, .3, .4, .45, .5, .55, .6, .65, .7, .8, 1.0]
A['bin'] = pd.cut(A.p, bins)
rel = A.groupby('bin', observed=True).agg(n=('over', 'size'), pred=('p', 'mean'), obs=('over', 'mean')).round(4)
out_lines.append('\n=== Reliability: P(over) predicted vs observed, ALL stats/offset lines pooled ===\n' + rel.to_string())
out_lines.append('\n=== Same, by stat (predicted-P bins) ===')
for stat in STATS:
    B = A[A.stat == stat].copy()
    B['bin'] = pd.cut(B.p, [0, .3, .4, .5, .6, .7, 1.0])
    out_lines.append(stat + '\n' + B.groupby('bin', observed=True).agg(n=('over', 'size'), pred=('p', 'mean'), obs=('over', 'mean')).round(3).to_string())
# the 'filter' bucket: legs where model side prob >= thresholds
rows = []
for th in (0.55, 0.60, 0.66, 0.70, 0.76):
    s = A[A.side_p >= th]
    rows.append(dict(model_side_prob_ge=th, n=len(s), mean_pred=s.side_p.mean(), hit_rate=s.side_hit.mean()))
out_lines.append('\n=== High-confidence side buckets (side = model-preferred side at the offset line) ===\n' + pd.DataFrame(rows).round(4).to_string(index=False))
# overall brier / logloss vs ewma-only
eps = 1e-6
def ll(p, o): p = np.clip(p, eps, 1 - eps); return -np.mean(o * np.log(p) + (1 - o) * np.log(1 - p))
out_lines.append(f'\nPooled log-loss at offset lines: full model={ll(A.p, A.over):.4f}  ewma-only={ll(A.pp, A.over):.4f}  '
                 f'(always-50% = {np.log(2):.4f}; note lines are centred on the full-model median so 50% is not a market benchmark)')
txt = '\n'.join(out_lines)
open(BASE + '/backtest_results.txt', 'w').write(txt)
json.dump(summary, open(BASE + '/params_train_only.json', 'w'), indent=1)
print(txt)
