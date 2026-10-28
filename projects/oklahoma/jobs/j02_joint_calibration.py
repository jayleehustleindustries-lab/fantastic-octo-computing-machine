"""J02: fit the points/rebounds/assists copula from walk-forward residuals and test combo-prop pricing.

Compares P(over) for P+R, P+A, R+A, PRA under (a) independent margins and (b) the copula, scored on
log loss at a stand-in line. Output: reports/copula.json (used by the projector) and reports/jobs/j02_*.csv.
Gate: adopt the copula for combos only if it lowers log loss in most seasons.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from jobs import common as C
from oklahoma import joint
from oklahoma.models import ContextGLMPlus2  # noqa: F401  (rows come from the backtest of this model)

M = ["points", "rebounds", "assists"]
COMBOS = {"pr": (0, 1), "pa": (0, 2), "ra": (1, 2), "pra": (0, 1, 2)}


def load_rows() -> pd.DataFrame:
    r = pd.read_parquet(C.ROOT / "reports" / "backtest_rows.parquet")
    r = r[(r.model == "context_glm_plus2") & r.market.isin(M)]
    wide = r.pivot_table(index=["season", "game_id", "athlete_id", "position"], columns="market",
                         values=["actual", "mu", "alpha"], aggfunc="first")
    wide.columns = [f"{a}_{b}" for a, b in wide.columns]
    return wide.dropna().reset_index()


def main():
    ap = C.parser(__doc__); ap.add_argument("--draws", type=int, default=2000); args = ap.parse_args()
    rng = np.random.default_rng(11)
    w = load_rows()
    if args.quick:
        w = w[w.season.isin(C.seasons(args))].head(3000)
    z = np.column_stack([joint.normal_scores(w[f"actual_{m}"], w[f"mu_{m}"], w[f"alpha_{m}"], rng) for m in M])
    pos = w["position"].fillna("?").str[0].replace({"?": "G"})
    corr = {"all": joint.fit_corr(z)}
    for g in ["G", "F", "C"]:
        sel = (pos == g).to_numpy()
        if sel.sum() > 500:
            corr[g] = joint.fit_corr(z[sel])
    joint.save(corr)
    print("correlation (all):\n", corr["all"].round(3))

    sub = w.sample(min(len(w), 400 if args.quick else 20000), random_state=3)
    rows = []
    for _, r in sub.iterrows():
        mu = [r[f"mu_{m}"] for m in M]; al = [r[f"alpha_{m}"] for m in M]
        c = corr.get(str(r.position)[:1], corr["all"])
        dep = joint.simulate(mu, al, c, args.draws, rng)
        ind = joint.simulate(mu, al, np.eye(3), args.draws, rng)
        for k, idx in COMBOS.items():
            actual = sum(r[f"actual_{M[i]}"] for i in idx)
            line = np.floor(sum(mu[i] for i in idx)) + 0.5
            rows.append({"season": r.season, "combo": k, "went_over": float(actual > line),
                         "p_dep": float((dep[:, list(idx)].sum(1) > line).mean()),
                         "p_ind": float((ind[:, list(idx)].sum(1) > line).mean())})
    d = pd.DataFrame(rows)
    ll = lambda p, y: -(y * np.log(p.clip(.005, .995)) + (1 - y) * np.log((1 - p).clip(.005, .995)))
    d["ll_dep"], d["ll_ind"] = ll(d.p_dep, d.went_over), ll(d.p_ind, d.went_over)
    out = d.groupby(["combo", "season"])[["ll_dep", "ll_ind"]].mean().assign(gain=lambda x: x.ll_ind - x.ll_dep).round(4)
    C.OUT.mkdir(parents=True, exist_ok=True); out.to_csv(C.OUT / "j02_joint.csv")
    print(out.to_string())


if __name__ == "__main__":
    main()
