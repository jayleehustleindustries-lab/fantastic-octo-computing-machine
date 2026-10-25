# JobCommand Commercial Engine

Second engine built on the Media-state-engine pattern, aimed at short vertical
**commercials for jobcommand.app**: a stock HeyGen presenter delivers the hook
and CTA on camera, B-roll carries the pain scenes, a **real screen recording**
of the app carries the fix, and a branded end card closes it out.

```
manifest CSV ─validate─▶ queued ─worker─▶ rendering ─▶ staged ─/approve─▶ approved
                                             │            │
                                             ▼            └─ retry (re-render)
                                           failed ── retry ─▶ queued
```

Differences from Media-state-engine:

| | Media-state-engine | Commercial engine |
|---|---|---|
| Avatar | Custom likeness (Jordan reference pack + image gate) | **Stock HeyGen avatar** — no likeness refs, no image gate |
| Unit of work | One script → one avatar video | One commercial = N scenes (`presenter` / `broll` / `screen_recording`) + end card |
| Store | Postgres | SQLite (WAL, single node). Postgres port is a follow-up |
| Output | YouTube distribute | Staged MP4 + `.srt` captions; human approve; no auto-posting |

## Guarantees

- **Validate before spend.** The manifest is checked up front (columns, empty
  cells, scene numbering, source type, HUD ≤ 32 chars) and every problem is
  reported at once. Nothing queues from a bad sheet.
- **No fake success.** A scene either produces a probe-verified video or is
  marked `failed` with its error. One failed scene fails the job; no MP4 is
  written. Stub files are never treated as output.
- **Narration sets the clock.** ElevenLabs audio is generated first; each
  scene runs exactly as long as its narration (+0.25s). Visuals loop or trim
  to fit; the HeyGen presenter lip-syncs to that same audio, so the voice is
  identical across all scenes.
- **Pay once.** Narration, presenter renders, composed scenes and end cards are
  content-addressed and reused on retry. The HeyGen `video_id` is persisted
  before polling, so a crash resumes the render instead of buying another.
- **Parallel, rate-limited.** Scenes run concurrently behind per-provider
  semaphores (`ELEVENLABS_CONCURRENCY`, `HEYGEN_CONCURRENCY`,
  `FFMPEG_CONCURRENCY`), not a global lock.
- **Safe HUD burn-in.** Overlay text goes through `drawtext=textfile=`, so
  `:` `,` `'` `%` `$` in copy can't break FFmpeg.
- **No HTTP timeouts.** `POST /commercials` returns `202` with job ids; a
  separate worker renders; `GET /commercials/{id}` shows per-scene status.
- **Locked down.** API returns 503 until `COMMERCIAL_ENGINE_API_KEY` is set.
  Manifests are read only from `MANIFESTS_DIR` by plain file name.
- **Copy can't drift mid-job.** If the manifest changes after a job is queued,
  the job fails closed; queue a new one for the new copy.
- **Nothing ships without a human.** Rendered jobs sit in `staged` until
  `POST /commercials/{id}/approve` with an `approved_by`.

## Manifest

`manifests/jobcommand_v2.csv`: one row per scene.

| column | notes |
|---|---|
| `video_id` | Commercial id (`CK-01`). Scene ids are derived: `CK-01-03` |
| `concept_name`, `trade` | Same on every scene of a commercial. One trade per ad |
| `scene_num` | 1..N, no gaps |
| `source` | `presenter` (HeyGen stock avatar), `broll` (`assets/broll/{scene_id}.mp4`), `screen_recording` (`assets/screen_recordings/{scene_id}.mp4`) |
| `visual_prompt` | Framing note / shot brief for whoever produces the footage |
| `hud_overlay_text` | ≤ 32 chars, trade language, readable in ~2s |
| `voiceover_script` | Spoken line. Write numbers and URLs how they're said ("jobcommand dot app") |

The shipped copy covers only features confirmed live: online booking +
deposits, instant invoicing + pay on the spot (with auto-reminders),
multi-truck dispatch, live GPS. Every ad names JobCommand and ends on the URL.

## Run it

Python 3.11+, `ffmpeg`/`ffprobe` on PATH.

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # set API key, ElevenLabs voice, HeyGen key + stock avatar id

python -m commercial_engine.cli validate jobcommand_v2.csv   # lists missing footage
python -m commercial_engine.cli enqueue jobcommand_v2.csv --video CK-01
python -m commercial_engine.cli render-next
python -m commercial_engine.cli status JOB_ID
python -m commercial_engine.cli approve JOB_ID --by "Your Name"
```

As a service:

```bash
uvicorn commercial_engine.api:app --port 8000
python -m commercial_engine.worker        # separate process

curl -X POST localhost:8000/commercials -H "Authorization: Bearer $COMMERCIAL_ENGINE_API_KEY" \
  -H 'content-type: application/json' -d '{"manifest":"jobcommand_v2.csv","video_ids":["CK-01"]}'
```

Endpoints: `POST /commercials`, `GET /commercials`, `GET /commercials/{id}`,
`POST /commercials/{id}/retry` (failed/staged only), `POST /commercials/{id}/approve`.

Output: `data/outputs/{video_id}/{video_id}-{job}.mp4` + `.srt` (upload the SRT
as captions; most viewers watch muted).

## Before the first paid run

1. Put the six footage files in place (`validate` lists them). Screen
   recordings must be real app captures with demo data.
2. Pick a stock avatar id from your HeyGen library and set `HEYGEN_AVATAR_ID`.
3. Run one commercial (`--video CK-01`) and check it before queueing the rest.
4. The HeyGen asset-upload + `/v3/videos` audio mode follow Media-state-engine's
   client and HeyGen's docs as of writing; confirm against your plan on that
   first run.
5. Set `CTA_TEXT` to your real offer (free trial? demo?) once decided.

## Tests

```bash
pytest -q
```

Pipeline tests render real MP4s with FFmpeg and fake providers (no credits):
full render to `staged`, failed scene → no output → retry reuses paid work,
HeyGen crash resume, manifest-edited-after-queue, HUD special characters.
