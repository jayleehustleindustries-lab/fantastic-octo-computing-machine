import json, numpy as np, pandas as pd, warnings
from sklearn.linear_model import LogisticRegression
from common import *
warnings.filterwarnings('ignore')

FEATS = ['elo', 'age', 'reach', 'height', 'exp', 'days', 'sl_pm', 'sa_pm', 'td15', 'tdd', 'sub15', 'l3_win', 'l3_diff']
def make_X(f):
    dm = div_means(f)
    ra, rb = fighter_rates(f, 'a', 1.0, dm), fighter_rates(f, 'b', 1.0, dm)
    X = pd.DataFrame(index=f.index)
    X['elo'] = (f.a_elo - f.b_elo) / 100
    age_med = f.groupby('gender')[['a_age', 'b_age']].transform('median').mean(axis=1)
    X['age'] = (f.a_age - f.b_age).fillna(0)
    # reach: impute from height when missing (division median reach-height gap), diff 0 if unknown
    gap = (pd.concat([f.a_reach - f.a_height, f.b_reach - f.b_height]).median())
    ar = f.a_reach.fillna(f.a_height + gap); br = f.b_reach.fillna(f.b_height + gap)
    X['reach'] = (ar - br).fillna(0); X['height'] = (f.a_height - f.b_height).fillna(0)
    X['exp'] = np.log1p(f.a_nf) - np.log1p(f.b_nf)
    X['days'] = (f.a_days_since.fillna(365).clip(upper=730) - f.b_days_since.fillna(365).clip(upper=730)) / 365
    X['sl_pm'] = ra.sl_pm - rb.sl_pm; X['sa_pm'] = ra.sa_pm - rb.sa_pm
    X['td15'] = 15 * (ra.td_pm - rb.td_pm); X['tdd'] = ra.tdd - rb.tdd
    X['sub15'] = 15 * (ra.sub_pm - rb.sub_pm)
    X['l3_win'] = f.a_l3_win.fillna(.5) - f.b_l3_win.fillna(.5)
    X['l3_diff'] = f.a_l3_diff_pm.fillna(0) - f.b_l3_diff_pm.fillna(0)
    return X[FEATS]

def fit_sym(X, y, C, cols):
    """Antisymmetric logistic: no intercept, trained on both orientations."""
    Xa = np.vstack([X[cols].values, -X[cols].values]); ya = np.concatenate([y, 1 - y])
    sd = X[cols].std().values + 1e-9
    m = LogisticRegression(C=C, fit_intercept=False, max_iter=2000).fit(Xa / sd, ya)
    return m, sd
def pred_sym(m, sd, X, cols): return m.predict_proba(X[cols].values / sd)[:, 1]

def run():
    f = pd.read_pickle(f'{DATA}/feat.pkl')
    X = make_X(f)
    ok = f.result.isin([0., 1.]) & ~f.tonight
    tr = ok & (f.date >= '2011-01-01') & (f.date < TRAIN_END)
    ho = ok & (f.date >= TRAIN_END)
    y = f.result.values
    # choose C by time-split validation inside training
    sub_tr = tr & (f.date < '2021-01-01'); sub_va = tr & (f.date >= '2021-01-01')
    rows = []
    for C in (0.003, 0.01, 0.03, 0.1, 0.3, 1.0):
        m, sd = fit_sym(X[sub_tr], y[sub_tr], C, FEATS)
        rows.append((C, ll(y[sub_va], pred_sym(m, sd, X[sub_va], FEATS))))
    cv = pd.DataFrame(rows, columns=['C', 'val_logloss']); print(cv)
    C = float(cv.sort_values('val_logloss').iloc[0].C)
    m, sd = fit_sym(X[tr], y[tr], C, FEATS)
    p_full = pred_sym(m, sd, X, FEATS)
    # Elo-only logistic (calibrated Elo diff, antisymmetric)
    me, sde = fit_sym(X[tr], y[tr], 1.0, ['elo']); p_elo_cal = pred_sym(me, sde, X, ['elo'])
    yh = y[ho]; res = {}
    for name, p in (('Full model (LR)', p_full[ho]), ('Elo only (raw expectation)', f.elo_pA[ho].values),
                    ('Elo only (calibrated LR on Elo diff)', p_elo_cal[ho]), ('50% baseline', np.full(ho.sum(), .5))):
        res[name] = dict(logloss=ll(yh, p), brier=brier(yh, p), accuracy=acc(yh, p) if name != '50% baseline' else .5, n=int(ho.sum()))
    # bootstrap SE of logloss difference vs Elo and vs 50%
    rng = np.random.default_rng(0); n = len(yh); d_e, d_b = [], []
    for _ in range(1000):
        i = rng.integers(0, n, n)
        d_e.append(ll(yh[i], f.elo_pA[ho].values[i]) - ll(yh[i], p_full[ho][i])); d_b.append(ll(yh[i], np.full(n, .5)) - ll(yh[i], p_full[ho][i]))
    res['_diff'] = dict(ll_gain_vs_elo=float(np.mean(d_e)), ll_gain_vs_elo_ci=[float(np.percentile(d_e, 2.5)), float(np.percentile(d_e, 97.5))],
                        ll_gain_vs_50=float(np.mean(d_b)), ll_gain_vs_50_ci=[float(np.percentile(d_b, 2.5)), float(np.percentile(d_b, 97.5))])
    # calibration (use both orientations -> p of the favourite side is more informative; but follow request: 5 bins on pA, and on fav)
    cal_full = calib(yh, p_full[ho]); cal_elo = calib(yh, f.elo_pA[ho].values)
    # favourite-oriented calibration
    fav = np.where(p_full[ho] >= .5, p_full[ho], 1 - p_full[ho]); fy = np.where(p_full[ho] >= .5, yh, 1 - yh)
    cal_fav = calib(fy, fav)
    yrs = f[ho].date.dt.year.values; by_year = []
    for yv in sorted(set(yrs)):
        mk = yrs == yv
        by_year.append(dict(year=int(yv), n=int(mk.sum()), model_ll=ll(yh[mk], p_full[ho][mk]), elo_ll=ll(yh[mk], f.elo_pA[ho].values[mk]), base_ll=.693147,
                            model_acc=acc(yh[mk], p_full[ho][mk]), elo_acc=acc(yh[mk], f.elo_pA[ho].values[mk])))
    print(pd.DataFrame(by_year))
    coefs = pd.Series(m.coef_[0] / sd, index=FEATS)
    coefs_std = pd.Series(m.coef_[0], index=FEATS)
    # tonight
    tn = f.tonight.values
    # refit on ALL data through the cutoff (same hyperparameters) for tonight's predictions
    tr_all = ok & (f.date >= '2011-01-01')
    m2, sd2 = fit_sym(X[tr_all], y[tr_all], C, FEATS); p_all = pred_sym(m2, sd2, X, FEATS)
    f_t = f[tn].copy(); f_t['p_model_pre2023fit'] = p_full[tn]; f_t['p_model'] = p_all[tn]; f_t['p_elo_raw'] = f.elo_pA[tn].values; f_t['p_elo_cal'] = p_elo_cal[tn]
    f_t[['nameA', 'nameB', 'p_model', 'p_model_pre2023fit', 'p_elo_raw', 'p_elo_cal', 'a_elo', 'b_elo']].to_pickle(f'{DATA}/tonight_win.pkl')
    json.dump(dict(res=res, C=C, coef_per_unit=coefs.to_dict(), coef_std=coefs_std.to_dict(), cv=cv.to_dict('records'),
                   by_year=by_year, n_train=int(tr.sum()), n_hold=int(ho.sum()), hold_start='2023-01-01', hold_end=str(f[ho].date.max().date())),
              open(f'{BASE}/win_metrics.json', 'w'), indent=1)
    cal_full.to_csv(f'{BASE}/calib_win_full.csv', index=False); cal_elo.to_csv(f'{BASE}/calib_win_elo.csv', index=False); cal_fav.to_csv(f'{BASE}/calib_win_fav.csv', index=False)
    print(json.dumps(res, indent=1)); print('C', C, 'train', tr.sum(), 'hold', ho.sum())
    print(coefs_std.round(3).to_string()); print(cal_full); print(cal_elo); print(cal_fav)
    print(f_t[['nameA', 'nameB', 'p_model', 'p_model_pre2023fit', 'p_elo_raw', 'p_elo_cal']])
if __name__ == '__main__': run()
