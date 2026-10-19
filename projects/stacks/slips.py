"""Pick'em slip builder with same-game correlation (Gaussian copula). Research only; nothing places bets.

Each leg: marginal P(win) after the Benter blend (0.3 model + 0.7 x 50/50 line, minus push) and a corr group.
P(slip wins) = P(all legs win) from a multivariate normal orthant with latent rho per pair type, measured
leak-free in corr.py. Pairs not listed are independent (rho 0), which corr.py found for opposing QBs,
WNBA teammates and WNBA opponents.

usage: python slips.py validate <corr.json>
       python slips.py build <legs.json> <payouts.json> [bankroll]
"""
import itertools, json, sys
import numpy as np
from scipy.stats import norm, multivariate_normal

# latent rho by (role_a, role_b, same_team) from corr.json; sign flips when the two legs take opposite sides
RHO = {
    ("QB_pass_yds", "WR1_rec_yds"): 0.402, ("QB_pass_yds", "WR2_rec_yds"): 0.325,
    ("QB_pass_yds", "TE1_rec_yds"): 0.287, ("QB_pass_tds", "WR1_rec_yds"): 0.197,
    ("QB_pass_yds", "WR1_receptions"): 0.310, ("QB_pass_yds", "RB1_rush_yds"): -0.077,
    ("WR1_rec_yds", "WR2_rec_yds"): 0.0, ("WR1_rec_yds", "TE1_rec_yds"): 0.0, ("WR2_rec_yds", "TE1_rec_yds"): 0.0,
    ("P_points", "P_rebounds"): 0.240, ("P_points", "P_assists"): 0.134,
}


def rho(a, b):
    """a, b: dicts with role, team, side ('MORE'/'LESS'). Same-team pairs only; cross-team = 0."""
    if a["team"] != b["team"] or a.get("game") != b.get("game"):
        return 0.0
    if a["role"].startswith("P_") and a.get("player") != b.get("player"):
        return 0.0                        # WNBA teammates: measured ~0
    r = RHO.get((a["role"], b["role"]), RHO.get((b["role"], a["role"]), 0.0))
    return r if a["side"] == b["side"] else -r


def p_all(legs):
    p = np.array([l["p"] for l in legs])
    if len(legs) == 1:
        return float(p[0])
    C = np.eye(len(legs))
    for i, j in itertools.combinations(range(len(legs)), 2):
        C[i, j] = C[j, i] = rho(legs[i], legs[j])
    # win iff latent Z_i <= Phi^-1(p_i)
    return float(multivariate_normal(mean=np.zeros(len(legs)), cov=C, allow_singular=True).cdf(norm.ppf(p)))


def validate(corr_path):
    """Copula with the empirical marginals must reproduce the observed joint hit rates."""
    c = json.load(open(corr_path))
    rows = []
    for r in c["nfl_pairs"] + c["wnba_pairs"]:
        rho_ = r["latent_rho"]
        for side, pa, pb, obs in (("over", r["p_a_over"], r["p_b_over"], r["p_over_over"]),
                                  ("under", 1 - r["p_a_over"], 1 - r["p_b_over"], r["p_under_under"])):
            pred = multivariate_normal(mean=[0, 0], cov=[[1, rho_], [rho_, 1]]).cdf(norm.ppf([pa, pb]))
            rows.append((r["pair"], side, r["n"], obs, round(float(pred), 3), round(float(pred - obs), 3)))
    for name, s, n, obs, pred, err in rows:
        print(f"{name:48s} {s:5s} n={n:5d} observed {obs:.3f} copula {pred:.3f} err {err:+.3f}")
    print("max |err|:", max(abs(r[5]) for r in rows))


def build(legs_path, payouts_path, bankroll=100.0):
    legs = json.load(open(legs_path))
    pay = {int(k): v for k, v in json.load(open(payouts_path)).items()}   # {n_legs: multiplier}
    out = []
    for n, mult in sorted(pay.items()):
        for combo in itertools.combinations(legs, n):
            if len({(l["player"], l["market"]) for l in combo}) < n:
                continue
            p = p_all(list(combo))
            ev = mult * p - 1
            b = mult - 1
            kelly = max(0.0, (b * p - (1 - p)) / b)
            stake = 0.0 if ev <= 0 else float(np.clip(round(0.25 * kelly * bankroll), 1, 5))
            out.append(dict(n=n, mult=mult, legs=[f"{l['player']} {l['market']} {l['side']} {l['line']}" for l in combo],
                            p_win=round(p, 4), p_indep=round(float(np.prod([l['p'] for l in combo])), 4),
                            ev_per_dollar=round(ev, 3), quarter_kelly=round(0.25 * kelly, 4), stake=stake))
    out.sort(key=lambda r: -r["ev_per_dollar"])
    return out


if __name__ == "__main__":
    if sys.argv[1] == "validate":
        validate(sys.argv[2])
    else:
        res = build(sys.argv[2], sys.argv[3], float(sys.argv[4]) if len(sys.argv) > 4 else 100.0)
        json.dump(res, open(sys.argv[2].replace(".json", "_slips.json"), "w"), indent=1)
        for r in res[:25]:
            print(f"{r['n']}-pick {r['mult']}x  p_win {r['p_win']:.3f} (indep {r['p_indep']:.3f})  EV/$ {r['ev_per_dollar']:+.3f}  stake ${r['stake']:.0f}  | " + " + ".join(r["legs"]))
