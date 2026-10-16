# Oklahoma

WNBA player prop model (points, rebounds, assists, PRA), following Bill Benter's method. **Research and backtest only.** Nothing here touches a sportsbook.

## Run it

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m oklahoma.ingest --seasons 2015-2026   # free box scores, ~7s
python -m oklahoma.backtest                     # walk-forward 2021-2026, ~6s
python -m pytest -q
```

## What it does

1. **Ingest** (`oklahoma/ingest.py`): ESPN box scores from the sportsdataverse/wehoop
   GitHub releases. Regular season + playoffs, players who actually played.
2. **Features** (`oklahoma/features.py`): pregame only, for every market. Rolling and
   season-to-date rates, minutes trend, defense allowed by position (G/F/C),
   teammates out tonight, schedule load, return from absence, hot streak.
   `tests/test_pipeline.py` fails if any feature sees the game it describes.
3. **Models** (`oklahoma/models.py`): each predicts a full count distribution
   (negative binomial), so it can price any over/under line.
   - `season_avg`, `last10`, `rate_x_minutes`: the baselines anything must beat.
   - `context_glm`: Benter stage 1, the fundamental model.
   - `context_glm_plus`: stage 1 plus teammates out, schedule, returns, hot streak.
5. **Benter stages 2-3** (`oklahoma/benter.py`): de-vig, market blend, fractional
   Kelly, walk-forward `blend_backtest`. Tested on simulated lines; waits for real ones.
4. **Backtest** (`oklahoma/backtest.py`): train on the 5 seasons before, test on
   the next, for 2021-2026. Never trains on the season it scores.

## What it can't tell you yet

There are **no real sportsbook lines** in this data. `line_proxy` is a stand-in
(the player's recent average, rounded to .5). Beating it is required, not
sufficient: a real book line is sharper. Proving betting edge needs historical
or forward-logged real lines, plus the price (odds) on each side.
