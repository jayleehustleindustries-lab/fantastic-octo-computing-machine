"""Grade a night's priced pick'em legs against public box scores. Paper trade only: never touches the ledger.

NFL legs come from nfl_legs.py output (already priced). WNBA lines are re-priced with oklahoma.compare on the
data as it stood BEFORE tip (pre-game parquet), so the grade uses exactly what we knew then. Actuals come from
the refreshed nflverse weekly stats and the refreshed player_games parquet.

card JSON: {"slips": {"A": ["Brock Purdy|pass_yds|LESS", ...]}, "notes": {"Mike Evans": "..."},
            "nfl": {"legs": path, "stats": path, "season": 2026, "week": 6, "teams": ["SF","WAS"], "source": url},
            "wnba": {"lines": path, "pre_games": path, "games": path, "date": "2026-10-19", "team": "ATL",
                     "game_id": 401918306, "source": url}}

usage: python grade.py <oklahoma_dir> <card.json> <out.csv>
"""
import json, sys
import pandas as pd

sys.path.insert(0, sys.argv[1])
from oklahoma import compare as C, project as P  # noqa: E402

NFL_COL = {"pass_yds": "passing_yards", "pass_tds": "passing_tds", "rush_yds": "rushing_yards",
           "rec_yds": "receiving_yards", "receptions": "receptions"}


def result(actual, line, side):
    if pd.isna(actual):
        return "NO_ACTION"
    if actual == line:
        return "PUSH"
    return "HIT" if (actual > line) == (side == "MORE") else "MISS"


def grade_nfl(cfg):
    legs = pd.DataFrame(json.load(open(cfg["legs"])))
    s = pd.read_csv(cfg["stats"], low_memory=False)
    s = s[(s.season == cfg["season"]) & (s.week == cfg["week"]) & s.team.isin(cfg["teams"])]
    rows = []
    for l in legs.itertuples():
        a = s.loc[s.player_display_name == l.player, NFL_COL[l.market]]
        actual = float(a.iloc[0]) if len(a) else float("nan")
        rows.append(dict(sport="NFL", player=l.player, market=l.market, line=l.line, side=l.side, proj=l.proj,
                         p_model=l.p_model, p_blend=l.p, actual=actual, source=cfg["source"]))
    return rows


def grade_wnba(cfg):
    lines = C.read_lines(cfg["lines"])
    pre = pd.read_parquet(cfg["pre_games"])
    schedule = P.load_schedule(int(pre["season"].max()))
    res, info = C.compare(lines, pre, schedule, cfg["date"], cfg["team"], payout=6.0, legs=3)
    post = pd.read_parquet(cfg["games"])
    box = post[post.game_id == cfg["game_id"]].set_index("athlete_display_name")
    rows = []
    for r in res.itertuples():
        actual = float(box.loc[r.player, r.market]) if r.player in box.index else float("nan")
        rows.append(dict(sport="WNBA", player=r.player, market=r.market, line=r.line, side=r.side,
                         proj=round(float(r.mean), 1), p_model=round(float(r.p_side), 4),
                         p_blend=round(float(r.p_blend), 4), actual=actual, source=cfg["source"]))
    print(f"WNBA priced on data through {info['data_cutoff']} (pre-game)")
    return rows


if __name__ == "__main__":
    card = json.load(open(sys.argv[2]))
    df = pd.DataFrame(grade_nfl(card["nfl"]) + grade_wnba(card["wnba"]))
    df["result"] = [result(a, l, s) for a, l, s in zip(df.actual, df.line, df.side)]
    key = df.player + "|" + df.market + "|" + df.side
    df["slip"] = [",".join(s for s, ks in card["slips"].items() if k in ks) for k in key]
    df["note"] = df.player.map(card.get("notes", {})).fillna("")
    df.to_csv(sys.argv[3], index=False)
    pd.set_option("display.width", 200)
    print(df.drop(columns="source").to_string(index=False))
    for s, ks in card["slips"].items():
        g = df[df.slip.str.split(",").apply(lambda v: s in v)]
        print(f"slip {s}: {'WON' if (g.result == 'HIT').all() and len(g) == len(ks) else 'LOST'} "
              f"({(g.result == 'HIT').sum()}/{len(ks)} legs hit)")
    bet = df[df.p_blend > 0.5]
    print(f"model-side legs (p_blend>0.5): {(bet.result == 'HIT').sum()}/{len(bet)} hit, "
          f"mean p_blend {bet.p_blend.mean():.3f}")
