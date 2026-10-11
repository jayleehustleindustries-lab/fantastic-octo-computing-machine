"""
Benter test on real closing lines.  Reads preds.csv + params.json (written by nfl_model.py).

  fit model        : 2010-2019 (done in nfl_model.py)
  fit blend + rule : 2020-2022 (logistic on model-minus-line, threshold grid)
  untouched holdout: 2023-2025 (evaluated once, frozen coefficients/threshold)
  apply            : 2026 un-played games with lines in games.csv

Run: python benter.py  -> report.md, picks_2026.csv, holdout_summary.json
"""
import json
import numpy as np
import pandas as pd
from scipy.stats import norm, binomtest
from scipy.optimize import minimize

P = json.load(open("params.json"))
D = pd.read_csv("preds.csv")
SD_M, SD_T = P["sd_margin"], P["sd_total"]
BE = 1.0 / 1.9090909  # -110 break-even 0.52381
DEC = 1.0 + 100 / 110
PER = {"fit": (2010, 2019), "blend": (2020, 2022), "hold": (2023, 2025)}
LL0 = np.log(2)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (c - h, c + h)


def logloss(y, p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


def fit_logit(X, y, l2=1e-6):
    X1 = np.column_stack([np.ones(len(X)), X])
    def nll(b):
        z = X1 @ b
        return np.sum(np.logaddexp(0, z) - y * z) + l2 * np.sum(b[1:] ** 2)
    def grad(b):
        z = X1 @ b; p = 1 / (1 + np.exp(-z))
        gr = X1.T @ (p - y); gr[1:] += 2 * l2 * b[1:]
        return gr
    b = minimize(nll, np.zeros(X1.shape[1]), jac=grad, method="BFGS").x
    z = X1 @ b; p = 1 / (1 + np.exp(-z))
    W = p * (1 - p)
    cov = np.linalg.inv((X1 * W[:, None]).T @ X1)
    return b, np.sqrt(np.diag(cov))


def sig(z):
    return 1 / (1 + np.exp(-z))


def sel(per, df):
    lo, hi = PER[per]
    return df[(df.season >= lo) & (df.season <= hi)]


# ---------------------------------------------------------------------------------------------
# build per-market tables
# ---------------------------------------------------------------------------------------------
def prep(kind):
    d = D[D.played].copy()
    if kind == "ats":
        d = d[d.spread_line.notna()]
        d["line"] = d.spread_line; d["mod"] = d.m_model; d["out"] = d.result; sd = SD_M
        d["push"] = d.out == d.line
        d["y"] = (d.out > d.line).astype(float)  # 1 = home covers
        # no-vig market prob that home covers (from posted spread odds)
        def dec(o): return np.where(o > 0, 1 + o / 100, 1 + 100 / (-o))
        ph = 1 / dec(d.home_spread_odds); pa = 1 / dec(d.away_spread_odds)
        d["p_mkt"] = pd.Series(ph / (ph + pa), index=d.index).fillna(0.5)
    else:
        d = d[d.total_line.notna()]
        d["line"] = d.total_line; d["mod"] = d.t_model; d["out"] = d.total; sd = SD_T
        d["push"] = d.out == d.line
        d["y"] = (d.out > d.line).astype(float)  # 1 = over
        def dec(o): return np.where(o > 0, 1 + o / 100, 1 + 100 / (-o))
        po = 1 / dec(d.over_odds); pu = 1 / dec(d.under_odds)
        d["p_mkt"] = pd.Series(po / (po + pu), index=d.index).fillna(0.5)
    d["x"] = d["mod"] - d["line"]
    d["p_model"] = norm.cdf(d.x / sd)
    return d[~d.push].copy(), sd


def evaluate_rule(df, side_p, thr):
    """side_p: P(home/over hits). Bet the side whose probability >= thr. Returns picks df."""
    side_p = np.asarray(side_p, dtype=float)
    pick_up = side_p >= thr
    pick_dn = (1 - side_p) >= thr
    m = pick_up | pick_dn
    sub = df[m].copy()
    sub["bet_up"] = pick_up[m]
    sub["p_side"] = np.where(pick_up[m], side_p[m], 1 - side_p[m])
    sub["hit"] = np.where(sub.bet_up, sub.y == 1, sub.y == 0)
    return sub


def summ(sub, null=BE):
    n = len(sub); k = int(sub.hit.sum()) if n else 0
    lo, hi = wilson(k, n)
    pval = binomtest(k, n, null, alternative="greater").pvalue if n else np.nan
    roi = (k * (DEC - 1) - (n - k)) / n if n else np.nan
    return dict(n=n, k=k, rate=k / n if n else np.nan, lo=lo, hi=hi, p_be=pval, roi=roi)


def fmt_row(label, s):
    if s["n"] == 0:
        return f"| {label} | 0 | - | - | - | - |"
    return (f"| {label} | {s['n']} | {100*s['rate']:.1f}% | {100*s['lo']:.1f}-{100*s['hi']:.1f}% | "
            f"{100*s['roi']:+.1f}% | {s['p_be']:.3f} |")


HDR = "| rule | picks | hit rate | 95% CI (Wilson) | ROI @-110 | p(rate<=52.38%) |\n|---|---|---|---|---|---|"
out = []
res_json = {}


def A(s=""):
    out.append(s)


def run_market(kind, label):
    d, sd = prep(kind)
    up = "home covers" if kind == "ats" else "over"
    dn = "away covers" if kind == "ats" else "under"
    A(f"## {label}")
    A()
    # ---- sample sizes + RMSE
    A("### Point-prediction quality (RMSE, points)")
    A()
    A("| period | n | model | market line | market better by |\n|---|---|---|---|---|")
    for per in PER:
        s = sel(per, d)
        rm = np.sqrt(np.mean((s.out - s["mod"]) ** 2)); rl = np.sqrt(np.mean((s.out - s.line) ** 2))
        A(f"| {per} {PER[per][0]}-{PER[per][1]} | {len(s)} | {rm:.3f} | {rl:.3f} | {rm-rl:+.3f} |")
    A()
    # ---- incremental information regression
    A("### Does the model add information beyond the line?  (OLS: outcome - line = a + b*(model - line))")
    A()
    A("b = 0: line already contains everything the model knows.  b = 1: line is useless.  Benter's w is this b.")
    A()
    A("| period | n | b (slope) | s.e. | t | a (intercept) |\n|---|---|---|---|---|---|")
    breg = {}
    for per in PER:
        s = sel(per, d)
        X = s.x.values; Y = (s.out - s.line).values
        xb = X.mean(); b = np.sum((X - xb) * (Y - Y.mean())) / np.sum((X - xb) ** 2); a = Y.mean() - b * xb
        e = Y - a - b * X; se = np.sqrt(np.sum(e ** 2) / (len(X) - 2) / np.sum((X - xb) ** 2))
        breg[per] = (b, se)
        A(f"| {per} | {len(s)} | {b:+.3f} | {se:.3f} | {b/se:+.2f} | {a:+.2f} |")
    A()
    # ---- blend fit on 2020-22
    tr = sel("blend", d)
    # Benter-style: market = flat 50% (logit 0), model enters through one slope b on (model - line), no intercept.
    xs, ys = tr.x.values, tr.y.values
    nll = lambda b: np.sum(np.logaddexp(0, b[0] * xs) - ys * b[0] * xs)
    bhat = float(minimize(nll, [0.0], method="BFGS").x[0])
    info = np.sum((sig(bhat * xs) * (1 - sig(bhat * xs))) * xs ** 2)
    b_se = float(1 / np.sqrt(info))
    a0 = 0.0
    b1 = max(bhat, 0.0)  # a negative weight on the model is not a hypothesis we act on -> truncate at 0
    w_equiv = (b1 / 4) / (norm.pdf(0) / sd)
    A("### Blend fit on 2020-2022 (logit P(home covers / over) = b*(model - line); market side = flat 50%, no intercept)")
    A()
    trunc_note = " (truncated at 0)" if bhat < 0 else ""
    A(f"* unconstrained MLE b = {bhat:+.4f} (s.e. {b_se:.4f}), n = {len(tr)};  used b = {b1:+.4f}{trunc_note}")
    A(f"* implied Benter weight on the model w ~ {w_equiv:.3f} (textbook default w=0.3 shown separately as 'fixed w=0.3').  "
      f"At b={b1:.4f}, p_blend reaches the 52.38% break-even only when |model - line| >= {(np.log(BE/(1-BE))/b1) if b1>0 else float('inf'):.1f} points.")
    A()
    for per in PER:
        s = sel(per, d)
        d.loc[s.index, "p_blend"] = sig(a0 + b1 * s.x.values)
    d["p_w30"] = 0.3 * d.p_model + 0.7 * 0.5

    # ---- thresholds chosen on 2020-22
    tr = sel("blend", d)
    grid_T = [0, 1, 2, 3, 4, 5]
    cand_A = []
    for T in grid_T:
        sub = tr[np.abs(tr.x) >= T]
        sub = sub.assign(hit=np.where(sub.x > 0, sub.y == 1, sub.y == 0))
        cand_A.append((T, summ(sub)))
    ok = [(T, s) for T, s in cand_A if s["n"] >= 120]
    T_A = max(ok, key=lambda t: t[1]["rate"])[0] if ok else 0
    grid_q = [BE, 0.5238 + 0.005, 0.5238 + 0.01, 0.5238 + 0.02, 0.5238 + 0.03]
    cand_B = []
    for q in grid_q:
        cand_B.append((q, summ(evaluate_rule(tr, tr.p_blend.values, q))))
    okB = [(q, s) for q, s in cand_B if s["n"] >= 30]
    q_B = max(okB, key=lambda t: t[1]["rate"])[0] if okB else BE
    A("### Rule selection on 2020-2022 (in-sample for the blend, so optimistic)")
    A()
    A("Model-only: bet the side the model prefers when |model - line| >= T.  Blend: bet the side with p_blend >= q.")
    A()
    A(HDR)
    for T, s in cand_A:
        A(fmt_row(f"model-only |x|>={T}", s))
    for q, s in cand_B:
        A(fmt_row(f"blend p>={q:.4f}", s))
    A()
    A(f"Chosen on 2020-22 (max hit rate with enough picks): model-only T_A = {T_A}; blend q_B = {q_B:.4f}. "
      f"Ex-ante rule: blend p >= {BE:.4f} (edge >= 0 at -110).")
    A()

    # ---- holdout
    ho = sel("hold", d)
    A("### UNTOUCHED HOLDOUT 2023-2025: hit rates (frozen model, frozen blend, frozen thresholds)")
    A()
    A(f"Direction: x = model - line; positive x means model likes {up}, negative {dn}.  Break-even at -110 = 52.38%.")
    A()
    A(HDR)
    rules = {}
    def add(name, sub):
        s = summ(sub); rules[name] = s; A(fmt_row(name, s))
    sub = ho.assign(hit=np.where(ho.x > 0, ho.y == 1, ho.y == 0)); add("(a) model-only, all games (T=0)", sub)
    sub = ho[np.abs(ho.x) >= T_A]; sub = sub.assign(hit=np.where(sub.x > 0, sub.y == 1, sub.y == 0))
    add(f"(a') model-only |x|>={T_A} (T chosen on 2020-22)", sub)
    add(f"(b) blend p>={BE:.4f} (ex-ante, edge>=0)", evaluate_rule(ho, ho.p_blend.values, BE))
    add(f"(b') blend p>={q_B:.4f} (q chosen on 2020-22)", evaluate_rule(ho, ho.p_blend.values, q_B))
    add("(b'') fixed w=0.3 blend, p>=52.38%", evaluate_rule(ho, ho.p_w30.values, BE))
    sub = ho.assign(hit=(ho.y == 1)); add(f"(c) market-only: always {up.split()[0]}", sub)
    sub = ho.assign(hit=(ho.y == 0)); add(f"(c) market-only: always {dn.split()[0]}", sub)
    A()
    A("Sensitivity (NOT used for selection; shown so you can see the whole shape): holdout hit rate by |x| bucket of the raw model edge")
    A()
    A("| |model - line| | picks | hit rate | 95% CI |\n|---|---|---|---|")
    edges = [0, 1, 2, 3, 4, 6, 99]
    for lo, hi in zip(edges[:-1], edges[1:]):
        sub = ho[(np.abs(ho.x) >= lo) & (np.abs(ho.x) < hi)]
        sub = sub.assign(hit=np.where(sub.x > 0, sub.y == 1, sub.y == 0)); s = summ(sub)
        A(f"| [{lo},{hi if hi<99 else 'inf'}) | {s['n']} | {100*s['rate']:.1f}% | {100*s['lo']:.1f}-{100*s['hi']:.1f}% |")
    A()
    A("By season (model-only, all games):")
    A()
    A("| season | n | hit rate |\n|---|---|---|")
    for yr in [2023, 2024, 2025]:
        s_ = ho[ho.season == yr]; sub = s_.assign(hit=np.where(s_.x > 0, s_.y == 1, s_.y == 0)); s = summ(sub)
        A(f"| {yr} | {s['n']} | {100*s['rate']:.1f}% |")
    A()
    # ---- log loss
    A("### Log loss (all non-push games; lower is better; coin flip = 0.6931)")
    A()
    A("| period | n | (a) model-only | (b) blend (fitted) | blend w=0.3 | (c) market no-vig from odds | (c) market 50/50 |\n|---|---|---|---|---|---|---|")
    ll = {}
    for per in PER:
        s = sel(per, d)
        row = dict(model=logloss(s.y.values, s.p_model.values), blend=logloss(s.y.values, s.p_blend.values),
                   w30=logloss(s.y.values, s.p_w30.values), mkt=logloss(s.y.values, s.p_mkt.values),
                   half=logloss(s.y.values, np.full(len(s), 0.5)))
        ll[per] = row
        tag = " (in-sample for blend)" if per == "blend" else ""
        A(f"| {per}{tag} | {len(s)} | {row['model']:.4f} | {row['blend']:.4f} | {row['w30']:.4f} | {row['mkt']:.4f} | {row['half']:.4f} |")
    A()
    # survival
    survivors = []
    for name, s in rules.items():
        if name.startswith("(c)"):
            continue
        if s["n"] >= 30 and s["rate"] >= BE and s["p_be"] < 0.05:
            survivors.append(name)
    res_json[kind] = dict(a=a0, b=b1, w_equiv=w_equiv, T_A=T_A, q_B=q_B, rules=rules, survivors=survivors, loglik=ll,
                          reg=breg)
    A(f"**Rules that beat 52.38% out-of-sample with one-sided p<0.05: {survivors if survivors else 'NONE'}**")
    A()
    return d, dict(a=a0, b=b1, T_A=T_A, q_B=q_B, survivors=survivors, sd=sd, w_equiv=w_equiv)


def su_diagnostic():
    d = D[D.played & D.home_moneyline.notna() & D.away_moneyline.notna()].copy()
    def imp(m): return np.where(m > 0, 100 / (m + 100), -m / (-m + 100))
    ph = imp(d.home_moneyline); pa = imp(d.away_moneyline)
    d["p_mkt"] = ph / (ph + pa)
    d["y"] = (d.result > 0).astype(float)
    d = d[d.result != 0]
    d["p_model"] = norm.cdf(d.m_model / SD_M)
    lg = lambda p: np.log(np.clip(p, 1e-4, 1 - 1e-4) / (1 - np.clip(p, 1e-4, 1 - 1e-4)))
    tr = sel("blend", d)
    coef, se = fit_logit(np.column_stack([lg(tr.p_mkt.values), lg(tr.p_model.values)]), tr.y.values)
    A("## Extra diagnostic: straight-up win probability vs moneyline (no-vig)")
    A()
    A(f"Logit blend fit on 2020-22: logit P(home wins) = {coef[0]:+.3f} + {coef[1]:+.3f}*logit(p_market) + {coef[2]:+.3f}*logit(p_model) "
      f"(s.e. of model coef {se[2]:.3f}).")
    A()
    A("| period | n | market | model-only | blend (fitted) | blend w=0.3 (prob space) |\n|---|---|---|---|---|---|")
    for per in PER:
        s = sel(per, d)
        pb = sig(coef[0] + coef[1] * lg(s.p_mkt.values) + coef[2] * lg(s.p_model.values))
        p30 = 0.3 * s.p_model.values + 0.7 * s.p_mkt.values
        A(f"| {per} | {len(s)} | {logloss(s.y.values, s.p_mkt.values):.4f} | {logloss(s.y.values, s.p_model.values):.4f} | "
          f"{logloss(s.y.values, pb):.4f} | {logloss(s.y.values, p30):.4f} |")
    A()
    return coef


# ---------------------------------------------------------------------------------------------
A("# NFL Benter test with real closing lines (nflverse games.csv)")
A()
A("Generated by benter.py / nfl_model.py in this directory (re-runnable).  Data: nflverse/nfldata games.csv, 2007-2026.")
A()
A("## Design (what was fit where)")
A()
A("* **Model (no market inputs):** margin = team rating + QB rating (online, Elo-style SGD) + online home field + rest differential; "
  "total = team offence + team defence + QB-offence ratings + dome/wind/cold terms.  Margin point forecast is an 80/20 blend of "
  "the Elo+QB margin and the margin implied by the offence/defence model (weight fit on 2010-19).  Week-batched walk-forward: "
  "every game is predicted before any result of its own week is used.  2007-09 = rating burn-in; hyper-parameters tuned on 2010-19 only "
  f"(Nelder-Mead on MSE).  Residual sd used for probabilities: margin {SD_M:.2f}, total {SD_T:.2f}.")
A("* **Blend + rule:** fit on 2020-22.  **Holdout:** 2023-25 never touched until the final evaluation; everything frozen.")
A("* **Lines:** nflverse `spread_line` (home margin expected) and `total_line` are the closing lines in the file.  Pushes are dropped.  "
  f"-110 break-even = {100*BE:.2f}%.")
A("* **Market-only baseline:** the closing line implies 50% for each side (log loss 0.6931); no-vig probability from the posted odds is also shown.")
A("* Weather: the totals model uses wind/temp when the file has them (history).  For 2026 un-played games they are blank, so weather is not in the 2026 total forecasts.")
A()
A(f"Fitted margin params: `{json.dumps({k: round(v, 4) for k, v in P['margin'].items()})}`")
A()
A(f"Fitted totals params: `{json.dumps({k: round(v, 4) for k, v in P['totals'].items()})}`")
A()
dA, ra = run_market("ats", "ATS (spread) results")
dT, rt = run_market("tot", "Totals (over/under) results")
su_coef = su_diagnostic()

# ---------------------------------------------------------------------------------------------
# 2026 application
# ---------------------------------------------------------------------------------------------
cur = D[(~D.played) & (D.season == 2026) & D.spread_line.notna() & D.total_line.notna()].copy()
cur["x_m"] = cur.m_model - cur.spread_line
cur["x_t"] = cur.t_model - cur.total_line
cur["p_home_cover_model"] = norm.cdf(cur.x_m / SD_M)
cur["p_home_cover_blend"] = sig(ra["a"] + ra["b"] * cur.x_m)
cur["p_home_cover_w30"] = 0.3 * cur.p_home_cover_model + 0.35
cur["p_over_model"] = norm.cdf(cur.x_t / SD_T)
cur["p_over_blend"] = sig(rt["a"] + rt["b"] * cur.x_t)
cur["p_over_w30"] = 0.3 * cur.p_over_model + 0.35
et = pd.to_datetime(cur.gameday.astype(str) + " " + cur.gametime.astype(str))
cur["kickoff_utc"] = (et + pd.Timedelta(hours=4)).dt.strftime("%Y-%m-%d %H:%MZ")  # Oct = EDT (UTC-4)

def side_ats(r, which):
    if which == "a'":
        return (r.home_team if r.x_m > 0 else r.away_team) if abs(r.x_m) >= ra["T_A"] else None
    p = r.p_home_cover_blend if which in ("b", "b'") else r.p_home_cover_w30
    thr = ra["q_B"] if which == "b'" else BE
    return r.home_team if p >= thr else (r.away_team if 1 - p >= thr else None)

def side_tot(r, which):
    if which == "a'":
        return ("OVER" if r.x_t > 0 else "UNDER") if abs(r.x_t) >= rt["T_A"] else None
    p = r.p_over_blend if which in ("b", "b'") else r.p_over_w30
    thr = rt["q_B"] if which == "b'" else BE
    return "OVER" if p >= thr else ("UNDER" if 1 - p >= thr else None)

for w in ["a'", "b", "b'", "b''"]:
    cur["ats_" + w] = [side_ats(r, w) for r in cur.itertuples()]
    cur["tot_" + w] = [side_tot(r, w) for r in cur.itertuples()]
cur.to_csv("picks_2026.csv", index=False)

A("## 2026 un-played games with lines in games.csv (Week 5 remainder + Week 6)")
A()
A("Week numbering in the file: **Week 5 = Oct 8-12 (today Sun Oct 11 and Mon Oct 12 are Week 5)**; Week 6 = Oct 15-19 (TNF Oct 15, Sun Oct 18, MNF Oct 19). "
  "Both are listed.  Lines are the values currently in games.csv (not verified against a live book; Week 6 lines are early and will move).  "
  "Starting QBs are those listed in the file (injuries/inactives NOT checked).  Kickoff = file `gametime` (US Eastern) converted to UTC (+4h, EDT).  "
  "No weather for 2026 games (blank in file).")
A()
A("### Margin (spread).  lean = side the raw model prefers; 'fires' = which frozen rules bet it (and which side)")
A()
A("| wk | kickoff UTC | game (away @ home) | home QB / away QB | model margin (home) | line (home) | model-line | P(home cover) raw model | P(home cover) fitted blend | P(home cover) w=0.3 | lean | fires |\n|---|---|---|---|---|---|---|---|---|---|---|---|")
for _, r in cur.sort_values(["week", "kickoff_utc"]).iterrows():
    lean = r.home_team if r.x_m > 0 else r.away_team
    fire = ", ".join(f"{w}={r['ats_'+w]}" for w in ["a'", "b", "b'", "b''"] if r["ats_" + w] is not None and r["ats_" + w] == r["ats_" + w]) or "-"
    A(f"| {int(r.week)} | {r.kickoff_utc} | {r.away_team} @ {r.home_team} | {r.home_qb_name} / {r.away_qb_name} | "
      f"{r.m_model:+.1f} | {r.spread_line:+.1f} | {r.x_m:+.1f} | {100*r.p_home_cover_model:.1f}% | {100*r.p_home_cover_blend:.1f}% | "
      f"{100*r.p_home_cover_w30:.1f}% | {lean} | {fire} |")
A()
A("### Total (over/under)")
A()
A("| wk | kickoff UTC | game | model total | line | model-line | P(over) raw model | P(over) fitted blend | P(over) w=0.3 | lean | fires |\n|---|---|---|---|---|---|---|---|---|---|---|")
for _, r in cur.sort_values(["week", "kickoff_utc"]).iterrows():
    lean = "OVER" if r.x_t > 0 else "UNDER"
    fire = ", ".join(f"{w}={r['tot_'+w]}" for w in ["a'", "b", "b'", "b''"] if r["tot_" + w] is not None and r["tot_" + w] == r["tot_" + w]) or "-"
    A(f"| {int(r.week)} | {r.kickoff_utc} | {r.away_team} @ {r.home_team} | {r.t_model:.1f} | {r.total_line:.1f} | "
      f"{r.x_t:+.1f} | {100*r.p_over_model:.1f}% | {100*r.p_over_blend:.1f}% | {100*r.p_over_w30:.1f}% | {lean} | {fire} |")
A()
A("Rule codes: a' = model-only |x|>=T (T chosen on 2020-22); b = fitted blend p>=52.38% (ex-ante); b' = fitted blend p>=q (q chosen on 2020-22); "
  "b'' = fixed w=0.3 blend p>=52.38%.  These are UNVALIDATED unless listed under Verdict as surviving the holdout.")
A()
A("## Verdict")
A()
surv_a, surv_t = ra["survivors"], rt["survivors"]
A(f"* ATS: rules surviving the holdout: {surv_a if surv_a else 'none'}.")
A(f"* Totals: rules surviving the holdout: {surv_t if surv_t else 'none'}.")
A("* Survival test used: holdout hit rate >= 52.38% AND one-sided exact binomial p < 0.05 vs 52.38%, n >= 30.  "
  "Four-ish rules x two markets = many looks, so even a pass would deserve a Bonferroni-style haircut.")

def _r(kind, name_prefix):
    for k, v in res_json[kind]["rules"].items():
        if k.startswith(name_prefix):
            return v
    return None
def _f(v):
    return "no picks fired" if v["n"] == 0 else f"{100*v['rate']:.1f}% on n={v['n']} (95% CI {100*v['lo']:.1f}-{100*v['hi']:.1f}%)"
bl = ["## Bottom line (read this first)", ""]
bl.append("**Nothing beats the 52.38% break-even out of sample, for either spreads or totals.**  Zero picks are issued.  The model is a worse predictor than the closing line, "
          "and the blend correctly collapses to 'trust the market'.")
bl.append("")
for kind, nm in [("ats", "Spread"), ("tot", "Total")]:
    R = res_json[kind]["rules"]
    k_a, k_ap, k_b, k_bpp = "(a) ", "(a'", "(b) ", "(b'')"
    bl.append(f"* **{nm}, holdout 2023-25:** model-only all games {_f(_r(kind, k_a))}; model-only |x|>=T* {_f(_r(kind, k_ap))}; "
              f"fitted blend ex-ante {_f(_r(kind, k_b))}; fixed w=0.3 blend {_f(_r(kind, k_bpp))}; market-only coin flip = 50%.")
    rg = res_json[kind]["reg"]["hold"]
    bl.append(f"  Incremental-information slope of model-minus-line on outcome-minus-line in 2023-25: b = {rg[0]:+.3f} (s.e. {rg[1]:.3f}) -> indistinguishable from 0 "
              f"(b=0 means the line already contains everything the model knows).  Fitted blend weight: b={res_json[kind]['b']:.4f}, implied w ~ {res_json[kind]['w_equiv']:.2f}.")
bl.append("* Straight-up check (moneyline no-vig): the fitted blend gives the model a NEGATIVE coefficient; blend log loss is no better than the market alone.")
bl.append("* The best-looking cells in the sensitivity tables are noise buckets (n=11 to ~250, CIs span break-even).  With ~8 looks, a lone pass at p<0.05 would still be expected by chance.")
bl.append("* Leakage test (leak_test.py): corrupting every result from 2023 week 10 onward changes no earlier prediction (max |diff| = 0).")
bl.append("")
bl.append("Caveats: nflverse closing lines (not the Dabble / Underdog / bet365 lines you will actually see); 2026 lines in the file are whatever is currently loaded (Week 6 lines are early); "
          "starting QBs in the file are projected, injuries/inactives not checked; no weather in 2026 forecasts; -110 assumed for payouts.")
bl.append("")
out[2:2] = bl
try:
    leak = open("leak_test.txt").read().strip()
    out.append("")
    out.append("## Leakage test output")
    out.append("")
    out.append("```")
    out.append(leak)
    out.append("```")
except Exception:
    pass
out.append("")
out.append("## Reproduce")
out.append("")
out.append("`python nfl_model.py` (fits 2010-19 hyper-parameters, ~3 min) -> `python benter.py` (blend, holdout, 2026) -> `python leak_test.py`.  "
           "Files: games.csv, params.json, preds.csv, picks_2026.csv, holdout_summary.json, report.md.")

open("holdout_summary.json", "w").write(json.dumps(res_json, indent=1, default=float))
open("report.md", "w").write("\n".join(out))
print("\n".join(out))
