"""Shared data + model code for NFL player-prop projections (nflverse data).
Model: per-player recency-weighted mean (shrunk to role prior) x log-linear (Poisson-GLM) adjustments for
opponent defense + game script (implied total, spread) -> Negative-Binomial distribution.
All features are causal (use only games before the target game).
"""
import numpy as np, pandas as pd
from scipy.stats import nbinom
from scipy.special import gammaln
from scipy.optimize import minimize

BASE = '/tmp/claude-0/-home-user-fantastic-octo-computing-machine/fd837da0-fc17-5f70-a6ad-c31478ee2717/scratchpad/nfl/props'
D = BASE + '/data'

STATS = {
    'pass_yds':  dict(col='passing_yards',  role='QB',   opp='opp_pass_yds'),
    'pass_tds':  dict(col='passing_tds',    role='QB',   opp='opp_pass_tds'),
    'rush_yds':  dict(col='rushing_yards',  role='RB',   opp='opp_rush_yds'),
    'rec_yds':   dict(col='receiving_yards', role='WRTE', opp='opp_rec_yds'),
    'receptions': dict(col='receptions',    role='WRTE', opp='opp_rec'),
}
SDECAY = 0.9   # carry-over of history across a season boundary


# ----------------------------------------------------------------------------- data
def load_games():
    g = pd.read_csv(D + '/games.csv')
    g = g[(g.game_type == 'REG') & (g.season >= 2022)].copy()
    g['total_line'] = g.total_line.fillna(g.total_line.median())
    g['spread_line'] = g.spread_line.fillna(0.0)
    rows = []
    for side in ['home', 'away']:
        opp = 'away' if side == 'home' else 'home'
        t = pd.DataFrame({
            'season': g.season, 'week': g.week, 'game_id': g.game_id,
            'team': g[side + '_team'], 'opp': g[opp + '_team'],
            'is_home': int(side == 'home'),
            'spread_team': g.spread_line if side == 'home' else -g.spread_line,  # team expected margin
            'total': g.total_line, 'gameday': g.gameday, 'gametime': g.gametime,
            'qb_name': g[side + '_qb_name']})
        t['imp'] = (t.total + t.spread_team) / 2.0
        rows.append(t)
    return pd.concat(rows, ignore_index=True)


def load_players():
    fr = [pd.read_csv(f'{D}/sp_{y}.csv', low_memory=False) for y in range(2022, 2027)]
    pg = pd.concat(fr, ignore_index=True)
    pg = pg[(pg.season_type == 'REG') & pg.position.isin(['QB', 'RB', 'FB', 'WR', 'TE'])]
    cols = ['player_id', 'player_display_name', 'position', 'season', 'week', 'team', 'opponent_team',
            'attempts', 'passing_yards', 'passing_tds', 'carries', 'rushing_yards', 'targets',
            'receptions', 'receiving_yards']
    pg = pg[cols].rename(columns={'player_display_name': 'name'}).copy()
    pg['pos'] = pg.position.replace({'FB': 'RB'})
    return pg


def ew_state(y, seasons, hl, sdecay=SDECAY):
    """Exponentially-weighted (by games ago) numerator/denominator BEFORE each game."""
    lam = 0.5 ** (1.0 / hl)
    n = len(y)
    num_pre = np.zeros(n); den_pre = np.zeros(n)
    num = 0.0; den = 0.0
    for i in range(n):
        if i > 0 and seasons[i] != seasons[i - 1]:
            num *= sdecay; den *= sdecay
        num_pre[i] = num; den_pre[i] = den
        if not np.isnan(y[i]):
            num = num * lam + y[i]; den = den * lam + 1.0
    return num_pre, den_pre


def ew_all(pg, col, hl):
    """pg must be sorted by player_id, season, week with RangeIndex."""
    yv = pg[col].values.astype(float); sv = pg.season.values
    num = np.zeros(len(pg)); den = np.zeros(len(pg))
    for _, idx in pg.groupby('player_id').indices.items():
        a, b = ew_state(yv[idx], sv[idx], hl)
        num[idx] = a; den[idx] = b
    return num, den


def def_factors(games, pg, hl=6, k=6.0, sdecay=SDECAY):
    """Opponent-defense factors: shrunk EW mean of stat allowed per game / league mean. Keyed (season,week,def_team)."""
    p = pg.copy()
    p['rush_rb'] = np.where(p.pos == 'RB', p.rushing_yards, 0)
    p['rec_wt'] = np.where(p.pos.isin(['WR', 'TE']), p.receiving_yards, 0)
    p['recp_wt'] = np.where(p.pos.isin(['WR', 'TE']), p.receptions, 0)
    a = p.groupby(['season', 'week', 'opponent_team']).agg(
        opp_pass_yds=('passing_yards', 'sum'), opp_pass_tds=('passing_tds', 'sum'),
        opp_rush_yds=('rush_rb', 'sum'), opp_rec_yds=('rec_wt', 'sum'), opp_rec=('recp_wt', 'sum')
    ).reset_index().rename(columns={'opponent_team': 'team'})
    s = games[['season', 'week', 'team']].merge(a, on=['season', 'week', 'team'], how='left')
    s = s.sort_values(['team', 'season', 'week']).reset_index(drop=True)
    out = s[['season', 'week', 'team']].copy()
    for c in ['opp_pass_yds', 'opp_pass_tds', 'opp_rush_yds', 'opp_rec_yds', 'opp_rec']:
        lg = a[c].mean()
        f = np.ones(len(s))
        for _, idx in s.groupby('team').indices.items():
            num, den = ew_state(s[c].values[idx].astype(float), s.season.values[idx], hl, sdecay)
            f[idx] = ((num + k * lg) / (den + k)) / lg
        out['f_' + c] = np.log(f)
    return out.rename(columns={'team': 'opp'})   # keyed by the defending team (= offense's opponent)


def build(pg=None, games=None, extra_rows=None):
    """Return player-game table with context + usage features. extra_rows: pseudo-rows for upcoming games
    (columns: player_id,name,pos,season,week,team,opponent_team) with NaN stats."""
    if pg is None: pg = load_players()
    if games is None: games = load_games()
    if extra_rows is not None:
        pg = pd.concat([pg, extra_rows], ignore_index=True)
    pg = pg.sort_values(['player_id', 'season', 'week']).reset_index(drop=True)
    ctx = games[['season', 'week', 'team', 'opp', 'is_home', 'spread_team', 'total', 'imp', 'game_id']]
    pg = pg.merge(ctx, left_on=['season', 'week', 'team'], right_on=['season', 'week', 'team'], how='left')
    pg = pg.sort_values(['player_id', 'season', 'week']).reset_index(drop=True)
    df = def_factors(games, pg[pg.carries.notna() | pg.attempts.notna() | pg.targets.notna()])
    pg = pg.merge(df, on=['season', 'week', 'opp'], how='left')
    pg = pg.sort_values(['player_id', 'season', 'week']).reset_index(drop=True)
    # usage (pre-game) for role selection
    for nm, col, hl in [('att', 'attempts', 3), ('car', 'carries', 3), ('tgt', 'targets', 4)]:
        n, d = ew_all(pg, col, hl)
        pg['u_' + nm] = np.where(d > 0, n / np.maximum(d, 1e-9), np.nan)
        pg['uw_' + nm] = d
    return pg


def assign_roles(pg):
    """Pre-game role assignment among players present in the game table for that team-week."""
    pg = pg.copy()
    pg['role'] = ''
    pg['rrank'] = 0
    q = pg[(pg.pos == 'QB') & (pg.u_att >= 15)]
    i = q.groupby(['season', 'week', 'team']).u_att.idxmax()
    pg.loc[i.values, 'role'] = 'QB'; pg.loc[i.values, 'rrank'] = 1
    r = pg[(pg.pos == 'RB') & (pg.u_car >= 6)]
    i = r.groupby(['season', 'week', 'team']).u_car.idxmax()
    pg.loc[i.values, 'role'] = 'RB'; pg.loc[i.values, 'rrank'] = 1
    w = pg[pg.pos.isin(['WR', 'TE']) & (pg.u_tgt >= 3.0)].copy()
    w['rk'] = w.groupby(['season', 'week', 'team']).u_tgt.rank(ascending=False, method='first')
    w = w[w.rk <= 2]
    pg.loc[w.index, 'role'] = 'WRTE'; pg.loc[w.index, 'rrank'] = w.rk.astype(int)
    return pg


# ----------------------------------------------------------------------------- model
def nb_params(mu, alpha):
    r = 1.0 / alpha
    return r, r / (r + mu)


def p_over(mu, alpha, L):
    """P(Y > L) for half-point/whole-number line L under NB(mean mu, var mu+alpha mu^2). Whole-number L -> P(Y>L) (push excluded)."""
    r, p = nb_params(mu, alpha)
    return 1.0 - nbinom.cdf(np.floor(L), r, p)


def p_push(mu, alpha, L):
    r, p = nb_params(mu, alpha)
    isint = (np.floor(L) == L)
    return np.where(isint, nbinom.pmf(L, r, p), 0.0)


def median_nb(mu, alpha):
    r, p = nb_params(mu, alpha)
    return nbinom.ppf(0.5, r, p)


def nb_ll(y, mu, alpha):
    r = 1.0 / alpha
    return (gammaln(y + r) - gammaln(r) - gammaln(y + 1) + r * np.log(r / (r + mu)) + y * np.log(mu / (r + mu)))


class StatModel:
    def __init__(self, stat):
        self.stat = stat; self.cfg = STATS[stat]

    # --- stage 1: player mean
    def player_mu(self, d, hl, k, prior):
        num, den = ew_all(d, self.cfg['col'], hl)  # d is full table sorted/indexed
        return num, den

    def fit(self, pg_all, train_mask, grid_hl=(3, 5, 8, 12, 20), grid_k=(0.5, 1.5, 3, 6, 10)):
        col = self.cfg['col']; role = self.cfg['role']
        roles = pg_all.role == role
        tr = train_mask & roles & pg_all[col].notna()
        # role prior by rank
        self.prior = {int(rk): float(pg_all.loc[tr & (pg_all.rrank == rk), col].mean())
                      for rk in sorted(pg_all.loc[tr, 'rrank'].unique())}
        best = None
        cache = {}
        for hl in grid_hl:
            num, den = ew_all(pg_all, col, hl)
            cache[hl] = (num, den)
            pri = pg_all.rrank.map(self.prior).fillna(np.mean(list(self.prior.values()))).values
            for k in grid_k:
                mu = (num + k * pri) / (den + k)
                err = np.mean((pg_all.loc[tr, col].values - mu[tr.values]) ** 2)
                if best is None or err < best[0]:
                    best = (err, hl, k)
        _, self.hl, self.k = best
        # GLM
        X, off = self._design(pg_all, cache[self.hl])
        y = pg_all[col].values.astype(float)
        y = np.where(np.isnan(y), np.nan, np.maximum(y, 0.0))   # negative yardage -> 0 for count likelihood
        m = tr.values
        Xm, om, ym = X[m], off[m], y[m]

        def nll(b):
            eta = om + Xm @ b
            return np.sum(np.exp(eta) - ym * eta) + 0.5 * 2.0 * np.sum(b[1:] ** 2)
        b0 = np.zeros(X.shape[1])
        self.beta = minimize(nll, b0, method='BFGS').x
        mu = np.exp(off + X @ self.beta)
        # dispersion  log alpha = a0 + a1 log(mu/mbar)
        self.mbar = float(np.mean(mu[m]))
        lm = np.log(mu[m] / self.mbar)

        # dispersion by method of moments (robust): alpha = sum((y-mu)^2 - mu)/sum(mu^2), single alpha
        alpha0 = max(1e-3, float(np.sum((ym - mu[m]) ** 2 - mu[m]) / np.sum(mu[m] ** 2)))
        self.a = np.array([np.log(alpha0), 0.0])
        self.params = dict(hl=self.hl, k=self.k, prior=self.prior, beta=self.beta.tolist(),
                           a=self.a.tolist(), mbar=self.mbar, n_train=int(m.sum()))
        return self

    def _design(self, d, state):
        num, den = state
        pri = d.rrank.map(self.prior).fillna(np.mean(list(self.prior.values()))).values
        mu0 = (num + self.k * pri) / (den + self.k)
        mu0 = np.maximum(mu0, 0.05)
        X = np.column_stack([np.ones(len(d)),
                             d['f_' + self.cfg['opp']].fillna(0).values,
                             np.log(d.imp.fillna(22.5).values / 22.5),
                             d.spread_team.fillna(0).values / 7.0])
        return X, np.log(mu0)

    def predict(self, d):
        state = ew_all(d, self.cfg['col'], self.hl)
        X, off = self._design(d, state)
        mu = np.exp(off + X @ self.beta)
        mu0 = np.exp(off)
        alpha = np.clip(np.exp(self.a[0] + self.a[1] * np.log(mu / self.mbar)), 1e-3, 5)
        return mu, mu0, alpha, state[1]
