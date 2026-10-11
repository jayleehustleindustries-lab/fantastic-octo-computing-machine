import os, re, unicodedata, numpy as np, pandas as pd
BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, 'data')
TRAIN_END = pd.Timestamp('2023-01-01')
CARD_DATE = pd.Timestamp('2026-10-10')

SUFFIX = {'jr', 'sr', 'ii', 'iii', 'iv', 'v'}
ALIASES = {'lupita godinez': 'loopy godinez'}
def norm(name):
    s = unicodedata.normalize('NFKD', str(name)).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r"[.'`\-]", ' ', s)
    s = re.sub(r'[^a-z ]', ' ', s)
    toks = [t for t in s.split() if t]
    while toks and toks[-1] in SUFFIX: toks.pop()
    s = ' '.join(toks)
    return ALIASES.get(s, s)

def ll(y, p):
    p = np.clip(p, 1e-6, 1 - 1e-6); y = np.asarray(y)
    return float(-(y * np.log(p) + (1 - y) * np.log(1 - p)).mean())
def brier(y, p): return float(((np.asarray(p) - np.asarray(y)) ** 2).mean())
def acc(y, p): return float(((np.asarray(p) > .5) == np.asarray(y)).mean())
def calib(y, p, bins=5):
    d = pd.DataFrame({'y': y, 'p': p})
    d['bin'] = pd.qcut(d.p, bins, duplicates='drop')
    g = d.groupby('bin', observed=True).agg(n=('y', 'size'), mean_pred=('p', 'mean'), observed=('y', 'mean'))
    return g.reset_index(drop=True)

def shr(num, den, prior_den, prior_rate):
    return (num + prior_den * prior_rate) / (den + prior_den)

def div_means(f, k0=300.):
    """Point-in-time division means (shrunk toward global), per fight row."""
    gm_sl = np.where(f.gl_min > 0, f.gl_sl / f.gl_min.clip(lower=1e-9), 3.5)
    gm_td = np.where(f.gl_min > 0, f.gl_tl / f.gl_min.clip(lower=1e-9), 0.05)
    gm_tdatt = np.where(f.gl_ta > 0, f.gl_tl / f.gl_ta.clip(lower=1e-9), .4)
    m = pd.DataFrame(index=f.index)
    m['sl'] = shr(f.dv_sl, f.dv_min, k0, gm_sl)
    m['td'] = shr(f.dv_tl, f.dv_min, k0, gm_td)           # TD landed per minute
    m['tdacc'] = shr(f.dv_tl, f.dv_ta, 40., gm_tdatt)    # TD accuracy = 1 - opponent TD defense
    return m

def fighter_rates(f, side, lam, dm, p_min=30., p_td=60., p_att=12.):
    """Shrunk rolling rates for one side ('a'/'b'), decay lam."""
    g = lambda c: f[f'{side}_s{lam}_{c}']
    r = pd.DataFrame(index=f.index)
    r['sl_pm'] = shr(g('sl'), g('min'), p_min, dm['sl'])
    r['sa_pm'] = shr(g('sa'), g('min'), p_min, dm['sl'])
    r['td_pm'] = shr(g('tl'), g('min'), p_td, dm['td'])               # TDs landed / min
    r['tdabs_pm'] = shr(g('otl'), g('min'), p_td, dm['td'])           # TDs absorbed / min
    r['tdd'] = 1 - shr(g('otl'), g('ota'), p_att, dm['tdacc'])        # TD defense (shrunk)
    r['sub_pm'] = shr(g('sub'), g('min'), p_td, 0.01)
    r['min'] = g('min')
    return r
