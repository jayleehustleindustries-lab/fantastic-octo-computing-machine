"""C. Per-fighter sig-strike and takedown count models (negative binomial) + mixture over fight time."""
import json, numpy as np, pandas as pd, warnings
from scipy.optimize import minimize
from scipy.special import gammaln
from scipy.stats import nbinom
from common import *
from methodmodel import *
warnings.filterwarnings('ignore')

def long_rows(f, ff, lam, pmin, ptd):
    dm = div_means(f)
    ra = fighter_rates(f, 'a', lam, dm, pmin, ptd); rb = fighter_rates(f, 'b', lam, dm, pmin, ptd)
    out = []
    for side, own, opp in (('A', ra, rb), ('B', rb, ra)):
        d = pd.DataFrame({'fid': f.fid.values, 'side': side, 'date': f.date.values, 'tonight': f.tonight.values, 'idx': f.index.values,
                          'own_sl': own.sl_pm.values, 'opp_sa': opp.sa_pm.values, 'own_td': own.td_pm.values, 'opp_tdabs': opp.tdabs_pm.values,
                          'opp_tdd': opp.tdd.values, 'mu_sl': dm.sl.values, 'mu_td': dm.td.values, 'mu_tdacc': dm.tdacc.values, 'divg': f.divg.values})
        out.append(d)
    L = pd.concat(out, ignore_index=True)
    L = L.merge(ff[['fid', 'side', 'sl', 'tl', 'minutes', 'has_stats']], on=['fid', 'side'], how='left')
    L['has_stats'] = L.has_stats.fillna(False).astype(bool)
    return L

def design(L, kind):
    if kind == 'sl':
        X = np.column_stack([np.ones(len(L)), np.log(L.own_sl / L.mu_sl), np.log(L.opp_sa / L.mu_sl)]); off = np.log(L.mu_sl.values)
    else:
        X = np.column_stack([np.ones(len(L)), np.log(L.own_td / L.mu_td), np.log(L.opp_tdabs / L.mu_td), np.log((1 - L.opp_tdd).clip(lower=.02) / L.mu_tdacc)]); off = np.log(L.mu_td.values)
    return X, off

def nb_ll(y, mu, alpha):
    r = 1 / alpha
    return gammaln(y + r) - gammaln(r) - gammaln(y + 1) + r * np.log(r / (r + mu)) + y * np.log(mu / (r + mu))

def fit_nb(L, kind, null=False):
    X, off = design(L, kind); y = L['sl' if kind == 'sl' else 'tl'].values; lt = np.log(L.minutes.clip(lower=.05).values)
    k = X.shape[1]
    if null: X = X[:, :1]; k = 1
    def nll(th):
        eta = X @ th[:k] + th[k] * lt + off; mu = np.exp(np.clip(eta, -12, 8))
        return -nb_ll(y, mu, np.exp(th[k + 1])).sum()
    x0 = np.zeros(k + 2); x0[k] = 1.0; x0[k + 1] = np.log(.2)
    r = minimize(nll, x0, method='L-BFGS-B')
    return dict(beta=r.x[:k], gamma=r.x[k], alpha=float(np.exp(r.x[k + 1])), null=null, kind=kind, nll=r.fun / len(y))

def base_mu(L, par):
    X, off = design(L, par['kind'])
    if par['null']: X = X[:, :1]
    return np.exp(np.clip(X @ par['beta'] + off, -12, 8))

def row_nll(L, par):
    y = L['sl' if par['kind'] == 'sl' else 'tl'].values
    mu = base_mu(L, par) * L.minutes.clip(lower=.05).values ** par['gamma']
    return float(-nb_ll(y, mu, par['alpha']).mean())

def mix_cdf(ks, base, par, T, W, chunk=250):
    out = np.zeros((len(base), len(ks)))
    for s in range(0, len(base), chunk):
        b = base[s:s + chunk, None] * (T[None, :] ** par['gamma'])           # (n, m)
        r = 1 / par['alpha']; p = r / (r + b)
        c = nbinom.cdf(np.asarray(ks)[None, :, None], r, p[:, None, :])      # (n, K, m)
        out[s:s + chunk] = (c * W[s:s + chunk, None, :]).sum(axis=2)
    return out

def tune(f, ff):
    rows = []
    for kind, grid in (('sl', [(l, p, 60.) for l in (1.0, .8, .6) for p in (15., 30., 60.)]), ('td', [(l, 30., p) for l in (1.0, .8) for p in (5., 10., 20., 40.)])):
        for lam, pmin, ptd in grid:
            L = long_rows(f, ff, lam, pmin, ptd); ok = L.has_stats & (L.minutes > 0) & ~L.tonight
            tr = ok & (L.date >= '2011-01-01') & (L.date < '2021-01-01'); va = ok & (L.date >= '2021-01-01') & (L.date < TRAIN_END)
            par = fit_nb(L[tr], kind); rows.append((kind, lam, pmin, ptd, row_nll(L[va], par), row_nll(L[va], fit_nb(L[tr], kind, null=True))))
    return pd.DataFrame(rows, columns=['kind', 'lam', 'p_min', 'p_td', 'val_nll', 'val_nll_null'])
