"""Dabble tennis cut-off cards, overnight Sun Oct 18 -> Mon Oct 19 2026 (CT). Research only; nothing places bets.

For each match: the most generous Dabble line at which MORE (or LESS) on total games / games won still clears a
pick'em break-even after the Benter blend (0.3 model + 0.7 x 50/50 line), in ALL three p_fav scenarios (lo/mid/hi).
p_fav comes from the no-vig public moneyline when one was verified, else a rank-based prior range (flagged).
WTA: wta/wta_mc.py (best of 3, tiebreak every set). ATP: atp/sim.py with tour-average 80.5% hold (assumed, unvalidated).

usage: python cards.py <tennis_dir> <matches.json> <out.json>
"""
import sys, json, numpy as np
sys.path.insert(0, sys.argv[1] + "/wta")
sys.path.insert(0, sys.argv[1] + "/atp")
import wta_mc as w
import sim as atp

W = 0.3
BE = {"2-pick 3x": 3 ** -0.5, "3-pick 6x": 6 ** (-1/3), "5-pick 20x": 20 ** (-1/5)}
RAW = {k: (v - (1 - W) * 0.5) / W for k, v in BE.items()}   # raw model p a pick'em leg needs
LINES = [x + 0.5 for x in range(14, 32)]
GLINES = [x + 0.5 for x in range(3, 17)]
ATP_HOLD, ATP_SIGMA = 0.805, 0.0205


def run(tour, p, seed):
    if tour.startswith("WTA") or tour == "ITF-W":
        d = w.solve_symmetric(p, n=150000, seed=seed)
        r = w.simulate(w.MU + d, (1 - w.MU) + d, w.MU - d, (1 - w.MU) - d, n=300000, seed=seed + 1)
        return r["total"], r["gamesA"], r["gamesB"], r["nsets"] == 3
    p0 = atp.inv_hold(ATP_HOLD)
    d0 = atp.calibrate_d0(p0, p0, p, ATP_SIGMA)
    _, three, ga, gb = atp.sim_match(p0, p0, d0, ATP_SIGMA, 300000, np.random.default_rng(seed + 1))
    return ga + gb, ga, gb, three


def cut(samples, lines, need):
    """Most generous line at which MORE (LESS) clears in every scenario: (max MORE line, min LESS line)."""
    more = [L for L in lines if min((s > L).mean() for s in samples) >= need]
    less = [L for L in lines if min((s < L).mean() for s in samples) >= need]
    return (max(more) if more else None, min(less) if less else None)


matches = json.load(open(sys.argv[2]))
cards = []
for i, m in enumerate(matches):
    sims = [run(m["tour"], p, 10 + 30 * j + i) for j, p in enumerate((m["p_lo"], m["p_mid"], m["p_hi"]))]
    tot, ga, gb, three = sims[1]
    card = dict(m, median_total=float(np.median(tot)), mean_total=round(float(tot.mean()), 2),
                p_3sets=round(float(three.mean()), 3),
                median_games_fav=float(np.median(ga)), median_games_dog=float(np.median(gb)),
                p_over={str(L): round(float((tot > L).mean()), 3) for L in LINES},
                cut_total={k: cut([s[0] for s in sims], LINES, v) for k, v in RAW.items()},
                cut_games_fav={k: cut([s[1] for s in sims], GLINES, v) for k, v in RAW.items()},
                cut_games_dog={k: cut([s[2] for s in sims], GLINES, v) for k, v in RAW.items()})
    cards.append(card)
    print(f"\n{m['time']} {m['fav']} v {m['dog']} [{m['tour']} {m['event']}] p_fav {m['p_lo']}/{m['p_mid']}/{m['p_hi']} ({m['p_source']})")
    print(f"  total games: median {card['median_total']}, mean {card['mean_total']}, P(3 sets) {card['p_3sets']}")
    print(f"  games won median: {m['fav']} {card['median_games_fav']}, {m['dog']} {card['median_games_dog']}")
    for name, key in (("total", "cut_total"), (m["fav"], "cut_games_fav"), (m["dog"], "cut_games_dog")):
        print(f"  {name:>14}: " + "; ".join(f"{k}: MORE<={v[0]} LESS>={v[1]}" for k, v in card[key].items()))
json.dump(dict(raw_needed=RAW, break_even=BE, cards=cards), open(sys.argv[3], "w"), indent=1)
print("\nraw model p needed:", {k: round(v, 3) for k, v in RAW.items()})
