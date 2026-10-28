"""Break-points-won legs re-priced with each player's 2026 hold / opponent-hold (matchstat), combined by odds ratio
against the tour average. Total games (so service games) still come from the cards.py simulators. UNVALIDATED."""
import sys, numpy as np
T = sys.argv[1]; sys.path.insert(0, T + "/wta"); sys.path.insert(0, T + "/atp")
import wta_mc as w, sim as atp
rng = np.random.default_rng(3); W = 0.3; BE = 6 ** (-1 / 3)
odds = lambda p: p / (1 - p)
def p_break(server_hold, returner_opp_hold, avg_hold):
    o = odds(1 - server_hold) * odds(1 - returner_opp_hold) / odds(1 - avg_hold)
    return o / (1 + o)
def totals(tour, p):
    if tour == "WTA":
        d = w.solve_symmetric(p, n=120000, seed=4)
        return w.simulate(w.MU + d, (1 - w.MU) + d, w.MU - d, (1 - w.MU) - d, n=200000, seed=5)["total"]
    p0 = atp.inv_hold(0.805); d0 = atp.calibrate_d0(p0, p0, p, 0.0205)
    _, _, ga, gb = atp.sim_match(p0, p0, d0, 0.0205, 200000, np.random.default_rng(6)); return ga + gb
LEGS = [  # leg, tour, p_fav, breaker returner opp-hold, server hold, line, side, source numbers
 ("Duckworth MORE 0.5", "ATP", 0.80, 0.833, 0.881, 0.5, "MORE"),
 ("Fernandez LESS 4.5", "WTA", 0.56, 0.677, 0.699, 4.5, "LESS"),
 ("Shnaider LESS 4.5", "WTA", 0.51, 0.631, 0.699, 4.5, "LESS"),
 ("Jovic LESS 4.5", "WTA", 0.51, 0.595, 0.716, 4.5, "LESS"),
]
AVG = {"ATP": 0.80, "WTA": 0.64}
for leg, tour, p, ret_opp_hold, srv_hold, L, side in LEGS:
    tot = totals(tour, p); n = np.floor(tot / 2).astype(int)
    pb = p_break(srv_hold, ret_opp_hold, AVG[tour])
    out = []
    for adj in (-0.03, 0.0, 0.03):      # +/-3 pts on the per-game break rate (form, conditions)
        b = rng.binomial(n, np.clip(pb + adj + rng.normal(0, 0.03, len(n)), 0.01, 0.9))
        pm = float((b > L).mean()) if side == "MORE" else float((b < L).mean())
        out.append(pm)
    bl = W * out[1] + (1 - W) * 0.5
    print(f"{leg:20s} break rate/game {pb:.3f}  model {out[1]:.3f} (range {min(out):.3f}-{max(out):.3f})  "
          f"blend {bl:.4f}  {'CLEARS' if bl >= BE else 'below'} 3-pick {BE:.4f}")
