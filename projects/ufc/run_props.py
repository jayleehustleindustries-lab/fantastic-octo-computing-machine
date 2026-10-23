import json, numpy as np, pandas as pd
from propmodel import *
f = pd.read_pickle(f'{DATA}/feat.pkl'); ff = pd.read_pickle(f'{DATA}/ff.pkl'); fr = pd.read_pickle(f'{DATA}/fights.pkl')
tun = tune(f, ff); print(tun.round(4).to_string()); tun.to_csv(f'{BASE}/props_tuning.csv', index=False)
best = {}
for kind in ('sl', 'td'):
    b = tun[tun.kind == kind].sort_values('val_nll').iloc[0]; best[kind] = dict(lam=float(b.lam), p_min=float(b.p_min), p_td=float(b.p_td))
print(best)
mp = json.load(open(f'{BASE}/method_metrics.json')); n0, al = mp['n0'], mp['alpha']
ls_pre = late_stats(fr[fr.date < TRAIN_END])
res = {'best': best, 'n0': n0, 'alpha_method': al}
ho_f = f[(f.date >= TRAIN_END) & ~f.tonight & f.fmt3.astype(bool) | (f.date >= TRAIN_END) & ~f.tonight & f.fmt5.astype(bool)]
P = method_probs(f.loc[ho_f.index], n0, al); T, W, pdist = time_mixture(P, ho_f.fmt5.values, ls_pre)
Wd = pd.DataFrame(W, index=ho_f.fid.values)
for kind in ('sl', 'td'):
    b = best[kind]; L = long_rows(f, ff, b['lam'], b['p_min'], b['p_td']); ok = L.has_stats & (L.minutes > 0) & ~L.tonight
    tr = ok & (L.date >= '2011-01-01') & (L.date < TRAIN_END); ho = ok & (L.date >= TRAIN_END)
    par = fit_nb(L[tr], kind); par0 = fit_nb(L[tr], kind, null=True)
    r = {'beta': par['beta'].tolist(), 'gamma': par['gamma'], 'alpha': par['alpha'], 'null_gamma': par0['gamma'], 'null_alpha': par0['alpha'],
         'cond_nll_holdout': row_nll(L[ho], par), 'cond_nll_holdout_divmean_only': row_nll(L[ho], par0), 'n_train': int(tr.sum()), 'n_hold': int(ho.sum())}
    y = L.loc[ho, 'sl' if kind == 'sl' else 'tl'].values
    mu = base_mu(L[ho], par) * L.loc[ho, 'minutes'].values ** par['gamma']
    r['cond_mean_pred'] = float(mu.mean()); r['cond_mean_obs'] = float(y.mean())
    # full chain: mixture over predicted fight time
    Lh = L[ho].reset_index(drop=True); base = base_mu(Lh, par)
    okf = Lh.fid.isin(Wd.index).values; Lh, base, y = Lh[okf].reset_index(drop=True), base[okf], y[okf]
    Wr = Wd.loc[Lh.fid.values].values
    if kind == 'sl':
        ks = np.arange(0, 301); C = mix_cdf(ks, base, par, T, Wr)
        med = (C >= .5).argmax(axis=1); r['mean_pred_median'] = float(med.mean()); r['obs_mean'] = float(y.mean())
        r['frac_over_median_line'] = dict(P_gt_med_pred=float((1 - C[np.arange(len(med)), med]).mean()), P_gt_med_obs=float((y > med).mean()),
                                          P_ge_med_pred=float((1 - C[np.arange(len(med)), np.maximum(med - 1, 0)]).mean()), P_ge_med_obs=float((y >= med).mean()))
        offs = [-30, -20, -10, -5, 0, 5, 10, 20, 30]; tab = []; pool_p, pool_y = [], []
        for d in offs:
            k = np.clip(med + d, 0, 300); po = 1 - C[np.arange(len(med)), k]; yo = (y > k).astype(float)
            tab.append(dict(offset=d, mean_line=float((k + .5).mean()), mean_pred_over=float(po.mean()), obs_over=float(yo.mean()), logloss=ll(yo, po), brier=brier(yo, po)))
            pool_p.append(po); pool_y.append(yo)
        r['offset_table'] = tab
        r['pooled_calib'] = calib(np.concatenate(pool_y), np.concatenate(pool_p), 8).to_dict('records')
        fl = []
        for ln in (15, 25, 35, 45, 55, 70, 90, 110):
            po = 1 - C[:, ln]; yo = (y > ln).astype(float); fl.append(dict(line=ln + .5, mean_pred_over=float(po.mean()), obs_over=float(yo.mean())))
        r['fixed_lines'] = fl
        # PIT-like coverage: central 50%/80% interval
        q = lambda p: (C >= p).argmax(axis=1)
        r['coverage'] = {'p25_p75': float(((y >= q(.25)) & (y <= q(.75))).mean()), 'p10_p90': float(((y >= q(.10)) & (y <= q(.90))).mean()), 'below_p10': float((y < q(.10)).mean()), 'above_p90': float((y > q(.90)).mean())}
        # simple benchmark: P(over) from NB with null (division mean) model, same mixture
        base0 = base_mu(Lh, par0); C0 = mix_cdf(ks, base0, par0, T, Wr); med0 = (C0 >= .5).argmax(axis=1)
        pp, yy = [], []
        for d in (-20, -10, 0, 10, 20):
            k = np.clip(med + d, 0, 300); pp.append(1 - C0[np.arange(len(k)), k]); yy.append((y > k).astype(float))
        pp1, yy1 = [], []
        for d in (-20, -10, 0, 10, 20):
            k = np.clip(med + d, 0, 300); pp1.append(1 - C[np.arange(len(k)), k]); yy1.append((y > k).astype(float))
        r['logloss_over_pooled_model'] = ll(np.concatenate(yy1), np.concatenate(pp1)); r['logloss_over_pooled_divmean_model'] = ll(np.concatenate(yy1), np.concatenate([1 - C0[np.arange(len(k)), k] for d in (-20, -10, 0, 10, 20) for k in [np.clip(med + d, 0, 300)]]))
        r['mae_median'] = float(np.abs(y - med).mean()); r['mae_divmean_median'] = float(np.abs(y - med0).mean())
    else:
        ks = np.arange(0, 12); C = mix_cdf(ks, base, par, T, Wr); p0 = C[:, 0]; p1 = 1 - p0; p2 = 1 - C[:, 1]
        base0 = base_mu(Lh, par0); C0 = mix_cdf(ks, base0, par0, T, Wr)
        r['mean_pred_td'] = float(((1 - nbinom.cdf(-1, 1, .5)) * 0 + (np.arange(12)[None, :] * np.diff(np.hstack([np.zeros((len(C), 1)), C]), axis=1)).sum(axis=1).mean()))
        r['obs_mean_td'] = float(y.mean())
        for nm, pr, yo, pr0 in (('ge1', p1, (y >= 1).astype(float), 1 - C0[:, 0]), ('ge2', p2, (y >= 2).astype(float), 1 - C0[:, 1])):
            r[nm] = dict(mean_pred=float(pr.mean()), obs=float(yo.mean()), logloss=ll(yo, pr), brier=brier(yo, pr), logloss_divmean=ll(yo, pr0), brier_divmean=brier(yo, pr0),
                         logloss_const=ll(yo, np.full(len(yo), yo.mean())), calib=calib(yo, pr, 5).to_dict('records'))
    res[kind] = r
    print(kind, json.dumps({k: v for k, v in r.items() if k not in ('pooled_calib',)}, indent=1, default=float)[:3500])
json.dump(res, open(f'{BASE}/props_metrics.json', 'w'), indent=1, default=float)
