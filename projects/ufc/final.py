"""Tonight's projections: refit on all data through the cutoff, then project the 5 fights -> projections.csv"""
import json, numpy as np, pandas as pd
from propmodel import *

f = pd.read_pickle(f'{DATA}/feat.pkl'); ff = pd.read_pickle(f'{DATA}/ff.pkl'); fr = pd.read_pickle(f'{DATA}/fights.pkl')
pm = json.load(open(f'{BASE}/props_metrics.json')); mm = json.load(open(f'{BASE}/method_metrics.json'))
win = pd.read_pickle(f'{DATA}/tonight_win.pkl')
cut = fr.date.max()
tn = f[f.tonight].copy()
# ---- method model + time mixture
P = method_probs(tn, mm['n0'], mm['alpha']); ls = late_stats(fr)
T, W, pdist = time_mixture(P, tn.fmt5.values, ls)
tmed = median_time(T, W); Etime = (W * T[None, :]).sum(axis=1)
# ---- IPF: coherent 2x3 table (winner x method) with rows = model win prob, cols = method totals
def ipf(seed, rows, cols, it=200):
    t = seed.copy()
    for _ in range(it):
        t *= (rows / t.sum(1))[:, None]; t *= (cols / t.sum(0))[None, :]
    return t
tables = []
for i, (idx, r) in enumerate(tn.iterrows()):
    pa = float(win.p_model.iloc[i]); p = P.loc[idx]
    seedA = [p.ko_A, p.sub_A, p.p_dec * pa]; seedB = [p.ko_B, p.sub_B, p.p_dec * (1 - pa)]
    tables.append(ipf(np.array([seedA, seedB]), np.array([pa, 1 - pa]), np.array([p.p_ko, p.p_sub, p.p_dec])))
# ---- NB count models refit on all data through cutoff
cnt = {}
for kind in ('sl', 'td'):
    b = pm['best'][kind]; L = long_rows(f, ff, b['lam'], b['p_min'], b['p_td']); ok = L.has_stats & (L.minutes > 0) & ~L.tonight & (L.date >= '2011-01-01')
    par = fit_nb(L[ok], kind)
    # trailing-24-month recency scale (league drift): observed / predicted under the refit model
    rec = ok & (L.date >= cut - pd.Timedelta(days=730)); y = L.loc[rec, 'sl' if kind == 'sl' else 'tl'].values
    mu = base_mu(L[rec], par) * L.loc[rec, 'minutes'].clip(lower=.05).values ** par['gamma']
    scale = float(y.sum() / mu.sum()); par['scale'] = scale
    Lt = L[L.tonight].copy(); Lt['base'] = base_mu(Lt, par) * scale
    cnt[kind] = (par, Lt)
    print(kind, 'beta', par['beta'].round(3), 'gamma', round(par['gamma'], 3), 'alpha', round(par['alpha'], 3), 'recency scale', round(scale, 3))
# ---- assemble per-fighter rows
SL_LINES = list(range(10, 151, 5)); rows = []
bio = pd.read_pickle(f'{DATA}/bio.pkl')
def mixmean(par, base, T, Wr): return base * (Wr * T[None, :] ** par['gamma']).sum(axis=1)
sl_par, sl_L = cnt['sl']; td_par, td_L = cnt['td']
for side in ('A', 'B'):
    s = sl_L[sl_L.side == side].set_index('fid').loc[tn.fid.values]; t_ = td_L[td_L.side == side].set_index('fid').loc[tn.fid.values]
    ks = np.arange(0, 301); C = mix_cdf(ks, s.base.values, sl_par, T, W)
    q = lambda p: (C >= p).argmax(axis=1)
    Ct = mix_cdf(np.arange(0, 12), t_.base.values, td_par, T, W)
    sl_mean = mixmean(sl_par, s.base.values, T, W); td_mean = mixmean(td_par, t_.base.values, T, W)
    for i, (idx, r) in enumerate(tn.iterrows()):
        me, opp = ('a_', 'b_') if side == 'A' else ('b_', 'a_')
        nm = r['name' + side]; on = r['name' + ('B' if side == 'A' else 'A')]
        tab = tables[i]; j = 0 if side == 'A' else 1
        pw = float(win.p_model.iloc[i]); pw = pw if side == 'A' else 1 - pw
        flags = [f'data_cutoff={cut.date()}']
        nf = int(r[me + 'nf']); lastd = r[me + 'last_date']
        flags.append(f'ufc_fights_in_data={nf}')
        if pd.notna(lastd): flags.append(f'last_fight={pd.Timestamp(lastd).date()} ({int(r[me + "days_since"])}d ago)')
        if nf < 5: flags.append('LOW_SAMPLE(<5 UFC fights; rates heavily shrunk to division means)')
        if not r[me + 'in_hist']: flags.append('NO_UFC_HISTORY_division_averages_used')
        if not r[me + 'in_bio']: flags.append('NOT_IN_BIO_TABLE')
        if pd.isna(r[me + 'reach']): flags.append('reach_missing_imputed')
        if pd.isna(r[me + 'age']): flags.append('dob_missing')
        if r.fmt5: flags.append('5_round_main_event(rounds4-5 survival from 2018+ history)')
        if r[me + 'nm'] < 3: flags.append('few_finish_history')
        if r['name' + side] == 'Kai Kamaka III': flags.append('matched_as_Kai Kamaka')
        row = dict(fight=f"{r.nameA} vs {r.nameB}", fighter=nm, opponent=on, division=r.divg, scheduled_rounds=5 if r.fmt5 else 3,
                   win_prob=pw, elo=float(r[me + 'elo']), elo_only_win_prob=float(r.elo_pA if side == 'A' else 1 - r.elo_pA),
                   p_distance=float(pdist[i]), p_ko_fight=float(P.p_ko.iloc[i]), p_sub_fight=float(P.p_sub.iloc[i]),
                   p_ko_for=float(tab[j, 0]), p_sub_for=float(tab[j, 1]), p_dec_win=float(tab[j, 2]),
                   fight_time_median_min=float(tmed[i]), fight_time_mean_min=float(Etime[i]),
                   sig_strikes_median=int(q(.5)[i]), sig_strikes_mean=float(sl_mean[i]), sig_strikes_p25=int(q(.25)[i]), sig_strikes_p75=int(q(.75)[i]))
        for X in SL_LINES: row[f'p_sig_over_{X}.5'] = float(1 - C[i, X])
        row.update(td_mean=float(td_mean[i]), p_td_ge1=float(1 - Ct[i, 0]), p_td_ge2=float(1 - Ct[i, 1]), data_flags='; '.join(flags))
        rows.append(row)
out = pd.DataFrame(rows)
out['_o'] = out.groupby('fight', sort=False).ngroup(); out = out.sort_values(['_o', 'fighter'], key=lambda c: c if c.name == '_o' else c.map(lambda x: 0), kind='stable').drop(columns='_o')
# keep fighter A first within each fight
out = pd.DataFrame(rows).assign(_o=lambda d: d.fight.map({k: i for i, k in enumerate(dict.fromkeys(d.fight))})).sort_values('_o', kind='stable').drop(columns='_o')
out.to_csv(f'{BASE}/projections.csv', index=False, float_format='%.4f')
pd.set_option('display.width', 250)
print(out[['fighter', 'win_prob', 'elo_only_win_prob', 'elo', 'p_distance', 'p_ko_fight', 'p_sub_fight', 'p_ko_for', 'p_sub_for', 'fight_time_median_min', 'fight_time_mean_min', 'sig_strikes_median', 'sig_strikes_mean', 'p_sig_over_40.5', 'td_mean', 'p_td_ge1', 'p_td_ge2']].round(3).to_string())
print(out[['fighter', 'data_flags']].to_string())
json.dump(dict(late_stats={k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in ls.items()}, sl_par={k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in sl_par.items()},
               td_par={k: (v.tolist() if hasattr(v, 'tolist') else v) for k, v in td_par.items()}), open(f'{BASE}/final_params.json', 'w'), indent=1)
