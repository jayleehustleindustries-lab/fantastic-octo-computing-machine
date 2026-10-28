"""Price the owner's Dabble men's lines, Tue Oct 27 2026 (Vienna/Basel 500, indoor hard). Research only.
Per-player 52-week hold % and return-games-won % from the ATP stats leaderboard (dl/*.json); missing players use a
flagged prior. Matchup hold = odds-ratio of server hold and returner's return-games-won vs the tour average (80%).
d0 is then calibrated so the sim reproduces the no-vig market win probability. Scenarios: p_fav +/-0.05 and an
indoor bump of +1.5 hold points. A side is reported only with the WORST scenario. Integer lines: push removed and
the line counts as 50/50 among non-push outcomes (pick'em blend 0.3 model + 0.7 x 0.5).
usage: python atp_dabble.py <tennis_dir>"""
import sys, numpy as np
sys.path.insert(0, sys.argv[1] + "/atp"); import sim as atp
SIG, AVG = 0.0205, 0.80
odds = lambda p: p / (1 - p); inv = lambda o: o / (1 + o)
H = {  # hold, return-games-won (52w ATP leaderboard); * = prior, not found on the leaderboard
 "Kym": (0.82, 0.18, "*"), "Rinderknech": (0.867, 0.149, ""), "Cobolli": (0.795, 0.203, ""), "Dimitrov": (0.84, 0.19, "*"),
 "Nakashima": (0.875, 0.190, ""), "Griekspoor": (0.833, 0.133, ""), "Jodar": (0.799, 0.294, ""), "Tabilo": (0.830, 0.181, ""),
 "Michelsen": (0.815, 0.215, ""), "Van de Zandschulp": (0.796, 0.219, ""), "Alcaraz": (0.875, 0.301, ""), "Khachanov": (0.865, 0.206, ""),
 "Mannarino": (0.759, 0.157, ""), "Buse": (0.747, 0.249, ""), "Fils": (0.861, 0.223, ""), "Mpetshi Perricard": (0.89, 0.10, "* ret"),
 "F. Cerundolo": (0.783, 0.288, ""), "Norrie": (0.816, 0.198, ""), "Zverev": (0.894, 0.217, ""), "Landaluce": (0.774, 0.205, ""),
 "Shelton": (0.898, 0.150, ""), "Kovacevic": (0.850, 0.092, ""), "Lehecka": (0.875, 0.180, ""), "Wawrinka": (0.80, 0.17, "*")}
M = [  # Dabble time CT, fav, dog, fav odds, dog odds (None = no price found), Dabble total line
 ("7:10 AM", "Kym", "Rinderknech", 1.80, 1.99, 23.5), ("7:30 AM", "Cobolli", "Dimitrov", 1.49, 2.58, 23),
 ("7:30 AM", "Nakashima", "Griekspoor", None, None, 23), ("8:00 AM", "Jodar", "Tabilo", 1.28, 3.63, 22),
 ("8:20 AM", "Michelsen", "Van de Zandschulp", 1.47, 2.68, 22.5), ("8:40 AM", "Alcaraz", "Khachanov", 1.21, 4.41, 22),
 ("9:00 AM", "Mannarino", "Buse", 1.54, 2.46, 22.5), ("9:10 AM", "Fils", "Mpetshi Perricard", 1.26, 3.85, 23.5),
 ("10:10 AM", "F. Cerundolo", "Norrie", 1.46, 2.69, 22.5), ("11:30 AM", "Zverev", "Landaluce", 1.08, 7.68, 21),
 ("12:00 PM", "Shelton", "Kovacevic", 1.20, 4.56, 23), ("1:10 PM", "Lehecka", "Wawrinka", 1.19, 4.65, 22.5)]
def mhold(s, r, bump):  # server hold vs this returner
    hs, _, _ = H[s]; _, rr, _ = H[r]
    return min(0.97, inv(odds(min(0.97, hs + bump)) * odds(1 - rr) / odds(AVG)))
bl = lambda c: 0.3 * c + 0.35
out = {}
for i, (t, f, d, of, od, L) in enumerate(M):
    p = 0.5 if of is None else (1 / of) / (1 / of + 1 / od)
    width = 0.08 if of is None else 0.05
    rows = []
    for bump in (0.0, 0.015):
        hf, hd = mhold(f, d, bump), mhold(d, f, bump)
        for pp in (max(0.5 if of else 0.42, p - width), p, min(0.95, p + width)):
            pf, pd = atp.inv_hold(hf), atp.inv_hold(hd)
            d0 = atp.calibrate_d0(pf, pd, pp, SIG)
            _, three, ga, gb = atp.sim_match(pf, pd, d0, SIG, 120000, np.random.default_rng(500 + 11 * i + int(bump * 1000) + int(pp * 100)))
            tot = ga + gb; eq = (tot == L).mean()
            rows.append(dict(bump=bump, p=pp, hf=hf, hd=hd, med=np.median(tot), less=(tot < L).mean() / (1 - eq),
                             more=(tot > L).mean() / (1 - eq), push=eq, ga=ga, gb=gb, tot=tot, pd=pd, d0=d0))
    base = rows[1]
    lw, mw = min(r["less"] for r in rows), min(r["more"] for r in rows)
    side, worst = ("LESS", lw) if base["less"] > base["more"] else ("MORE", mw)
    flags = ",".join(n for n in (f, d) if H[n][2])
    out[(f, d)] = (side, base[side.lower()], worst, base, rows)
    print(f"{t:>8} {f} v {d} line {L}: p_fav {p:.2f} | holds {base['hf']:.3f}/{base['hd']:.3f} | median {base['med']:.0f} push {base['push']:.3f} "
          f"| lean {side} {base[side.lower()]:.3f} (worst {worst:.3f}) blend {bl(base[side.lower()]):.3f} worst-blend {bl(worst):.3f}"
          + (f" | PRIOR: {flags}" if flags else ""))
# Cerundolo break points won (integer line 3) = breaks of Norrie's serve
rng = np.random.default_rng(9)
for r in [x for x in out[("F. Cerundolo", "Norrie")][4]]:
    hB = atp.hold_prob(r["pd"] - r["d0"])
    nB = np.where(rng.random(len(r["tot"])) < 0.5, np.floor(r["tot"] / 2), np.ceil(r["tot"] / 2)).astype(int)
    b = rng.binomial(nB, 1 - hB); eq = (b == 3).mean()
    print(f"  Cerundolo BP won line 3 (bump {r['bump']}, p {r['p']:.2f}): Norrie hold {hB:.3f}; LESS {(b < 3).mean() / (1 - eq):.3f} "
          f"MORE {(b > 3).mean() / (1 - eq):.3f} push {eq:.3f} median {np.median(b):.0f}")
