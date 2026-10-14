# Media Automation State Engine (NeuralHUD)

Core database backend powering FastAPI media orchestration, ElevenLabs audio synthesis jobs, and Remotion rendering state transitions, plus an MCP server and Claude plugin to operate it.

---

### Responsibilities
- **State Transitions:** Atomic status tracking for raw scripts, TTS audio generation, video rendering, and delivery.
- **Idempotency & Deduplication:** Prevents duplicate AI generation calls, API credit burn, and race conditions across webhooks.
- **Asset Registry:** Canonical storage for generated ElevenLabs audio URLs, Remotion asset paths, and rendered MP4 artifacts.
- **Dispatcher Sync:** Emits webhooks/events to notify downstream review dashboards upon render completion.

---

### Engine vs. Dashboard Split
- **Backend (Supabase / Postgres):** Handles high-frequency atomic state changes, webhooks, and raw asset mapping.
- **Frontend / Review (ClickUp / Notion):** Human-in-the-loop review station notified only after video rendering completes successfully.

---

## Layout

| Path | What |
|---|---|
| `db/schema.sql` | Tables, state machine, and the `transition_job()` function. Re-runnable. |
| `neuralhud/` | FastAPI app serving MCP (Streamable HTTP, stateless) at `/mcp` |
| `api/index.py`, `vercel.json` | Vercel entrypoint |
| `plugin/neuralhud/` | Claude plugin: 5 skills plus the MCP connection |
| `dist/neuralhud.plugin` | Packaged plugin (`scripts/build-plugin.sh` rebuilds it) |
| `.claude-plugin/marketplace.json` | Makes this repo installable as a plugin marketplace |

## Deploy

1. **Database.** In the Supabase SQL editor, run `db/schema.sql`.
2. **Tokens.** Generate one token per client, each at least 32 characters:
   `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
3. **Vercel.** Import the repo and set these environment variables:

   | Variable | Value |
   |---|---|
   | `DATABASE_URL` | Supabase **transaction pooler** URI (port `6543`). A direct connection will exhaust Postgres connections under serverless load. |
   | `NEURALHUD_MCP_TOKENS` | `label:token` pairs, comma-separated, e.g. `jay:abc...,cowork:def...`. Labels show up in the audit log. To rotate, add the new pair, roll out clients, then remove the old one. |
   | `NEURALHUD_ALLOWED_ORIGINS` | Optional. A comma-separated allowlist for browser `Origin` headers. |

4. **Check it.**
   `curl https://<app>.vercel.app/health` should return `{"ok": true, ...}`.
   `curl -X POST https://<app>.vercel.app/mcp` should return `401`.
   The server returns `503` if the tokens or the database URL are missing. It never serves unauthenticated requests.

## Connect Claude

Install the plugin, which includes the connection plus the skills:

```
/plugin install neuralhud --marketplace jayleehustleindustries-lab/fantastic-octo-computing-machine
```

Then set `NEURALHUD_MCP_URL=https://<app>.vercel.app/mcp` and `NEURALHUD_MCP_TOKEN=<token>` in the environment Claude runs in.

For the bare connection without the skills:

```bash
claude mcp add --transport http neuralhud https://<app>.vercel.app/mcp \
  --header "Authorization: Bearer $NEURALHUD_MCP_TOKEN"
```

## Contract for workers and webhooks

The MCP guards only work if the rest of the pipeline follows these rules:

- **Change status only through `select transition_job(job_id, expected, to, actor, reason)`.** Never `update jobs set status = ...` directly. This function is the compare-and-set and the audit log.
- **Before every paid call**, insert a `generation_calls` row with a unique `idempotency_key`. Insert-before-call means a crashed worker leaves an orphan the audit can find, instead of a silent double charge. For ElevenLabs, set `request_hash = jobs.script_hash`.
- **After the call**, set `status` to `succeeded` or `failed`, plus `completed_at` and `cost_units`. Do this in a `finally` block.
- **Register outputs** in `assets` before advancing to `tts_done` or `rendered`.

## MCP tools

Read: `pipeline_status`, `list_jobs`, `get_job`, `find_stuck_jobs`, `find_assets`, `credit_audit`.
Write: `create_job`, `transition_job`, `retry_job`, `cancel_job`, `register_asset`.

Every write needs an `idempotency_key`. Entering `tts_pending` or `render_pending` needs `confirm_spend=true`. Regenerating audio or video that already succeeded needs `force_regenerate=true`.

## Tests

```bash
pip install -r requirements-dev.txt
NEURALHUD_TEST_DATABASE_URL=postgresql://postgres@localhost:5432/neuralhud_test pytest
```

Use a disposable database: the tests truncate the tables.
