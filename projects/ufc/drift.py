import pandas as pd, numpy as np, json
from propmodel import *
f = pd.read_pickle(f'{DATA}/feat.pkl'); ff = pd.read_pickle(f'{DATA}/ff.pkl')
tun = pd.read_csv(f'{BASE}/props_tuning.csv')
for kind, b in (('sl', dict(lam=1.0, p_min=30., p_td=60.)), ('td', dict(lam=.8, p_min=30., p_td=30.))):
    L = long_rows(f, ff, b['lam'], b['p_min'], b['p_td']); ok = L.has_stats & (L.minutes > 0) & ~L.tonight
    tr = ok & (L.date >= '2011-01-01') & (L.date < TRAIN_END); par = fit_nb(L[tr], kind)
    y = L['sl' if kind == 'sl' else 'tl']; mu = base_mu(L, par) * L.minutes.clip(lower=.05) ** par['gamma']
    d = pd.DataFrame({'yr': L.date.dt.year, 'y': y, 'mu': mu})[ok]
    print(kind, d.groupby('yr').apply(lambda g: pd.Series({'n': len(g), 'obs': g.y.mean(), 'pred': g.mu.mean(), 'ratio': g.y.sum() / g.mu.sum()})).tail(8).round(3).to_string())
