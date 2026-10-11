"""Point-in-time features: every feature for a fight uses only fights on strictly earlier dates.
Also appends tonight's card (date 2026-10-10) computed from the full history."""
import json, numpy as np, pandas as pd
from collections import defaultdict
from common import *

DECAYS = (1.0, 0.8, 0.6)   # per-fight geometric decay (1.0 = plain career totals)
CARD = [  # fighter A, fighter B, division, gender, rounds
    ('Brendan Allen', 'Christian Leroy Duncan', 'Middleweight', 'M', 5),
    ('Matheus Camilo', 'Jai Herbert', 'Lightweight', 'M', 3),
    ('Loopy Godinez', 'Ketlen Souza', 'Strawweight', 'F', 3),
    ('Andre Fili', 'Kai Kamaka III', 'Featherweight', 'M', 3),
    ('Malcolm Wellmaker', 'Otari Tanzilovi', 'Bantamweight', 'M', 3),
]
SUMCOLS = ['min', 'sl', 'sa', 'tl', 'ta', 'otl', 'ota', 'sub']

def build(K=None, boost=None):
    p = json.load(open(f'{BASE}/elo_params.json')); K = K or p['K']; boost = boost or p['boost']
    fr = pd.read_pickle(f'{DATA}/fights.pkl').sort_values(['date', 'fid']).reset_index(drop=True)
    ff = pd.read_pickle(f'{DATA}/ff.pkl'); bio = pd.read_pickle(f'{DATA}/bio.pkl')
    # add tonight's card
    tonight = []
    for i, (a, b, div, g, rds) in enumerate(CARD):
        tonight.append(dict(fid=10 ** 6 + i, date=CARD_DATE, kA=norm(a), kB=norm(b), nameA=a, nameB=b, div=div, gender=g,
                            divg=f'{g}_{div}', result=np.nan, method='NA', ROUND=np.nan, minutes=np.nan,
                            sched_min=15. * rds / 3 if rds == 3 else 25., fmt3=rds == 3, fmt5=rds == 5, tonight=True))
    fr['tonight'] = False
    fr = pd.concat([fr, pd.DataFrame(tonight)], ignore_index=True)
    fr['tonight'] = fr.tonight.fillna(False).astype(bool)
    ffd = {}
    for r in ff.itertuples(index=False):
        ffd[(r.fid, r.side)] = r

    hist = defaultdict(list)            # fighter -> list of per-fight dicts (chronological)
    R, N = {}, {}
    div = defaultdict(lambda: defaultdict(float))   # divg -> sums over fighter-fight rows
    glob = defaultdict(float)
    meth = defaultdict(lambda: defaultdict(float))  # divg -> method counts (3-round-equivalent)
    methg = defaultdict(float)
    out = []

    def wsums(h, lam):
        s = dict.fromkeys(SUMCOLS, 0.0); w = 1.0
        for rec in reversed(h):
            if rec['has_stats']:
                s['min'] += w * rec['minutes']
                for c in ('sl', 'sa', 'tl', 'ta', 'otl', 'ota', 'sub'): s[c] += w * rec[c]
            w *= lam
        return s
    def fcount(h):
        d = dict(nm=0, ko_for=0, sub_for=0, ko_ag=0, sub_ag=0)
        for rec in h:
            if rec['m_valid']:
                d['nm'] += 1; d['ko_for'] += rec['ko_for']; d['sub_for'] += rec['sub_for']; d['ko_ag'] += rec['ko_ag']; d['sub_ag'] += rec['sub_ag']
        return d
    def fighter_feats(k, date, side, divg):
        h = hist.get(k, [])
        f = {'elo': R.get(k, 1500.), 'nf': len(h)}
        b = bio.loc[k] if k in bio.index else None
        f['age'] = (date - b.dob).days / 365.25 if b is not None and pd.notna(b.dob) else np.nan
        f['height'] = b.height if b is not None else np.nan; f['reach'] = b.reach if b is not None else np.nan
        f['in_bio'] = b is not None; f['in_hist'] = len(h) > 0
        f['days_since'] = (date - h[-1]['date']).days if h else np.nan
        last3 = h[-3:]
        f['l3_n'] = len(last3)
        f['l3_win'] = np.nan if not last3 else np.mean([r['win'] if r['win'] == r['win'] else .5 for r in last3])
        ls = [r for r in last3 if r['has_stats']]
        f['l3_diff_pm'] = np.nan if not ls else sum(r['sl'] - r['sa'] for r in ls) / max(sum(r['minutes'] for r in ls), 1e-9)
        f['last_date'] = h[-1]['date'] if h else pd.NaT
        f['wins_streak_loss_last'] = np.nan if not h else (1.0 if h[-1]['win'] == 0 else 0.0)
        for lam in DECAYS:
            s = wsums(h, lam)
            for c in SUMCOLS: f[f's{lam}_{c}'] = s[c]
        f.update(fcount(h))
        return f

    for date, g in fr.groupby('date', sort=True):
        # ---- features for every fight on this date (history strictly before)
        dstats = {}
        for dv in g.divg.unique():
            d = div[dv]; dstats[dv] = dict(d)
        for r in g.itertuples():
            fa = fighter_feats(r.kA, date, 'A', r.divg); fb = fighter_feats(r.kB, date, 'B', r.divg)
            row = {'fid': r.fid, 'date': date, 'kA': r.kA, 'kB': r.kB, 'nameA': r.nameA, 'nameB': r.nameB, 'divg': r.divg, 'div': r.div,
                   'gender': r.gender, 'result': r.result, 'method': r.method, 'ROUND': r.ROUND, 'minutes': r.minutes,
                   'sched_min': r.sched_min, 'fmt3': bool(r.fmt3), 'fmt5': bool(r.fmt5), 'tonight': bool(r.tonight)}
            for k, v in fa.items(): row['a_' + k] = v
            for k, v in fb.items(): row['b_' + k] = v
            d = dstats[r.divg]
            for c in ('min', 'sl', 'sa', 'tl', 'ta', 'n'): row['dv_' + c] = d.get(c, 0.0)
            for c in ('min', 'sl', 'sa', 'tl', 'ta', 'n'): row['gl_' + c] = glob[c]
            m = meth[r.divg]
            for c in ('n', 'ko', 'sub'): row['dm_' + c] = m.get(c, 0.0); row['gm_' + c] = methg[c]
            out.append(row)
        # ---- updates after the whole card
        for r in g.itertuples():
            if r.tonight: continue
            ra, rb = R.get(r.kA, 1500.), R.get(r.kB, 1500.)
            if r.result == r.result:
                e = 1 / (1 + 10 ** ((rb - ra) / 400))
                ka = K * (boost if N.get(r.kA, 0) < 3 else 1); kb = K * (boost if N.get(r.kB, 0) < 3 else 1)
                R[r.kA] = ra + ka * (r.result - e); R[r.kB] = rb - kb * (r.result - e)
                N[r.kA] = N.get(r.kA, 0) + 1; N[r.kB] = N.get(r.kB, 0) + 1
            valid_m = (r.fmt3 or r.fmt5) and r.method in ('DEC', 'KO', 'SUB')
            fin3 = valid_m and r.method != 'DEC' and (r.fmt3 or r.ROUND <= 3)
            for side, k in (('A', r.kA), ('B', r.kB)):
                x = ffd[(r.fid, side)]; o = ffd[(r.fid, 'B' if side == 'A' else 'A')]
                hs = bool(x.has_stats)
                rec = dict(date=date, has_stats=hs, minutes=x.minutes if hs else 0.0, win=x.win,
                           sl=x.sl if hs else 0., sa=x.o_sl if hs else 0., tl=x.tl if hs else 0., ta=x.ta if hs else 0.,
                           otl=x.o_tl if hs else 0., ota=x.o_ta if hs else 0., sub=x.sub if hs else 0.,
                           m_valid=bool(valid_m), ko_for=int(fin3 and r.method == 'KO' and x.win == 1), sub_for=int(fin3 and r.method == 'SUB' and x.win == 1),
                           ko_ag=int(fin3 and r.method == 'KO' and x.win == 0), sub_ag=int(fin3 and r.method == 'SUB' and x.win == 0))
                hist[k].append(rec)
                if hs:
                    d = div[r.divg]
                    d['min'] += x.minutes; d['sl'] += x.sl; d['sa'] += x.o_sl; d['tl'] += x.tl; d['ta'] += x.ta; d['n'] += 1
                    glob['min'] += x.minutes; glob['sl'] += x.sl; glob['sa'] += x.o_sl; glob['tl'] += x.tl; glob['ta'] += x.ta; glob['n'] += 1
            if valid_m:
                m = meth[r.divg]; m['n'] += 1; methg['n'] += 1
                if fin3 and r.method == 'KO': m['ko'] += 1; methg['ko'] += 1
                if fin3 and r.method == 'SUB': m['sub'] += 1; methg['sub'] += 1
    feat = pd.DataFrame(out).sort_values(['date', 'fid']).reset_index(drop=True)
    feat['elo_pA'] = 1 / (1 + 10 ** ((feat.b_elo - feat.a_elo) / 400))
    return feat, R, N

if __name__ == '__main__':
    feat, R, N = build()
    feat.to_pickle(f'{DATA}/feat.pkl')
    print(feat.shape, feat.date.max())
    print(feat[feat.tonight][['nameA', 'nameB', 'a_elo', 'b_elo', 'a_nf', 'b_nf', 'a_age', 'b_age', 'a_reach', 'b_reach', 'a_days_since', 'b_days_since', 'a_in_hist', 'b_in_hist']].to_string())
