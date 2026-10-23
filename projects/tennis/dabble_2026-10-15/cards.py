"""Dabble Tennis W total-games cards, Oct 15 2026. Research only.
p_fav = rough prior (public rank/Elo snippets, no live price found). Totals barely move for p_fav 0.50-0.65."""
import sys, json, numpy as np
sys.path.insert(0, sys.argv[1])
import wta_mc as m

W = 0.3
BE = {"2-pick 3x": 3 ** -0.5, "3-pick 6x": 6 ** (-1/3), "5-pick 20x": 20 ** (-1/5), "-110": 110/210}
RAW = {k: (v - (1 - W) * 0.5) / W for k, v in BE.items()}   # raw model p a pick'em leg needs

MATCHES = [  # (CT time, event, fav, dog, p_fav_lo, p_fav_mid, p_fav_hi, note)
    ("2:30 AM", "Wuhan WTA 1000, outdoor hard", "Ostapenko", "Fernandez", 0.50, 0.50, 0.60, "Elo pages conflict (60.5% Ostapenko on 2026 stats vs 73.5% Fernandez on 2025 stats)"),
    ("3:00 AM", "Rovereto WTA 125, indoor hard", "Brancaccio", "Lazaro Garcia", 0.50, 0.50, 0.60, "Brancaccio won their June 2026 meeting 6-3 6-4"),
    ("6:10 AM", "Rovereto WTA 125, indoor hard", "Salkova", "Hruncakova", 0.50, 0.57, 0.65, "Salkova #128 vs Hruncakova #222; Hruncakova won the only H2H (2024)"),
    ("6:10 AM", "Rovereto WTA 125, indoor hard", "F. Jones", "F. Jorge", 0.50, 0.60, 0.70, "Jones #106 (Sep 14); Jorge mostly ITF level"),
    ("6:30 AM", "Rovereto WTA 125, indoor hard", "Zidansek", "Steur", 0.55, 0.65, 0.75, "Zidansek won the Bari WTA 125 (Aug 2026); Steur rank not found"),
    ("8:30 AM", "Rovereto WTA 125, indoor hard", "Masarova", "Mintegi Del Olmo", 0.50, 0.55, 0.60, "April 2026 meeting priced near 50/50; Masarova won"),
    ("9:30 AM", "Rovereto WTA 125, indoor hard", "Koevermans", "Boskovic", 0.50, 0.58, 0.65, "Koevermans #231 vs Boskovic ~#316-341"),
]
LINES = [17.5, 18.5, 19.5, 20.5, 21.5, 22.5, 23.5, 24.5, 25.5, 26.5]
GLINES = [8.5, 9.5, 10.5, 11.5, 12.5, 13.5]

def run(p, seed):
    d = m.solve_symmetric(p, n=200000, seed=seed)
    return m.simulate(m.MU + d, (1 - m.MU) + d, m.MU - d, (1 - m.MU) - d, n=400000, seed=seed + 1)

def cut(r_lo, r_mid, r_hi, need):
    """Most generous line at which MORE (or LESS) clears in ALL three p_fav scenarios."""
    more = [L for L in LINES if min((x['total'] > L).mean() for x in (r_lo, r_mid, r_hi)) >= need]
    less = [L for L in LINES if min((x['total'] < L).mean() for x in (r_lo, r_mid, r_hi)) >= need]
    return (max(more) if more else None, min(less) if less else None)

out = []
for i, (t, ev, fav, dog, lo, mid, hi, note) in enumerate(MATCHES):
    r_lo, r_mid, r_hi = run(lo, 10 + i), run(mid, 40 + i), run(hi, 70 + i)
    tot = r_mid['total']
    card = dict(time=t, event=ev, fav=fav, dog=dog, p_fav=[lo, mid, hi], note=note,
                median=float(np.median(tot)), mean=round(float(tot.mean()), 2), sd=round(float(tot.std()), 2),
                p_3sets=round(float((r_mid['nsets'] == 3).mean()), 3),
                p_over={str(L): [round(float((x['total'] > L).mean()), 3) for x in (r_lo, r_mid, r_hi)] for L in LINES},
                games_fav={str(L): round(float((r_mid['gamesA'] > L).mean()), 3) for L in GLINES},
                games_dog={str(L): round(float((r_mid['gamesB'] > L).mean()), 3) for L in GLINES},
                med_games_fav=float(np.median(r_mid['gamesA'])), med_games_dog=float(np.median(r_mid['gamesB'])),
                cutoffs={k: cut(r_lo, r_mid, r_hi, RAW[k]) for k in RAW})
    out.append(card)
    print(f"\n{t} {fav} v {dog} [{ev}] p_fav {lo}/{mid}/{hi}")
    print(f"  total: median {card['median']}, mean {card['mean']}, sd {card['sd']}, P(3 sets) {card['p_3sets']}")
    print("  P(over L) lo/mid/hi: " + "  ".join(f"{L}:{v[1]:.2f}({v[0]:.2f}-{v[2]:.2f})" for L, v in card['p_over'].items()))
    print(f"  games won median: {fav} {card['med_games_fav']}, {dog} {card['med_games_dog']}")
    print("  cutoffs (MORE if line <= x, LESS if line >= y): " + "; ".join(f"{k}: MORE<={v[0]} LESS>={v[1]}" for k, v in card['cutoffs'].items()))
json.dump(dict(raw_needed=RAW, break_even=BE, cards=out), open(sys.argv[2], "w"), indent=1)
print("\nraw model p needed:", {k: round(v, 3) for k, v in RAW.items()})
