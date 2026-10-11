"""Download free WNBA player box scores and build a clean player-game table.

Source: sportsdataverse (wehoop) mirror of ESPN box scores, one parquet file per
season, hosted as GitHub release assets. No API key, no scraping.
"""
from __future__ import annotations

import argparse
import pathlib

import pandas as pd
import requests

URL = (
    "https://github.com/sportsdataverse/sportsdataverse-data/releases/download/"
    "espn_wnba_player_boxscores/player_box_{season}.parquet"
)
ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
GAMES_PATH = ROOT / "data" / "player_games.parquet"

REGULAR, PLAYOFFS = 2, 3
MIN_FRANCHISE_GAMES = 15   # All-Star / exhibition sides (ALL, EAST, USA, ...) play 1-2 games

COLUMNS = [
    "game_id", "season", "season_type", "tip", "athlete_id", "athlete_display_name",
    "athlete_position_abbreviation", "team_id", "team_abbreviation", "opponent_team_id",
    "opponent_team_abbreviation", "is_home", "playoffs", "starter", "minutes",
    "offensive_rebounds", "defensive_rebounds", "rebounds", "points", "assists", "pra",
    "field_goals_attempted", "free_throws_attempted", "turnovers", "team_score", "opponent_team_score",
    "threes_made", "threes_attempted",
]


def parse_seasons(spec: str) -> list[int]:
    """'2015-2026' or '2024,2026' -> list of ints."""
    out: list[int] = []
    for part in spec.split(","):
        if "-" in part:
            lo, hi = part.split("-")
            out.extend(range(int(lo), int(hi) + 1))
        else:
            out.append(int(part))
    return sorted(set(out))


def download(season: int, force: bool = False) -> pathlib.Path:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / f"player_box_{season}.parquet"
    if path.exists() and not force:
        return path
    resp = requests.get(URL.format(season=season), timeout=60)
    resp.raise_for_status()
    path.write_bytes(resp.content)
    return path


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    """Keep regular season + playoff games a player actually played in."""
    d = raw[raw["season_type"].isin([REGULAR, PLAYOFFS])].copy()
    played = ~d["did_not_play"].fillna(False).astype(bool) & (d["minutes"].fillna(0) > 0)
    d = d[played & d[["rebounds", "points", "assists"]].notna().all(axis=1)]
    # Drop All-Star and exhibition games: keep only games between real franchises.
    games_per_team = d.groupby(["season", "team_id"])["game_id"].nunique()
    franchises = set(games_per_team[games_per_team >= MIN_FRANCHISE_GAMES].index)
    is_franchise = lambda col: pd.Series(list(zip(d["season"], d[col])), index=d.index).isin(franchises)
    d = d[is_franchise("team_id") & is_franchise("opponent_team_id")]
    d["tip"] = pd.to_datetime(d["game_date_time"], utc=True)
    d["is_home"] = d["home_away"].eq("home")
    d["playoffs"] = d["season_type"].eq(PLAYOFFS)
    d["starter"] = d["starter"].fillna(False).astype(bool)
    for col in ["minutes", "offensive_rebounds", "defensive_rebounds", "rebounds", "points", "assists",
                "field_goals_attempted", "free_throws_attempted", "turnovers",
                "team_score", "opponent_team_score"]:
        d[col] = d[col].astype(float)
    d["pra"] = d["points"] + d["rebounds"] + d["assists"]
    d["threes_made"] = d["three_point_field_goals_made"].astype(float) if "three_point_field_goals_made" in d else float("nan")
    d["threes_attempted"] = d["three_point_field_goals_attempted"].astype(float) if "three_point_field_goals_attempted" in d else float("nan")
    d = d.drop_duplicates(["game_id", "athlete_id"])
    return d[COLUMNS].sort_values(["tip", "game_id", "athlete_id"]).reset_index(drop=True)


def build(seasons: list[int], force: bool = False) -> pd.DataFrame:
    raw = pd.concat([pd.read_parquet(download(s, force)) for s in seasons], ignore_index=True)
    games = clean(raw)
    GAMES_PATH.parent.mkdir(parents=True, exist_ok=True)
    if GAMES_PATH.exists():
        # A partial refresh (e.g. --seasons 2026) must never drop the other seasons.
        old = pd.read_parquet(GAMES_PATH)
        keep = old[~old["season"].isin(games["season"].unique())]
        if len(keep):
            games = pd.concat([keep.reindex(columns=COLUMNS), games], ignore_index=True)
            games = games.sort_values(["tip", "game_id", "athlete_id"]).reset_index(drop=True)
    games.to_parquet(GAMES_PATH, index=False)
    return games


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seasons", default="2015-2026")
    ap.add_argument("--force", action="store_true", help="re-download files already on disk")
    args = ap.parse_args()
    games = build(parse_seasons(args.seasons), args.force)
    summary = games.groupby("season").agg(rows=("game_id", "size"), games=("game_id", "nunique"))
    print(summary.to_string())
    print(f"wrote {len(games):,} player-games -> {GAMES_PATH}")


if __name__ == "__main__":
    main()
