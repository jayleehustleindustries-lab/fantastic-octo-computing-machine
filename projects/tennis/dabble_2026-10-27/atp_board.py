"""ATP board Tue Oct 27 2026 (Vienna/Basel 500s, indoor hard). Research only.
p_fav = no-vig average odds (tennisexplorer). ATP sim uses tour-average 80.5% hold (UNVALIDATED; big servers hold more,
so totals/tiebreaks are biased LOW for them). Prints: median total, P(fav games won > 11.5) and the line cutoffs."""
import sys, numpy as np
T = sys.argv[1]; sys.path.insert(0, T + "/atp"); import sim as atp
BE3, BE2 = 6 ** (-1/3), 3 ** -0.5
M = [  # CT time, fav, dog, event, fav odds, dog odds
 ("6:00 AM", "Hurkacz", "Bergs", "Basel", 1.55, 2.44), ("7:30 AM", "Paul", "Rublev", "Vienna", 1.70, 2.14),
 ("7:30 AM", "Rinderknech", "Kym", "Basel", 1.99, 1.80), ("8:00 AM", "Jodar", "Tabilo", "Basel", 1.28, 3.63),
 ("9:00 AM", "Alcaraz", "Khachanov", "Vienna", 1.21, 4.41), ("9:00 AM", "Mannarino", "Buse", "Vienna", 1.54, 2.46),
 ("9:00 AM", "Michelsen", "Van de Zandschulp", "Basel", 1.47, 2.68), ("9:30 AM", "Fils", "Mpetshi Perricard", "Basel", 1.26, 3.85),
 ("11:30 AM", "Zverev", "Landaluce", "Vienna", 1.08, 7.68), ("11:30 AM", "F. Cerundolo", "Norrie", "Vienna", 1.46, 2.69),
 ("12:00 PM", "Shelton", "Kovacevic", "Basel", 1.20, 4.56), ("1:30 PM", "Lehecka", "Wawrinka", "Basel", 1.19, 4.65),
 ("2:00 PM", "Cobolli", "Dimitrov", "Vienna", 1.49, 2.58)]
p0 = atp.inv_hold(0.805)
bl = lambda p: 0.3 * p + 0.35
for i, (t, f, d, ev, of, od) in enumerate(M):
    p = (1 / of) / (1 / of + 1 / od)
    res = []
    for j, pp in enumerate((max(0.5, p - 0.05), p, min(0.95, p + 0.05))):
        d0 = atp.calibrate_d0(p0, p0, pp, 0.0205)
        _, three, ga, gb = atp.sim_match(p0, p0, d0, 0.0205, 150000, np.random.default_rng(100 + 7 * i + j))
        res.append((ga + gb, ga, gb))
    tot, ga, gb = res[1]
    gw = min(float((r[1] > 11.5).mean()) for r in res)
    more = [L + 0.5 for L in range(14, 30) if min((r[0] > L + 0.5).mean() for r in res) >= (BE3 - 0.35) / 0.3]
    less = [L + 0.5 for L in range(14, 30) if min((r[0] < L + 0.5).mean() for r in res) >= (BE3 - 0.35) / 0.3]
    dl = [L + 0.5 for L in range(2, 14) if min((r[2] < L + 0.5).mean() for r in res) >= (BE3 - 0.35) / 0.3]
    print(f"{t:>8} {ev:6s} {f} v {d}: p_fav {p:.3f} | total median {np.median(tot):.0f} | {f} games MORE 11.5: {gw:.3f} -> blend {bl(gw):.3f} "
          f"{'2-PICK' if bl(gw) >= BE2 else '3-PICK' if bl(gw) >= BE3 else 'no'} | total MORE<= {max(more) if more else '-'} LESS>= {min(less) if less else '-'} "
          f"| {d} games LESS>= {min(dl) if dl else '-'}")
