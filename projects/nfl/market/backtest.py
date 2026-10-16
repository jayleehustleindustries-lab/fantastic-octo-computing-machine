"""Situational ATS / totals backtest on nflverse games.csv (closing lines), 2015-2025 REG season.

Re-runnable: python backtest.py   (reads games.csv in same dir)

Conventions (nflverse): spread_line is from HOME perspective, positive = home favored.
  home covers iff result > spread_line   (result = home_score - away_score)
  push iff result == spread_line
  over iff total > total_line
Pick'em juice assumed -110 (break-even 52.38%). Pushes dropped from win-rate (treated as no action).
"""
import numpy as np
import pandas as pd
from scipy import stats

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 50)
pd.set_option("display.max_rows", 200)

g = pd.read_csv("games.csv")
h = g[(g.season.between(2015, 2025)) & (g.game_type == "REG")].copy()
h = h.dropna(subset=["result", "spread_line", "total_line"])
h["home_cov"] = np.sign(h.result - h.spread_line)  # +1 home covers, -1 away covers, 0 push
h["over"] = np.sign(h.total - h.total_line)  # +1 over, -1 under
h["hfav"] = h.spread_line > 0
h["afav"] = h.spread_line < 0
h["abs_sp"] = h.spread_line.abs()
BE = 110 / 210  # 0.5238

print(f"N games 2015-2025 REG with lines: {len(h)}")
print(f"Overall: home ATS {(h.home_cov==1).sum()}-{(h.home_cov==-1).sum()}-{(h.home_cov==0).sum()}; "
      f"over {(h.over==1).sum()}-{(h.over==-1).sum()}-{(h.over==0).sum()}")


def rec(name, wins, losses, season_wins=None):
    n = wins + losses
    if n == 0:
        return dict(spot=name, n=0)
    p = wins / n
    z = (wins - 0.5 * n) / np.sqrt(0.25 * n)
    pval = 2 * (1 - stats.norm.cdf(abs(z)))
    # test vs break-even for the better side
    return dict(spot=name, n=n, w=wins, l=losses, hit=round(p, 4), z=round(z, 2), p_two_sided=round(pval, 4),
                edge_vs_BE=round(p * (100 / 110 + 1) - 1, 4))


def split_halves(df, col_win):
    """hit-rate in 2015-2020 and 2021-2025 for stability."""
    a = df[df.season <= 2020]
    b = df[df.season >= 2021]
    return (round(col_win(a).mean(), 3) if len(a) else None, len(a), round(col_win(b).mean(), 3) if len(b) else None, len(b))


rows = []


def ats_spot(name, mask_home_side=None, df=None, side="home"):
    """Evaluate ATS for a boolean mask. side='home' -> bet home team, 'away' -> bet away team."""
    d = df if df is not None else h
    d = d[d.home_cov != 0]
    if side == "home":
        w = (d.home_cov == 1)
    else:
        w = (d.home_cov == -1)
    n = len(d)
    r = rec(name, int(w.sum()), int((~w).sum()))
    a = d[d.season <= 2020]
    b = d[d.season >= 2021]
    wa = ((a.home_cov == 1) if side == "home" else (a.home_cov == -1))
    wb = ((b.home_cov == 1) if side == "home" else (b.home_cov == -1))
    r["h1_2015_20"] = f"{wa.mean():.3f} (n={len(a)})" if len(a) else "-"
    r["h2_2021_25"] = f"{wb.mean():.3f} (n={len(b)})" if len(b) else "-"
    rows.append(r)


def tot_spot(name, df, side="under"):
    d = df[df.over != 0]
    w = (d.over == -1) if side == "under" else (d.over == 1)
    r = rec(name, int(w.sum()), int((~w).sum()))
    a = d[d.season <= 2020]
    b = d[d.season >= 2021]
    wa = ((a.over == -1) if side == "under" else (a.over == 1))
    wb = ((b.over == -1) if side == "under" else (b.over == 1))
    r["h1_2015_20"] = f"{wa.mean():.3f} (n={len(a)})" if len(a) else "-"
    r["h2_2021_25"] = f"{wb.mean():.3f} (n={len(b)})" if len(b) else "-"
    rows.append(r)


nonneutral = h[h.location == "Home"]

# ---------- ATS spots ----------
ats_spot("Home dogs (any) -> bet HOME", df=nonneutral[nonneutral.afav], side="home")
ats_spot("Home dogs +3 or more -> bet HOME", df=nonneutral[nonneutral.spread_line <= -3], side="home")
ats_spot("Home dogs +6 or more -> bet HOME", df=nonneutral[nonneutral.spread_line <= -6], side="home")
ats_spot("Home favs (any) -> bet HOME", df=nonneutral[nonneutral.hfav], side="home")
ats_spot("Big home favs 7+ -> bet HOME", df=nonneutral[nonneutral.spread_line >= 7], side="home")
ats_spot("Big home favs 7+ -> bet AWAY dog", df=nonneutral[nonneutral.spread_line >= 7], side="away")
ats_spot("Road dogs 7+ -> bet AWAY", df=nonneutral[nonneutral.spread_line >= 7], side="away")
ats_spot("Road favs (any) -> bet AWAY", df=nonneutral[nonneutral.afav], side="away")
ats_spot("Division games: bet home dog", df=nonneutral[(nonneutral.div_game == 1) & nonneutral.afav], side="home")
ats_spot("Division games: bet road dog", df=nonneutral[(nonneutral.div_game == 1) & nonneutral.hfav], side="away")

# rest
ats_spot("Home team rest>=10 (off bye/mini-bye) -> bet HOME", df=nonneutral[(nonneutral.home_rest >= 10) & (nonneutral.away_rest <= 8)], side="home")
ats_spot("Away team rest>=10 (off bye/mini-bye) -> bet AWAY", df=nonneutral[(nonneutral.away_rest >= 10) & (nonneutral.home_rest <= 8)], side="away")
ats_spot("Away team rest>=10 -> bet AWAY (any home rest)", df=nonneutral[(nonneutral.away_rest >= 10)], side="away")
ats_spot("Home rest>=10 -> bet HOME (any away rest)", df=nonneutral[(nonneutral.home_rest >= 10)], side="home")
ats_spot("Home on short week (<=5) vs rested opp (>=7) -> bet HOME", df=nonneutral[(nonneutral.home_rest <= 5) & (nonneutral.away_rest >= 7)], side="home")
ats_spot("Away on short week (<=5) vs rested opp (>=7) -> bet AWAY", df=nonneutral[(nonneutral.away_rest <= 5) & (nonneutral.home_rest >= 7)], side="away")
ats_spot("Away more rest by 3+ days -> bet AWAY", df=nonneutral[(nonneutral.away_rest - nonneutral.home_rest) >= 3], side="away")
ats_spot("Home more rest by 3+ days -> bet HOME", df=nonneutral[(nonneutral.home_rest - nonneutral.away_rest) >= 3], side="home")
ats_spot("Home rest 6 (played MNF/Sun late) vs away 7 -> bet AWAY", df=nonneutral[(nonneutral.home_rest == 6) & (nonneutral.away_rest == 7)], side="away")

# early 9:30 ET international kicks (any location)
intl = h[(h.gametime == "09:30") | (h.gametime == "9:30")]
ats_spot("9:30 ET (international) -> bet HOME/designated home", df=intl, side="home")
ats_spot("9:30 ET (international) -> bet AWAY/designated away", df=intl, side="away")
ats_spot("Neutral-site games -> bet designated home", df=h[h.location == "Neutral"], side="home")

# wind / weather (outdoors only, wind recorded)
wind = h[(h.roof.isin(["outdoors"])) & h.wind.notna()]
wind15 = wind[wind.wind >= 15]
wind12 = wind[wind.wind >= 12]
tot_spot("Outdoor wind>=15 -> UNDER", wind15, "under")
tot_spot("Outdoor wind>=12 -> UNDER", wind12, "under")
tot_spot("Outdoor wind>=20 -> UNDER", wind[wind.wind >= 20], "under")
tot_spot("Outdoor wind<=5 -> UNDER (control)", wind[wind.wind <= 5], "under")
ats_spot("Wind>=15: bet home favs -> HOME", df=wind15[wind15.hfav], side="home")
ats_spot("Wind>=15: bet road dogs (underdog)", df=wind15[wind15.hfav], side="away")
ats_spot("Wind>=15: bet home dogs", df=wind15[wind15.afav], side="home")
cold = h[(h.roof == "outdoors") & (h.temp <= 32)]
tot_spot("Outdoor temp<=32F -> UNDER", cold, "under")

# totals level
tot_spot("Total >=50 -> UNDER", h[h.total_line >= 50], "under")
tot_spot("Total >=52 -> UNDER", h[h.total_line >= 52], "under")
tot_spot("Total <=40 -> OVER", h[h.total_line <= 40], "over")
tot_spot("Total <=38 -> OVER", h[h.total_line <= 38], "over")
tot_spot("Total 41-44 -> OVER", h[h.total_line.between(41, 44)], "over")
tot_spot("Domes/closed -> OVER", h[h.roof.isin(["dome", "closed"])], "over")
tot_spot("Week 5 all -> UNDER", h[h.week == 5], "under")
tot_spot("Week 5 all -> OVER", h[h.week == 5], "over")
tot_spot("9:30 ET games -> UNDER", intl, "under")
tot_spot("Both teams rest>=10 -> OVER", h[(h.home_rest >= 10) & (h.away_rest >= 10)], "over")
tot_spot("Short week either side (rest<=5) -> UNDER", h[(h.home_rest <= 5) | (h.away_rest <= 5)], "under")
tot_spot("Spread<=3 and total>=47 -> OVER", h[(h.abs_sp <= 3) & (h.total_line >= 47)], "over")
tot_spot("Spread>=7 -> UNDER", h[h.abs_sp >= 7], "under")
tot_spot("Spread>=7 -> OVER", h[h.abs_sp >= 7], "over")

res = pd.DataFrame(rows)
res["sig_flag"] = np.where((res.n >= 100) & (res.p_two_sided < 0.01), "CANDIDATE", "")
print("\n===== SITUATIONAL TESTS 2015-2025 REG (-110 BE = 52.38%) =====")
print(res.to_string(index=False))
res.to_csv("situational_results.csv", index=False)
print(f"\nNumber of tests: {len(res)}. Bonferroni 5% threshold p<{0.05/len(res):.4f}; expected false positives at p<0.05 ~ {0.05*len(res):.1f}")

# ---------- key numbers: margin distribution and totals distribution ----------
print("\n===== KEY NUMBER ANALYSIS (final margin from favorite perspective; closing spread) =====")
h["fav_margin"] = np.where(h.spread_line >= 0, h.result, -h.result)  # margin from favorite's perspective
h["fav_line"] = h.abs_sp
for L in [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5.5, 6, 6.5, 7, 7.5, 8, 9.5, 10, 10.5, 11, 13.5, 14]:
    d = h[h.fav_line == L]
    if len(d) == 0:
        continue
    fav_cov = (d.fav_margin > L).mean()
    push = (d.fav_margin == L).mean()
    dog_cov = (d.fav_margin < L).mean()
    print(f"line {L:>4}: n={len(d):4d}  fav covers {fav_cov:.3f}  push {push:.3f}  dog covers {dog_cov:.3f}")

print("\nFinal margin frequency (all games 2015-2025, absolute margin):")
am = h.result.abs()
for k in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14]:
    print(f"  |margin|={k:2d}: {(am==k).mean():.4f}")

# prob favorite wins by exactly 3 / 7 conditioned on spread near 3 and 7
for L in [2.5, 3, 3.5, 6.5, 7, 7.5]:
    d = h[h.fav_line == L]
    print(f"  spread {L}: P(fav wins by exactly 3)={(d.fav_margin==3).mean():.3f}  by exactly 7={(d.fav_margin==7).mean():.3f}  n={len(d)}")

# cover prob for dog +2.5 vs +3 vs +3.5 vs fav; implied value of buying the half point
print("\nDog +2.5/+3/+3.5 cover prob (dog win/push/lose), from line sample:")
for L in [2.5, 3, 3.5, 6.5, 7, 7.5]:
    d = h[h.fav_line == L]
    print(f"  fav -{L}: dog cover {(d.fav_margin<L).mean():.3f}, push {(d.fav_margin==L).mean():.3f}")

# totals key numbers
print("\n===== TOTALS: where do final totals land =====")
tt = h.total
for k in [37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51]:
    print(f"  total=={k}: {(tt==k).mean():.4f}")
for L in [40.5, 41, 41.5, 43.5, 44, 44.5, 46.5, 47, 47.5]:
    d = h[h.total_line == L]
    if len(d) == 0:
        continue
    print(f"  total line {L}: n={len(d):4d} over {(d.total>L).mean():.3f} push {(d.total==L).mean():.3f} under {(d.total<L).mean():.3f}")

# ---------- 2026 YTD ----------
y = g[(g.season == 2026) & (g.game_type == "REG") & g.result.notna()].copy()
y["home_cov"] = np.sign(y.result - y.spread_line)
y["over"] = np.sign(y.total - y.total_line)
print("\n===== 2026 YTD (weeks 1-5 played) =====")
print(f"games {len(y)}; home ATS W-L-P {(y.home_cov==1).sum()}-{(y.home_cov==-1).sum()}-{(y.home_cov==0).sum()}; over-under-push {(y.over==1).sum()}-{(y.over==-1).sum()}-{(y.over==0).sum()}")
print(f"home dog ATS: {((y.spread_line<0)&(y.home_cov==1)).sum()}-{((y.spread_line<0)&(y.home_cov==-1)).sum()}")
