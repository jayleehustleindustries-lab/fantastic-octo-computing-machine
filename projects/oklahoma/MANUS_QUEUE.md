# Manus work queue: Benter Method Model V1 (Project Oklahoma)

Work these **in order**. Don't start a task until the one before it is verified.
Linear project: https://linear.app/jayleehustlespace/project/benter-method-model-v1-5806a0c992dd
Read `HANDOFF.md` first for background and the rules that must survive any change.

---

## Task 1: URGENT security fix in Supabase (Linear JOR-8)

**Where:** Supabase project **vig-tracker** (ref `nnfhuklwcmibntszmywq`) → SQL editor.
**Run:** the whole file `supabase/PENDING_security_fixes.sql`.

It does three things:
1. Closes `public.picks`. Its policy "server access" lets anyone with the public anon key read and write bets.
2. Drops the `http` extension. Its functions are executable by everyone, and it's only needed during box-score reloads.
3. Deletes the 222 All-Star and exhibition rows from `wnba_player_games`, plus expired loader tokens.

**Verify (all three must match):**
```sql
select (select count(*) from pg_policies where tablename = 'picks')  as picks_policies,   -- 0
       (select count(*) from pg_extension where extname = 'http')     as http_installed,   -- 0
       (select count(*) from public.wnba_player_games)                as box_rows;         -- 55476
```
Then mark JOR-8 Done in Linear and paste the verify output into a comment.

---

## Task 2: Create the GitHub repo (Linear JOR-10)

1. Create an **empty, private** GitHub repo named `oklahoma`.
2. From this folder:
```bash
git init -b main && git add -A && git commit -m "Oklahoma: Benter Method Model V1"
git remote add origin https://github.com/<account>/oklahoma.git
git push -u origin main
```
3. Check it works from a clean clone:
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python -m oklahoma.ingest --seasons 2015-2026   # expect: wrote 55,476 player-games
python -m pytest -q                             # expect: 11 passed
python -m oklahoma.backtest                     # expect: context_glm_plus best in all 4 markets
```
Mark JOR-10 Done with the repo link.

---

## Task 3: Pause the empty nightly Outlier sync (Linear JOR-11)

The nightly "Outlier Betting Engine" sync (writes `outlier-sync-YYYY-MM-DD.md` to Google Drive)
has run on an empty sheet every night since Sep 22. **Pause it.** Don't delete it. It gets
repointed to Supabase `prop_lines` after Task 5.

---

## Task 4: Get historical odds quotes (Linear JOR-9). Needs owner approval to buy.

Ask each provider for a **sample file and a price**. **Don't pay without the owner's approval.**
Providers: The Odds API, OpticOdds / OddsJam API, SportsDataIO, Sportradar.

Requirements (reject anything missing these):
- WNBA **player props**: points, rebounds, assists, PRA
- Seasons **2023–2026**
- **Both over and under prices** (American odds)
- **Multiple books**, including at least one sharp book
- **Timestamps**, with opening and closing lines

Post a comparison table (provider, price, seasons, books, has close?, sample OK?) on JOR-9.
Keep any API key in an environment secret, **never** in code, chat or Linear.

---

## Task 5: Load odds into Supabase (Linear JOR-13). Blocked by Task 4.

Load into `public.prop_lines` (schema: `supabase/migrations/20261003_oklahoma_core_tables.sql`).
Match rows to `wnba_player_games` (`game_id`, `athlete_id`) by date, team and player name.
**Report the match rate. Never invent a match.** Unmatched rows stay with null ids.

## Task 6: Benter stage 2-3 backtest on real lines (Linear JOR-14). Blocked by Task 5.

Build rows with `season, p_model, over_price, under_price, went_over, close_p_over`, where
`p_model` comes from `context_glm_plus` (walk-forward) at the real line. Then run
`oklahoma.benter.blend_backtest`.

**Report:** the blend weights (a = model, b = market), log loss of blend vs market vs model,
ROI, and average closing-line value, per season.

**Decision gate:** if the blend doesn't beat the market across seasons, **stop and report.**
No live betting.

---

## Daily: project a slate (no lines needed)

```bash
python -m oklahoma.ingest --seasons 2015-2026 --force   # pull last night's games
python -m oklahoma.project --date YYYY-MM-DD [--out "Name,Name"] [--add "Name"]
```
Check the official injury report first. `--out` removes listed-out players; `--add` brings
back players who sat the last game. Output: `reports/slate_<date>.csv` with projection, fair
line, P(over) at the fair line, and the 10th-90th percentile range. These are projections, not bets.

---

## Owner's rule: default is YES, except money, deletions and security changes

---

## Rules (non-negotiable)

- No leakage: inputs use only information from before the game. Keep `pytest` green.
- Walk-forward testing only: never train on the season being scored.
- Public, official data only. **No scraping personal social media, no tracking players'
  private lives, no scraping sportsbook sites against their terms.**
- No fabricated lines, matches or results. If data is missing, say so.
- Research and backtest only. Nothing places bets.
