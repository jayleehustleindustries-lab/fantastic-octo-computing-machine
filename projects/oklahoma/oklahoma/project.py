"""Project an upcoming slate: each player's full distribution for every market.

Trains a model (default context_glm_plus2si, pick another with --model) on the most
recent seasons (all games played so far), then scores the scheduled games. Tonight's
roster defaults to each team's most recent game; pass --out for players listed out on
the official injury report.

Output is a projection, not a bet. There is no sportsbook line here: "fair_line"
is the model's own 50/50 line. An edge only exists where a book's line differs
from it by more than the vig, and that has not been shown to be profitable yet.
"""
from __future__ import annotations

import argparse

import numpy as np
import pandas as pd
from scipy import stats

from oklahoma import calibrate, ingest
from oklahoma.features import STATS, build_features
from oklahoma.models import PRODUCTION_MODEL, Model, prob_over, registry

DEFAULT_MODEL = PRODUCTION_MODEL
SCHED_URL = (
    "https://github.com/sportsdataverse/sportsdataverse-data/releases/download/"
    "espn_wnba_schedules/wnba_schedule_{season}.csv"
)
SLATE_FLAG = "_slate"
# Player box-score counts a not-yet-played row carries as 0.0. They are never read for the row's own
# features (every feature shifts by one game), but features that subtract the row's own value from a
# running sum (3P%, career 3PA/game) turn NaN if the column is missing. team_score / opponent_team_score
# are deliberately left unset: a 0-0 "final" would drag the league pace average, and no slate-row
# feature reads them.
ZERO_BOX_COLS = [
    "minutes", "offensive_rebounds", "defensive_rebounds", "rebounds", "points", "assists", "pra",
    "field_goals_attempted", "free_throws_attempted", "turnovers", "threes_made", "threes_attempted",
]


def get_model(name: str = DEFAULT_MODEL) -> type[Model]:
    """Model class by registry name (models.registry())."""
    reg = registry()
    if name not in reg:
        raise SystemExit(f"unknown model {name!r}; choose from {sorted(reg)}")
    return reg[name]


def load_schedule(season: int) -> pd.DataFrame:
    """The season's full schedule/results table (one row per game)."""
    return pd.read_csv(SCHED_URL.format(season=season), low_memory=False)


def load_slate(date: str, season: int, schedule: pd.DataFrame | None = None) -> pd.DataFrame:
    """Scheduled games on a local (US) game date, both teams known. Pass `schedule` to skip the download."""
    s = load_schedule(season) if schedule is None else schedule
    s = s[(s["game_date"] == date) & ~s["home_abbreviation"].isin(["TBD"]) & ~s["away_abbreviation"].isin(["TBD"])]
    return pd.DataFrame({
        "game_id": s["game_id"].astype("int64"),
        "tip": pd.to_datetime(s["date"], utc=True),
        "season": season,
        "season_type": s["season_type"].astype(int),
        "home": s["home_abbreviation"],
        "away": s["away_abbreviation"],
        "label": s["notes_headline"].fillna(""),
    }).reset_index(drop=True)


def placeholder_rows(games: pd.DataFrame, slate: pd.DataFrame, out: set[str],
                     add: set[str] = frozenset()) -> pd.DataFrame:
    """One row per expected player per slate game. Box-score columns are zero and
    never read: every feature uses only games before the row's tip. `starter` carries the
    player's last-game flag (the pregame-known stand-in; features.starter_prev agrees)."""
    rows = []
    for _, sg in slate.iterrows():
        sides = {}
        for abbr in (sg["home"], sg["away"]):
            team = games[(games["team_abbreviation"] == abbr) & (games["season"] == sg["season"])]
            last = team[team["tip"] == team["tip"].max()]
            # Players who sat the last game but are expected back (per the injury report).
            back = team[team["athlete_display_name"].str.lower().isin(add)
                        & ~team["athlete_id"].isin(last["athlete_id"])]
            back = back.sort_values("tip").drop_duplicates("athlete_id", keep="last")
            sides[abbr] = pd.concat([last, back], ignore_index=True)
        for abbr, opp in ((sg["home"], sg["away"]), (sg["away"], sg["home"])):
            last, opp_last = sides[abbr], sides[opp]
            for _, p in last.iterrows():
                if p["athlete_display_name"].lower() in out:
                    continue
                rows.append({
                    "game_id": sg["game_id"], "season": sg["season"], "season_type": sg["season_type"],
                    "tip": sg["tip"], "athlete_id": p["athlete_id"],
                    "athlete_display_name": p["athlete_display_name"],
                    "athlete_position_abbreviation": p["athlete_position_abbreviation"],
                    "team_id": p["team_id"], "team_abbreviation": abbr,
                    "opponent_team_id": opp_last["team_id"].iloc[0], "opponent_team_abbreviation": opp,
                    "is_home": abbr == sg["home"], "playoffs": sg["season_type"] == ingest.PLAYOFFS,
                    "starter": bool(p["starter"]), **{c: 0.0 for c in ZERO_BOX_COLS},
                    SLATE_FLAG: True,
                })
    return pd.DataFrame(rows)


def fair_line(mu: float, alpha: float) -> tuple[float, float]:
    """The x.5 line closest to a 50/50 split, and P(over) at it."""
    lines = np.arange(0, int(mu * 3) + 10) + 0.5
    p = prob_over(lines, np.full(len(lines), mu), alpha)
    i = int(np.argmin(np.abs(p - 0.5)))
    return float(lines[i]), float(p[i])


def quantile(q: float, mu: float, alpha: float) -> float:
    if alpha <= 1e-8:
        return float(stats.poisson.ppf(q, mu))
    n = 1 / alpha
    return float(stats.nbinom.ppf(q, n, n / (n + mu)))


def prepare(games: pd.DataFrame, slate: pd.DataFrame, out: set[str], add: set[str] = frozenset(),
            train_window: int = 5, min_prior_games: int = 5) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Features for history plus the slate's placeholder rows -> (train, target).

    train: games before the slate, last `train_window` seasons, players with >= `min_prior_games`.
    target: one row per expected slate player (index reset), every feature built from prior games only."""
    season = int(slate["season"].iloc[0])
    played = set(slate["game_id"]) & set(games["game_id"])
    if played:
        raise SystemExit(f"game(s) {sorted(played)} are already in the data; projecting is for games not yet played")
    ph = placeholder_rows(games, slate, out, add)
    if ph.empty:
        raise SystemExit("no roster found for the slate teams this season")
    unknown = add - set(ph["athlete_display_name"].str.lower())
    if unknown:
        raise SystemExit(f"--add names not found on a slate team this season: {sorted(unknown)}")
    feats = build_features(pd.concat([games.assign(**{SLATE_FLAG: False}), ph], ignore_index=True))
    is_slate = feats[SLATE_FLAG].astype(bool)

    hist = feats[~is_slate]
    train = hist[(hist["season"] > season - train_window) & (hist["career_games"] >= min_prior_games)]
    return train, feats[is_slate].copy().reset_index(drop=True)


def fit_markets(train: pd.DataFrame, target: pd.DataFrame,
                model_cls: type[Model]) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    """Fit one model per market on `train`; return {market: (mu, alpha)}, unrounded, aligned to `target` rows."""
    fits = {}
    for market in STATS:
        model = model_cls(market).fit(train)
        mu = model.predict_mean(target)
        fits[market] = (mu, model.alpha_for(mu))
    return fits


def project(date: str, out: set[str], add: set[str] = frozenset(),
            train_window: int = 5, min_prior_games: int = 5,
            model: str = DEFAULT_MODEL) -> tuple[pd.DataFrame, pd.DataFrame]:
    games = pd.read_parquet(ingest.GAMES_PATH)
    season = int(games["season"].max())
    slate = load_slate(date, season)
    if slate.empty:
        raise SystemExit(f"no scheduled games with known teams on {date}")
    data_cutoff = games["tip"].max().isoformat()
    train, target = prepare(games, slate, out, add, train_window, min_prior_games)
    fits = fit_markets(train, target, get_model(model))

    out_rows = []
    for market, (mus, alphas) in fits.items():
        for (_, r), m, a in zip(target.iterrows(), mus, alphas):
            line, p = fair_line(m, a)
            out_rows.append({
                "game": f"{r['team_abbreviation']} vs {r['opponent_team_abbreviation']}",
                "player": r["athlete_display_name"], "pos": r["athlete_position_abbreviation"],
                "market": market, "mu": float(m), "alpha": float(a),
                "projection": round(m, 1), "fair_line": line,
                "p_over_fair": round(p, 3),
                "p10": quantile(0.10, m, a), "p90": quantile(0.90, m, a),
                "recent_min": round(r["min_ewm"], 1), "teammates_out_min": round(r["out_minutes"], 1),
                "returning": bool(r["returning"]), "games_of_history": int(r["career_games"]),
                "model": model, "data_cutoff": data_cutoff,
            })
    res = pd.DataFrame(out_rows)
    cal, apply_to = calibrate.load(), calibrate.effective_apply_to()      # the file's own market list, if it has one
    res["p_over_cal"] = [round(float(calibrate.calibrate(p, m, cal, apply_to)), 3)
                         for p, m in zip(res["p_over_fair"], res["market"])]
    res["low_history"] = res["games_of_history"] < min_prior_games
    return slate, res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="local game date, e.g. 2026-10-04")
    ap.add_argument("--out", default="", help="comma-separated player names ruled out")
    ap.add_argument("--add", default="", help="comma-separated players who sat the last game but will play")
    ap.add_argument("--model", default=DEFAULT_MODEL, help=f"model name from models.registry() (default {DEFAULT_MODEL})")
    args = ap.parse_args()
    names = lambda s: {n.strip().lower() for n in s.split(",") if n.strip()}

    slate, res = project(args.date, names(args.out), names(args.add), model=args.model)
    ingest.ROOT.joinpath("reports").mkdir(exist_ok=True)
    path = ingest.ROOT / "reports" / f"slate_{args.date}.csv"
    res.to_csv(path, index=False)
    print(slate[["game_id", "tip", "home", "away", "label"]].to_string(index=False), "\n")
    print(f"model {args.model} | data through {res['data_cutoff'].iloc[0]}\n")
    wide = res.pivot_table(index=["game", "player", "pos", "recent_min"], columns="market",
                           values="projection").reset_index()
    print(wide.sort_values(["game", "recent_min"], ascending=[True, False]).to_string(index=False))
    print(f"\nfull table (fair lines, p10/p90) -> {path}")


if __name__ == "__main__":
    main()
