"""Build fight-level and fighter-fight-level tables from the raw CSVs."""
import pandas as pd, numpy as np, re
from common import *

ev = pd.read_csv(f'{DATA}/ufc_event_details.csv'); ev['EV'] = ev.EVENT.str.strip(); ev['date'] = pd.to_datetime(ev.DATE)
fr = pd.read_csv(f'{DATA}/ufc_fight_results.csv'); fr['EV'] = fr.EVENT.str.strip()
fr['row_order'] = np.arange(len(fr))  # file order is newest-first
fr = fr.merge(ev[['EV', 'date']].drop_duplicates('EV'), on='EV', how='left')
fr = fr.sort_values('row_order').reset_index(drop=True)
nmiss = int(fr.date.isna().sum())
# Events absent from event_details: impute date as midpoint of neighbouring known events in file order (flagged)
fr['date_imputed'] = fr.date.isna()
d_prev = fr.date.ffill(); d_next = fr.date.bfill()   # newer neighbour above, older neighbour below
fr['date'] = fr.date.fillna(d_next + (d_prev - d_next) / 2).dt.normalize()
print('fights with imputed date:', nmiss, fr[fr.date_imputed][['EV', 'date']].drop_duplicates().to_string())
fr = fr.dropna(subset=['date']).copy()
fr['bout'] = fr.BOUT.str.strip()
sp = fr.bout.str.split(' vs. ', n=1, expand=True)
fr['nameA'], fr['nameB'] = sp[0].str.strip(), sp[1].str.strip()
fr['kA'], fr['kB'] = fr.nameA.map(norm), fr.nameB.map(norm)

def wc(s):
    s = str(s); gender = 'F' if "Women" in s else 'M'
    t = re.sub(r"UFC |Interim |Title Bout|Bout|Women's |Superfight Championship", '', s).strip()
    if t in ('Open Weight', 'Catch Weight', '') or 'Tournament' in t: t = 'Other'
    return t, gender
fr[['div', 'gender']] = fr.WEIGHTCLASS.apply(lambda s: pd.Series(wc(s)))
fr['divg'] = fr.gender + '_' + fr['div']
def parse_fmt(f):
    m = re.search(r'\(([\d\-]+)\)', str(f)); 
    return [int(x) for x in m.group(1).split('-')] if m else [5]
def fight_minutes(r):
    lens = parse_fmt(r['TIME FORMAT']); rd = int(r.ROUND) if pd.notna(r.ROUND) else 1
    try: mm, ss = str(r.TIME).split(':'); t = int(mm) + int(ss) / 60
    except Exception: t = np.nan
    pre = sum(lens[:rd - 1]) if rd - 1 <= len(lens) else 5 * (rd - 1)
    return pre + t
fr['minutes'] = fr.apply(fight_minutes, axis=1)
fr['sched_rounds'] = fr['TIME FORMAT'].map(lambda f: len(parse_fmt(f)) if 'Rnd' in str(f) else np.nan)
fr['fmt3'] = fr['TIME FORMAT'].isin(['3 Rnd (5-5-5)']); fr['fmt5'] = fr['TIME FORMAT'].isin(['5 Rnd (5-5-5-5-5)'])
fr['sched_min'] = np.where(fr.fmt5, 25., np.where(fr.fmt3, 15., np.nan))
m = fr.METHOD.str.strip()
fr['method'] = np.select([m.str.startswith('Decision'), m.eq('KO/TKO') | m.str.contains('Doctor'), m.eq('Submission')], ['DEC', 'KO', 'SUB'], 'OTHER')
fr['result'] = fr.OUTCOME.map({'W/L': 1.0, 'L/W': 0.0, 'D/D': 0.5, 'NC/NC': np.nan})
fr['ROUND'] = pd.to_numeric(fr.ROUND, errors='coerce')
fr = fr.sort_values(['date', 'URL']).reset_index(drop=True)
fr['fid'] = np.arange(len(fr))

# ---------------- per-fighter-fight stats (sum over rounds)
fs = pd.read_csv(f'{DATA}/ufc_fight_stats.csv').dropna(subset=['ROUND'])
fs['EV'] = fs.EVENT.str.strip(); fs['bout'] = fs.BOUT.str.strip(); fs['k'] = fs.FIGHTER.map(norm)
def of(s):
    a = s.str.extract(r'(\d+) of (\d+)').astype(float); return a[0], a[1]
fs['sl'], fs['sa'] = of(fs['SIG.STR.']); fs['tl'], fs['ta'] = of(fs['TD'])
fs['sub'] = pd.to_numeric(fs['SUB.ATT'], errors='coerce'); fs['kd'] = pd.to_numeric(fs['KD'], errors='coerce')
def sec(x):
    try: a, b = str(x).split(':'); return int(a) * 60 + int(b)
    except Exception: return np.nan
fs['ctrl'] = fs.CTRL.map(sec)
agg = fs.groupby(['EV', 'bout', 'k'], as_index=False)[['sl', 'sa', 'tl', 'ta', 'sub', 'kd', 'ctrl']].sum(min_count=1)
rows = []
for side, o in (('A', 'B'), ('B', 'A')):
    t = fr[['fid', 'EV', 'bout', 'date', 'div', 'gender', 'divg', 'minutes', 'sched_min', 'fmt3', 'fmt5', 'method', 'ROUND', 'result']].copy()
    t['k'] = fr['k' + side]; t['ok'] = fr['k' + o]; t['name'] = fr['name' + side]; t['side'] = side
    t['win'] = t.result if side == 'A' else 1 - t.result
    rows.append(t)
ff = pd.concat(rows, ignore_index=True)
ff = ff.merge(agg, on=['EV', 'bout', 'k'], how='left')
# opponent's stats in same fight
opp = ff[['fid', 'k', 'sl', 'tl', 'ta', 'sub']].rename(columns={'k': 'ok', 'sl': 'o_sl', 'tl': 'o_tl', 'ta': 'o_ta', 'sub': 'o_sub'})
ff = ff.merge(opp, on=['fid', 'ok'], how='left')
ff['has_stats'] = ff.sl.notna() & ff.o_sl.notna() & ff.minutes.gt(0)
ff = ff.sort_values(['date', 'fid', 'side']).reset_index(drop=True)
print('fighter-fights', len(ff), 'with stats', ff.has_stats.mean().round(3))

# ---------------- fighter bio
tt = pd.read_csv(f'{DATA}/ufc_fighter_tott.csv'); tt['k'] = tt.FIGHTER.map(norm)
def inch(h):
    m = re.match(r"(\d+)' (\d+)", str(h)); return int(m.group(1)) * 12 + int(m.group(2)) if m else np.nan
tt['height'] = tt.HEIGHT.map(inch); tt['reach'] = pd.to_numeric(tt.REACH.astype(str).str.replace('"', ''), errors='coerce')
tt['dob'] = pd.to_datetime(tt.DOB, format='%b %d, %Y', errors='coerce')
dups = tt[tt.k.duplicated(keep=False)].sort_values('k')
print('duplicate normalized names in bios:', dups.k.nunique())
bio = tt.drop_duplicates('k', keep='last').set_index('k')[['FIGHTER', 'height', 'reach', 'dob', 'STANCE']]
fr.to_pickle(f'{DATA}/fights.pkl'); ff.to_pickle(f'{DATA}/ff.pkl'); bio.to_pickle(f'{DATA}/bio.pkl')
print(fr.date.max(), len(fr)); print(fr.method.value_counts())
print(fr.groupby(fr.date.dt.year).size().tail(3))
