"""B. Method / duration model (3-round-equivalent finish probabilities + 5-round extension)."""
import json, numpy as np, pandas as pd
from common import *

def target(f):
    """3-round-equivalent class: 0=DEC (incl. 5-rd fights going past rd 3), 1=KO, 2=SUB; NaN if invalid."""
    valid = (f.fmt3 | f.fmt5) & f.method.isin(['DEC', 'KO', 'SUB']) & ~f.tonight
    t = np.where(f.method == 'KO', 1, np.where(f.method == 'SUB', 2, 0))
    late = f.fmt5 & (f.ROUND > 3)
    t = np.where(late, 0, t)
    return pd.Series(np.where(valid, t, np.nan), index=f.index)

def method_probs(f, n0=8., alpha=1.0, k_div=40., use_div=True, use_fighter=True):
    gk = np.where(f.gm_n > 0, f.gm_ko / f.gm_n.clip(lower=1), .27); gs = np.where(f.gm_n > 0, f.gm_sub / f.gm_n.clip(lower=1), .17)
    if use_div:
        pko = shr(f.dm_ko, f.dm_n, k_div, gk); psub = shr(f.dm_sub, f.dm_n, k_div, gs)
    else: pko, psub = pd.Series(gk, index=f.index), pd.Series(gs, index=f.index)
    hk, hs = pko / 2, psub / 2
    out = {}
    for tag, (a, b) in (('ko', ('ko_for', 'ko_ag')), ('sub', ('sub_for', 'sub_ag'))):
        h = hk if tag == 'ko' else hs
        fa, ga = shr(f['a_' + a], f.a_nm, n0, h), shr(f['a_' + b], f.a_nm, n0, h)
        fb, gb = shr(f['b_' + a], f.b_nm, n0, h), shr(f['b_' + b], f.b_nm, n0, h)
        pa = h + alpha * (0.5 * (fa + gb) - h); pb = h + alpha * (0.5 * (fb + ga) - h)
        out[tag + '_A'] = pa.clip(lower=.004); out[tag + '_B'] = pb.clip(lower=.004)
    P = pd.DataFrame(out)
    if not use_fighter:
        P = pd.DataFrame({'ko_A': hk, 'ko_B': hk, 'sub_A': hs, 'sub_B': hs})
    P['p_ko'] = P.ko_A + P.ko_B; P['p_sub'] = P.sub_A + P.sub_B
    s = P.p_ko + P.p_sub; over = (s > .95)
    P.loc[over, ['ko_A', 'ko_B', 'sub_A', 'sub_B', 'p_ko', 'p_sub']] *= (.95 / s[over]).values[:, None]
    P['p_dec'] = 1 - P.p_ko - P.p_sub
    return P

def mlogloss(t, P):
    pr = np.where(t == 0, P.p_dec, np.where(t == 1, P.p_ko, P.p_sub))
    return float(-np.log(np.clip(pr, 1e-6, 1)).mean())

def tune(f):
    t = target(f); ok = t.notna()
    tr = ok & (f.date >= '2011-01-01') & (f.date < '2021-01-01'); va = ok & (f.date >= '2021-01-01') & (f.date < TRAIN_END)
    rows = []
    for n0 in (6, 10, 16, 30, 50):
        for al in (1.0, 1.5, 2.0, 2.5, 3.0, 4.0):
            P = method_probs(f[va], n0, al); rows.append((n0, al, mlogloss(t[va], P)))
    # also vs division-only, global-only
    d = pd.DataFrame(rows, columns=['n0', 'alpha', 'val_mlogloss']).sort_values('val_mlogloss')
    base_div = mlogloss(t[va], method_probs(f[va], use_fighter=False)); base_g = mlogloss(t[va], method_probs(f[va], use_fighter=False, use_div=False))
    return d, base_div, base_g

def late_stats(fr_hist):
    """Time supports + survival from history (fights strictly before cutoff)."""
    h = fr_hist[fr_hist.method.isin(['DEC', 'KO', 'SUB'])]
    e = h[(h.method != 'DEC') & (h.minutes <= 15.0001) & (h.fmt3 | h.fmt5)].minutes.values
    f5 = h[h.fmt5]; late = f5[(f5.method != 'DEC') & (f5.ROUND > 3)].minutes.values
    f5r = f5[f5.date >= '2018-01-01']; reach4 = f5r[(f5r.method == 'DEC') | (f5r.ROUND > 3)]   # modern-era survival of rounds 4-5
    S45 = float((reach4.method == 'DEC').mean())
    qe = np.quantile(e, (np.arange(30) + .5) / 30); ql = np.quantile(late, (np.arange(10) + .5) / 10)
    return dict(S45=S45, qe=qe, ql=ql, n_early=len(e), n_late=len(late), n_reach4=len(reach4), late_ko_share=float((f5[(f5.method != 'DEC') & (f5.ROUND > 3)].method == 'KO').mean()))

def time_mixture(P, is5, ls):
    """Return (T support (m,), W weights (n,m)) mixture over fight minutes, plus P(distance) per row."""
    n = len(P); pdec3 = P.p_dec.values
    T = np.concatenate([ls['qe'], ls['ql'], [15.0, 25.0]]); W = np.zeros((n, len(T)))
    is5 = np.asarray(is5, bool)
    pfin3 = 1 - pdec3
    W[:, :30] = (pfin3 / 30)[:, None]
    # 3-round: decision at 15
    W[~is5, -2] = pdec3[~is5]
    # 5-round: late finishes and decision at 25
    plate = pdec3 * (1 - ls['S45']); pd5 = pdec3 * ls['S45']
    W[is5, 30:40] = (plate[is5] / 10)[:, None]; W[is5, -1] = pd5[is5]
    pdist = np.where(is5, pd5, pdec3)
    return T, W, pdist

def median_time(T, W):
    o = np.argsort(T); Ts, Ws = T[o], W[:, o]; c = Ws.cumsum(axis=1)
    idx = (c >= .5 - 1e-12).argmax(axis=1); return Ts[idx]

if __name__ == '__main__':
    f = pd.read_pickle(f'{DATA}/feat.pkl'); t = target(f)
    d, bd, bg = tune(f); print(d.head(8)); print('division-only val mlogloss', bd, 'global-only', bg)
    n0, al = float(d.iloc[0].n0), float(d.iloc[0].alpha)
    ho = t.notna() & (f.date >= TRAIN_END)
    hist = pd.read_pickle(f'{DATA}/fights.pkl'); ls = late_stats(hist[hist.date < TRAIN_END])
    print({k: (v if not isinstance(v, np.ndarray) else v.round(2)[:3]) for k, v in ls.items()})
    P = method_probs(f[ho], n0, al); Pd = method_probs(f[ho], use_fighter=False); Pg = method_probs(f[ho], use_fighter=False, use_div=False)
    th = t[ho]
    # 3-round-equivalent metrics; P(distance) metrics on actual 3-round fights; 5-round fights separately
    isdec = (th == 0).astype(float).values
    res = {'n0': n0, 'alpha': al, 'n_hold': int(ho.sum())}
    for nm, PP in (('fighter+division', P), ('division base only', Pd), ('global base only', Pg)):
        res[nm] = dict(mlogloss=mlogloss(th, PP), dist_logloss=ll(isdec, PP.p_dec.values), dist_brier=brier(isdec, PP.p_dec.values),
                       ko_brier=brier((th == 1).astype(float), PP.p_ko.values), sub_brier=brier((th == 2).astype(float), PP.p_sub.values))
    res['const_dist_logloss'] = ll(isdec, np.full(len(isdec), isdec.mean()))
    print(json.dumps(res, indent=1))
    cal = calib(isdec, P.p_dec.values); print(cal)
    # 5-round check
    ff = f[ho]; m5 = ff.fmt5.values
    T, W, pdist = time_mixture(P, ff.fmt5.values, ls)
    act_dist = np.where(ff.fmt5.values, (ff.method == 'DEC').values, (ff.method == 'DEC').values).astype(float)
    res['dist_all_formats'] = dict(logloss=ll(act_dist, pdist), brier=brier(act_dist, pdist), mean_pred=float(pdist.mean()), observed=float(act_dist.mean()), n=len(pdist),
                                   five_rd_n=int(m5.sum()), five_rd_mean_pred=float(pdist[m5].mean()), five_rd_observed=float(act_dist[m5].mean()),
                                   three_rd_mean_pred=float(pdist[~m5].mean()), three_rd_observed=float(act_dist[~m5].mean()))
    print(res['dist_all_formats'])
    cal_all = calib(act_dist, pdist); print(cal_all)
    # time check: median predicted vs actual fight time
    med = median_time(T, W)
    ET = (W * T[None, :]).sum(axis=1)
    cdf5 = (W * (T[None, :] <= 5.0001)).sum(axis=1); cdf10 = (W * (T[None, :] <= 10.0001)).sum(axis=1)
    res['time_check'] = dict(mean_pred_E_time=float(ET.mean()), actual_mean_time=float(ff.minutes.mean()), pred_P_le5=float(cdf5.mean()), obs_P_le5=float((ff.minutes <= 5.0001).mean()),
                             pred_P_le10=float(cdf10.mean()), obs_P_le10=float((ff.minutes <= 10.0001).mean()), mean_pred_median_time=float(med.mean()))
    print(res['time_check'])
    # by division x gender table on holdout
    g = ff[['divg']].copy(); g['t'] = th.values; g['p_dec'] = P.p_dec.values; g['p_ko'] = P.p_ko.values; g['p_sub'] = P.p_sub.values
    g['b_dec'] = Pd.p_dec.values; g['b_ko'] = Pd.p_ko.values; g['b_sub'] = Pd.p_sub.values
    tab = g.groupby('divg').agg(n=('t', 'size'), obs_dec=('t', lambda s: (s == 0).mean()), pred_dec=('p_dec', 'mean'), base_dec=('b_dec', 'mean'),
                                obs_ko=('t', lambda s: (s == 1).mean()), pred_ko=('p_ko', 'mean'), base_ko=('b_ko', 'mean'),
                                obs_sub=('t', lambda s: (s == 2).mean()), pred_sub=('p_sub', 'mean'), base_sub=('b_sub', 'mean')).reset_index()
    print(tab.round(3).to_string())
    tab.to_csv(f'{BASE}/method_by_division_holdout.csv', index=False); cal.to_csv(f'{BASE}/calib_dist_3rd_eq.csv', index=False); cal_all.to_csv(f'{BASE}/calib_dist_all.csv', index=False)
    res['hist_late_stats'] = {k: (v if not isinstance(v, np.ndarray) else v.tolist()) for k, v in ls.items()}
    json.dump(res, open(f'{BASE}/method_metrics.json', 'w'), indent=1)
    d.to_csv(f'{BASE}/method_tuning.csv', index=False)
