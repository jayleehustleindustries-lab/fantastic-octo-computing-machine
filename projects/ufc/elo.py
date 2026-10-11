import numpy as np, pandas as pd
from common import *

def elo_run(fr, K=30., boost=1.0, nboost=3, scale=400., init=1500.):
    """Chronological Elo. Returns pre-fight P(A wins) per fight (same order as fr) and final ratings."""
    R, N = {}, {}
    pA = np.full(len(fr), np.nan)
    for date, g in fr.groupby('date', sort=True):
        upd = []
        for i, a, b, res in zip(g.index, g.kA, g.kB, g.result):
            ra, rb = R.get(a, init), R.get(b, init)
            e = 1 / (1 + 10 ** ((rb - ra) / scale)); pA[i] = e
            if not np.isnan(res): upd.append((a, b, e, res))
        for a, b, e, res in upd:   # apply after whole card is predicted (no same-day leakage)
            ka = K * (boost if N.get(a, 0) < nboost else 1); kb = K * (boost if N.get(b, 0) < nboost else 1)
            ra, rb = R.get(a, init), R.get(b, init)
            R[a] = ra + ka * (res - e); R[b] = rb - kb * (res - e)
            N[a] = N.get(a, 0) + 1; N[b] = N.get(b, 0) + 1
    return pA, R, N

if __name__ == '__main__':
    import json
    fr = pd.read_pickle(f'{DATA}/fights.pkl').sort_values(['date', 'fid']).reset_index(drop=True)
    msk = (fr.date >= '2011-01-01') & (fr.date < TRAIN_END) & fr.result.isin([0., 1.])
    y = fr.result[msk].values
    out = []
    for K in (10, 15, 20, 25, 30, 40, 50, 60, 75, 90, 110, 130):
        for boost in (1.0, 1.25, 1.5, 2.0):
            pA, _, _ = elo_run(fr, K, boost)
            out.append((K, boost, ll(y, pA[msk.values]), brier(y, pA[msk.values]), acc(y, pA[msk.values])))
    t = pd.DataFrame(out, columns=['K', 'boost', 'logloss', 'brier', 'acc']).sort_values('logloss')
    print(t.to_string(index=False))
    best = t.iloc[0]
    json.dump({'K': float(best.K), 'boost': float(best.boost)}, open(f'{BASE}/elo_params.json', 'w'))
    t.to_csv(f'{BASE}/elo_tuning.csv', index=False)
    print('50% baseline logloss', ll(y, np.full(len(y), .5)))
