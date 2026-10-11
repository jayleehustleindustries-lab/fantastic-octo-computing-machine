"""Line comparison for pick'em slips: the model's side, probability and edge for every line you give it.

    python -m oklahoma.compare --date 2026-10-09 --team NY --lines lines.csv [--out "A,B"] [--add "C"]
        [--payout 3 --legs 2] [--model context_glm_plus2si] [--no-role-bias] [--log scratch.csv]

lines.csv columns: player, market (points, rebounds, assists, pra, pr, pa, ra), line, and an
optional side (MORE / LESS). `mkt` is accepted as an alias of `market`. --team picks the game
(either team in it); lines for players on both teams of that game are matched.

Method (productized from the ad hoc tonight.py / thresholds.py):
  * Each player's points, rebounds, assists and PRA come from the chosen model (mean mu) with a
    negative-binomial spread (alpha_for(mu)). PRA uses its own model; P+R, P+A and R+A add
    independent points/rebounds/assists draws.
  * 40,000 draws per player from a fixed seed. Draws are inverse-CDF samples of per-player uniforms,
    so every row of the same player shares the same random numbers (common random numbers): two
    lines on one player are priced off the same simulated games, and re-running gives identical output.
  * P(over), P(push), P(under) come from the same draws, so they sum to 1; push is nonzero only
    for whole-number lines.
  * Calibrated P(more)/P(less): the over/under split among non-push outcomes goes through
    calibrate.calibrate (single markets listed in the calibration file's own _meta.apply_to, else
    calibrate.APPLY_TO) or, for combos, 0.5 + 0.85*(p-0.5) (flag COMBO_UNCALIBRATED: no fitted map
    exists). Push mass is carried unchanged.
  * break-even = payout ** (-1 / legs) (3x for 2 legs: 0.5774; 6x for 3 legs: 0.5503). edge =
    P(win) of the evaluated side minus break-even. A push is counted as not winning, which is
    conservative; the book's push rule decides the true value.
  * Playoff role bias (on by default in playoff games for context_glm_plus2 ONLY; --no-role-bias turns it
    off): see ROLE_BIAS. It is switched off automatically for a model whose design already has starter_prev
    terms (context_glm_plus2si, the default, and plus2s): those fit the starter/bench playoff effect
    themselves, so the shift would count it twice. Applied to the mean of each component's distribution, so
    draws stay whole numbers and a whole-number line keeps its push probability.

Flags (space separated in the `flags` column):
  STALE               the data lacks a completed game the schedule shows for either team: every row is marked
  LOW_HISTORY         fewer than 5 prior career games (outside the model's training population)
  PLAYOFF_BENCH_MORE  playoff game, did not start her previous game, evaluated side is MORE
  BIG_DISAGREEMENT    |line - model mean| > 1 sd: the book probably knows something the model does not
  SAME_PLAYER         more than one input row for this player (the legs are correlated; do not stack them)
  COMBO_UNCALIBRATED  P+R / P+A / R+A: no fitted calibration, 0.85 shrink toward 50% instead
  UNCALIBRATED        single market the calibration file does not list in apply_to (today: all but points), probabilities are the raw model's
  MINUTES_DIFF        |median of a quantile-GBM minutes model (oklahoma.minutes, fit on the same training
                      window) - her recent minutes (min_ewm)| >= 3: the projection assumes her usual workload and
                      the minutes model disagrees. A flag only, never a model input.
  NOT_ON_ROSTER       name not on tonight's projected roster (sat the last game? use --add; or --out removed her)

Every input row (not just picks) is appended to data/line_log.csv (or --log PATH), so model-vs-line history
builds up for later grading. Nothing here places a bet, and no edge over a real book is demonstrated yet.
"""
from __future__ import annotations

import argparse
import datetime as dt
import pathlib
import re
import unicodedata

import numpy as np
import pandas as pd
from scipy import stats

from oklahoma import calibrate, ingest, project as P
from oklahoma.features import STATS
from oklahoma.minutes import MinutesModel
from oklahoma.models import MU_FLOOR

N_SIMS = 40_000
SEED = 7
COMBO_SHRINK = 0.85          # fitted single-market calibration slopes are 0.82-0.89
MIN_HISTORY = 5              # prior career games below this: outside the training distribution
MINUTES_DIFF_MIN = 3.0       # |minutes-model median - min_ewm| at or above this raises MINUTES_DIFF
LOG_PATH = ingest.ROOT / "data" / "line_log.csv"
REPORTS = ingest.ROOT / "reports"

MARKETS = {
    "points": ("points",), "rebounds": ("rebounds",), "assists": ("assists",), "pra": ("pra",),
    "pr": ("points", "rebounds"), "pa": ("points", "assists"), "ra": ("rebounds", "assists"),
}
COMBOS = ("pr", "pa", "ra")
ALIASES = {
    "pts": "points", "point": "points", "reb": "rebounds", "rebs": "rebounds", "rebound": "rebounds",
    "ast": "assists", "asts": "assists", "assist": "assists",
    "p+r": "pr", "pts+reb": "pr", "points+rebounds": "pr", "p+a": "pa", "pts+ast": "pa", "points+assists": "pa",
    "r+a": "ra", "reb+ast": "ra", "rebounds+assists": "ra", "p+r+a": "pra", "pts+reb+ast": "pra",
}
SIDES = {"more": "MORE", "over": "MORE", "higher": "MORE", "less": "LESS", "under": "LESS", "lower": "LESS"}

# Playoff role bias: mean residual (actual - projected) of the production model in playoff games,
# walk-forward 2021-26 (each season projected from earlier seasons only), grouped by whether the
# player started her PREVIOUS game. Starters are under-projected, bench players over-projected.
# Values carried over from the ad hoc tonight.py; not re-derived here. PRA is the sum of the three
# components (0.77+0.32+0.11 = 1.20; -0.94-0.43-0.29 = -1.66). Keys: True = started previous game.
# They are plus2's residuals, so they are only valid for plus2 (ROLE_BIAS_MODEL): see role_bias_status.
# The shift moves each component's MEAN. (tonight.py added it to every draw; with whole-number draws
# that rounds the shift, so a +0.43 never moved a .5 line, and it left no push on whole-number lines.)
ROLE_BIAS = {
    True: {"points": 0.77, "rebounds": 0.32, "assists": 0.11, "pra": 1.20},
    False: {"points": -0.94, "rebounds": -0.43, "assists": -0.29, "pra": -1.66},
}

ROLE_BIAS_MODEL = "context_glm_plus2"

LOG_COLS = ["timestamp_utc", "date", "team", "player", "athlete_id", "game_id", "market", "line",
            "model", "data_cutoff", "p_more_cal", "p_push", "flags"]
RESULT_COLS = ["player", "team", "opp", "athlete_id", "game_id", "market", "line", "side", "rec_side", "role",
               "mean", "mean_raw", "role_shift", "sd", "p_over", "p_push", "p_under", "p_more_cal", "p_less_cal",
               "p_side", "break_even", "edge", "recent_min", "min_p50", "career_games", "flags"]


# ---------- input ----------

def normalize_name(name: str) -> str:
    """Lowercase ASCII with punctuation dropped: "A'ja Wilson" == "Aja Wilson", "Parker-Tyus" == "Parker Tyus"."""
    s = unicodedata.normalize("NFKD", str(name))
    s = "".join(ch for ch in s if not unicodedata.combining(ch)).lower()
    s = re.sub(r"[’'`.]", "", s)
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def normalize_market(raw: str) -> str:
    key = re.sub(r"\s+", "", str(raw).strip().lower())
    key = ALIASES.get(key, key)
    if key not in MARKETS:
        raise SystemExit(f"unknown market {raw!r}; use one of {sorted(MARKETS)}")
    return key


def read_lines(path) -> pd.DataFrame:
    """lines.csv -> columns player, market, line, side (side is None where not given)."""
    df = pd.read_csv(path)
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "market" not in df and "mkt" in df:
        df = df.rename(columns={"mkt": "market"})
    missing = {"player", "market", "line"} - set(df.columns)
    if missing:
        raise SystemExit(f"{path}: missing column(s) {sorted(missing)}; need player, market, line")
    out = pd.DataFrame({
        "player": df["player"].astype(str).str.strip(),
        "market": df["market"].map(normalize_market),
        "line": pd.to_numeric(df["line"], errors="raise").astype(float),
    })
    if "side" in df:
        def side(v):
            if pd.isna(v) or not str(v).strip():
                return None
            if str(v).strip().lower() not in SIDES:
                raise SystemExit(f"unknown side {v!r}; use MORE or LESS")
            return SIDES[str(v).strip().lower()]
        out["side"] = df["side"].map(side).astype(object)
        out["side"] = out["side"].where(out["side"].notna(), None)
    else:
        out["side"] = None
    return out.reset_index(drop=True)


# ---------- simulation ----------

def break_even(payout: float, legs: int) -> float:
    """Win probability per leg at which a pick'em slip paying `payout`x for `legs` legs breaks even."""
    return float(payout) ** (-1.0 / legs)


def sample_counts(u: np.ndarray, mu: float, alpha: float) -> np.ndarray:
    """Inverse-CDF draws from NB(mu, alpha) (Poisson when alpha ~ 0) for uniforms `u`.

    The same u with a larger mu gives a larger count, which is what makes draws common random numbers."""
    if alpha <= 1e-8:
        dist = stats.poisson(mu)
    else:
        n = 1.0 / alpha
        dist = stats.nbinom(n, n / (n + mu))
    top = int(dist.ppf(1 - 1e-9)) + 2
    cdf = dist.cdf(np.arange(top + 1))
    return np.minimum(np.searchsorted(cdf, u, side="left"), top).astype(np.int32)


def simulate_player(athlete_id: int, mu: dict[str, float], alpha: dict[str, float],
                    n_sims: int = N_SIMS, seed: int = SEED) -> dict[str, np.ndarray]:
    """Draws for each stat. Uniforms depend only on (seed, athlete_id), never on other players or lines."""
    u = np.random.default_rng([int(seed), int(athlete_id)]).random((len(STATS), n_sims))
    return {s: sample_counts(u[i], mu[s], alpha[s]) for i, s in enumerate(STATS)}


# ---------- role bias ----------

def role_bias_status(model: str) -> tuple[bool, str]:
    """(may the ROLE_BIAS shift be used with `model`, why not). The shift was measured on plus2's playoff
    residuals. A model with starter_prev terms has already absorbed that effect (the shift would count it
    twice), and any other model was never measured against these numbers."""
    if P.get_model(model).has_starter_terms:
        return False, f"{model} already models the previous-game starter role (starter_prev terms); the shift would count it twice"
    if model != ROLE_BIAS_MODEL:
        return False, f"the shift was measured on {ROLE_BIAS_MODEL} only"
    return True, ""


# ---------- staleness ----------

def staleness(games: pd.DataFrame, schedule: pd.DataFrame, teams, before_tip) -> dict[str, str]:
    """{team: message} for each team whose latest completed schedule game (before `before_tip`) is missing
    from the data. Empty dict = data is current. Compared by game id; dates are for the message."""
    done = schedule[schedule["status_type_completed"].fillna(False).astype(bool)
                    & schedule["season_type"].isin([ingest.REGULAR, ingest.PLAYOFFS])].copy()
    done["tip"] = pd.to_datetime(done["date"], utc=True)
    done = done[done["tip"] < before_tip]
    stale = {}
    for abbr in teams:
        mine = done[(done["home_abbreviation"] == abbr) | (done["away_abbreviation"] == abbr)]
        if mine.empty:
            continue
        last = mine.loc[mine["tip"].idxmax()]
        have = games[games["team_abbreviation"] == abbr]
        if int(last["game_id"]) not in set(have["game_id"]):
            seen = have["tip"].max()
            in_data = f"latest game in data is {seen:%Y-%m-%d %H:%M}Z" if pd.notna(seen) else "no games in data"
            stale[abbr] = f"{abbr}: {in_data}, but the schedule shows game {int(last['game_id'])} completed {last['tip']:%Y-%m-%d %H:%M}Z"
    return stale


# ---------- evaluation ----------

def started_previous(target: pd.DataFrame) -> pd.Series:
    """Started her previous game? features.starter_prev if present, else the roster's last-game starter flag."""
    last = target["starter"].astype(bool)
    if "starter_prev" not in target:
        return last
    prev = target["starter_prev"]
    return prev.where(prev.notna(), last).astype(bool)


def evaluate(lines: pd.DataFrame, target: pd.DataFrame, fits: dict[str, tuple[np.ndarray, np.ndarray]], *,
             playoffs: bool, role_bias: bool = True, payout: float = 3.0, legs: int = 2, stale: bool = False,
             n_sims: int = N_SIMS, seed: int = SEED, cal_params: dict | None = None, cal_apply_to=None,
             min_p50: np.ndarray | None = None) -> pd.DataFrame:
    """One result row per input line. `fits` = {stat: (mu, alpha)} arrays aligned to `target` rows.

    `role_bias` is taken as given (compare() has already checked role_bias_status). `cal_params` replaces the
    production calibration file (with `cal_apply_to` as its market list, default calibrate.APPLY_TO).
    `min_p50` = minutes-model medians aligned to `target`; None skips MINUTES_DIFF."""
    if cal_params is None:
        cal, cal_apply = calibrate.load(), calibrate.effective_apply_to()
    else:
        cal, cal_apply = cal_params, calibrate.APPLY_TO if cal_apply_to is None else cal_apply_to
    be = break_even(payout, legs)
    lines, target = lines.reset_index(drop=True), target.reset_index(drop=True)
    started = started_previous(target)
    apply_bias = bool(role_bias and playoffs)
    roster = {}
    for i, name in enumerate(target["athlete_display_name"]):
        roster.setdefault(normalize_name(name), i)
    keys = lines["player"].map(normalize_name)
    n_rows = keys.map(keys.value_counts())                              # rows per player, for SAME_PLAYER
    game_id = target["game_id"].iloc[0] if len(target) else np.nan

    draws: dict[int, dict[str, np.ndarray]] = {}
    mus: dict[int, dict[str, float]] = {}
    rows = []
    for k, L in lines.iterrows():
        flags = ["STALE"] if stale else []
        if n_rows.iloc[k] > 1:
            flags.append("SAME_PLAYER")
        i = roster.get(normalize_name(L["player"]))
        if i is None:
            rows.append({"player": L["player"], "game_id": game_id, "market": L["market"], "line": L["line"],
                         "side": L["side"], "flags": " ".join(flags + ["NOT_ON_ROSTER"])})
            continue
        r = target.iloc[i]
        aid = int(r["athlete_id"])
        shift = ROLE_BIAS[bool(started.iloc[i])] if apply_bias else dict.fromkeys(STATS, 0.0)
        if aid not in draws:
            raw = {s: float(fits[s][0][i]) for s in STATS}
            mus[aid] = {s: max(raw[s] + shift[s], MU_FLOOR) for s in STATS}
            draws[aid] = simulate_player(aid, mus[aid], {s: float(fits[s][1][i]) for s in STATS}, n_sims, seed)
        comps = MARKETS[L["market"]]
        s = sum(draws[aid][c] for c in comps)
        mean = sum(mus[aid][c] for c in comps)
        mean_raw = sum(float(fits[c][0][i]) for c in comps)
        sd = float(s.std())
        over, push, under = float((s > L["line"]).mean()), float((s == L["line"]).mean()), float((s < L["line"]).mean())

        q = over / (over + under) if over + under > 0 else 0.5          # P(more | not a push)
        if L["market"] in COMBOS:
            q_cal = 0.5 + COMBO_SHRINK * (q - 0.5)
            flags.append("COMBO_UNCALIBRATED")
        else:
            q_cal = float(calibrate.calibrate(q, L["market"], cal, cal_apply))
            if L["market"] not in cal_apply or L["market"] not in cal:
                flags.append("UNCALIBRATED")
        p_more, p_less = (1 - push) * q_cal, (1 - push) * (1 - q_cal)
        rec = "MORE" if p_more >= p_less else "LESS"
        side = L["side"] if isinstance(L["side"], str) else rec        # the caller's side, else the model's
        p_side = p_more if side == "MORE" else p_less

        if int(r["career_games"]) < MIN_HISTORY:
            flags.append("LOW_HISTORY")
        if playoffs and not started.iloc[i] and side == "MORE":
            flags.append("PLAYOFF_BENCH_MORE")
        if abs(L["line"] - mean) > sd:
            flags.append("BIG_DISAGREEMENT")
        recent = float(r["min_ewm"])
        m50 = np.nan if min_p50 is None else float(min_p50[i])
        if abs(m50 - recent) >= MINUTES_DIFF_MIN:                      # NaN on either side compares False
            flags.append("MINUTES_DIFF")
        rows.append({
            "player": r["athlete_display_name"], "team": r["team_abbreviation"], "opp": r["opponent_team_abbreviation"],
            "athlete_id": aid, "game_id": r["game_id"], "market": L["market"], "line": L["line"],
            "side": side, "rec_side": rec, "role": "S" if started.iloc[i] else "B",
            "mean": mean, "mean_raw": mean_raw, "role_shift": mean - mean_raw, "sd": sd,
            "p_over": over, "p_push": push, "p_under": under, "p_more_cal": p_more, "p_less_cal": p_less,
            "p_side": p_side, "break_even": be, "edge": p_side - be,
            "recent_min": recent, "min_p50": m50, "career_games": int(r["career_games"]), "flags": " ".join(flags),
        })
    res = pd.DataFrame(rows).reindex(columns=RESULT_COLS)
    res["athlete_id"] = res["athlete_id"].astype("Int64")               # blank, not 1234.0, for unmatched rows
    return res


def compare(lines: pd.DataFrame, games: pd.DataFrame, schedule: pd.DataFrame, date: str, team: str, *,
            out=frozenset(), add=frozenset(), model: str = P.DEFAULT_MODEL, role_bias: bool = True,
            payout: float = 3.0, legs: int = 2, n_sims: int = N_SIMS, seed: int = SEED,
            train_window: int = 5, min_prior_games: int = 5,
            cal_params: dict | None = None, cal_apply_to=None, minutes_iter: int = 250,
            minutes_flag: bool = True) -> tuple[pd.DataFrame, dict]:
    """Project the game `team` plays on `date` from `games`, then price every line. -> (rows, info).

    `role_bias` is a request: it only takes effect in a playoff game with a model role_bias_status allows.
    MINUTES_DIFF comes from a MinutesModel (`minutes_iter` boosting rounds) fit on the same training window."""
    season = int(games["season"].max())
    slate = P.load_slate(date, season, schedule)
    slate = slate[(slate["home"] == team) | (slate["away"] == team)].reset_index(drop=True)
    if slate.empty:
        raise SystemExit(f"{team} has no scheduled game with known teams on {date}")
    game = slate.iloc[0]
    lower = lambda names: {str(n).strip().lower() for n in names}
    train, target = P.prepare(games, slate, lower(out), lower(add), train_window, min_prior_games)
    fits = P.fit_markets(train, target, P.get_model(model))
    min_p50 = MinutesModel(max_iter=minutes_iter).fit(train).predict(target)["min_p50"].to_numpy() if minutes_flag else None
    stale = staleness(games, schedule, [game["home"], game["away"]], game["tip"])
    playoffs = int(game["season_type"]) == ingest.PLAYOFFS
    allowed, why = role_bias_status(model)
    use_bias = bool(role_bias and allowed and playoffs)
    note = ("off: --no-role-bias" if not role_bias else f"off: {why}" if not allowed else
            "off: not a playoff game" if not playoffs else
            f"ON: shifts each mean by previous-game starter ({ROLE_BIAS_MODEL} only)")
    res = evaluate(lines, target, fits, playoffs=playoffs, role_bias=use_bias, payout=payout, legs=legs,
                   stale=bool(stale), n_sims=n_sims, seed=seed, cal_params=cal_params, cal_apply_to=cal_apply_to,
                   min_p50=min_p50)
    info = {"game": game, "playoffs": playoffs, "role_bias": use_bias, "role_bias_note": note, "stale": stale,
            "model": model, "data_cutoff": games["tip"].max().isoformat(), "break_even": break_even(payout, legs),
            "n_sims": n_sims, "seed": seed}
    return res, info


# ---------- output ----------

def append_log(res: pd.DataFrame, *, date: str, model: str, data_cutoff: str, path=None, now=None) -> int:
    """Append every result row (picks or not) to the line log (default LOG_PATH); header written once.
    Returns rows written."""
    path = pathlib.Path(LOG_PATH if path is None else path)
    path.parent.mkdir(parents=True, exist_ok=True)
    stamp = (now or dt.datetime.now(dt.timezone.utc)).isoformat(timespec="seconds")
    log = pd.DataFrame({
        "timestamp_utc": stamp, "date": date, "team": res["team"], "player": res["player"],
        "athlete_id": res["athlete_id"], "game_id": res["game_id"], "market": res["market"], "line": res["line"],
        "model": model, "data_cutoff": data_cutoff, "p_more_cal": res["p_more_cal"], "p_push": res["p_push"],
        "flags": res["flags"],
    })[LOG_COLS]
    fresh = not path.exists() or path.stat().st_size == 0
    log.to_csv(path, mode="a", header=fresh, index=False)
    return len(log)


def format_table(res: pd.DataFrame) -> str:
    """Sorted for reading: biggest edge first, unmatched rows last."""
    t = res.sort_values("edge", ascending=False, na_position="last", kind="stable")
    t = t[["player", "team", "market", "line", "side", "role", "mean", "sd", "p_more_cal", "p_less_cal",
           "p_push", "p_side", "edge", "flags"]].copy()
    t = t.round({"mean": 1, "sd": 1, "p_more_cal": 3, "p_less_cal": 3, "p_push": 3, "p_side": 3, "edge": 3})
    return t.to_string(index=False, na_rep="")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="local game date, e.g. 2026-10-09")
    ap.add_argument("--team", required=True, help="abbreviation of either team in the game, e.g. NY")
    ap.add_argument("--lines", required=True, help="CSV: player, market, line[, side]")
    ap.add_argument("--out", default="", help="comma-separated player names ruled out")
    ap.add_argument("--add", default="", help="comma-separated players who sat the last game but will play")
    ap.add_argument("--payout", type=float, default=3.0, help="slip multiplier (default 3 = Dabble 2-pick)")
    ap.add_argument("--legs", type=int, default=2, help="legs in the slip (default 2)")
    ap.add_argument("--model", default=P.DEFAULT_MODEL, help=f"models.registry() name (default {P.DEFAULT_MODEL})")
    ap.add_argument("--log", default=None, help="line log to append to (default data/line_log.csv); use a "
                                                "scratch path for demos and smoke runs")
    ap.add_argument("--no-role-bias", action="store_true",
                    help="skip the playoff starter/bench mean shift (it is only ever applied to context_glm_plus2; "
                         "models with starter_prev terms, including the default, already include that effect)")
    args = ap.parse_args(argv)
    names = lambda s: {n.strip().lower() for n in s.split(",") if n.strip()}

    lines = read_lines(args.lines)
    games = pd.read_parquet(ingest.GAMES_PATH)
    schedule = P.load_schedule(int(games["season"].max()))
    res, info = compare(lines, games, schedule, args.date, args.team, out=names(args.out), add=names(args.add),
                        model=args.model, role_bias=not args.no_role_bias, payout=args.payout, legs=args.legs)

    g = info["game"]
    print(f"{g['label'] or 'game'} | {g['away']} @ {g['home']} | tip {g['tip']:%Y-%m-%d %H:%M} UTC | "
          f"{'playoffs' if info['playoffs'] else 'regular season'}")
    print(f"model {info['model']} | data through {info['data_cutoff']} | {info['n_sims']} sims, seed {info['seed']}")
    print(f"role bias {info['role_bias_note']} | "
          f"{args.payout:g}x / {args.legs} legs: break-even {info['break_even']:.4f}\n")
    if info["stale"]:
        bar = "!" * 78
        print(bar)
        print("STALE DATA: projections are built on box scores that are missing recent games.")
        for msg in info["stale"].values():
            print("  " + msg)
        print(f"  Refresh first: python -m oklahoma.ingest --seasons {int(g['season'])}")
        print(bar + "\n")
    print(format_table(res))
    missing = res.loc[res["flags"].str.contains("NOT_ON_ROSTER"), "player"].unique()
    if len(missing):
        print(f"\nnot on tonight's projected roster (no numbers): {', '.join(missing)}. "
              "If she sat the last game but plays, pass --add \"Name\".")
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / f"compare_{args.date}_{args.team}.csv"
    res.to_csv(path, index=False)
    n = append_log(res, date=args.date, model=info["model"], data_cutoff=info["data_cutoff"], path=args.log)
    print(f"\n{len(res)} rows -> {path}\n{n} rows appended -> {LOG_PATH if args.log is None else args.log}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
