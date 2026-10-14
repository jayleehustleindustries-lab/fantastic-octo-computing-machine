# NeuralHUD plugin

Lets Claude run the NeuralHUD media pipeline (script -> ElevenLabs TTS -> Remotion render -> delivery) from chat.

## Skills

| Skill | What it does | Writes? |
|---|---|---|
| pipeline-status | Snapshot of jobs per stage, throughput, and blockers | No |
| triage-stuck-jobs | Diagnoses stuck and failed jobs and recommends the cheapest safe fix | Only with approval, via pipeline-control |
| find-assets | Finds audio, Remotion project, and MP4 links for a job | No |
| credit-audit | Finds duplicate, orphaned, and abandoned ElevenLabs/Remotion spend | No |
| pipeline-control | Creates, advances, retries, and cancels jobs, and attaches assets | Yes, guarded |

## Install

In Claude Code:

```
/plugin install neuralhud --marketplace jayleehustleindustries-lab/fantastic-octo-computing-machine
```

Or upload `dist/neuralhud.plugin` from this repo in Claude's plugin settings.

## Setup

The plugin connects to your NeuralHUD server's `/mcp` endpoint. Set two environment variables where Claude runs:

| Variable | Example |
|---|---|
| `NEURALHUD_MCP_URL` | `https://your-app.vercel.app/mcp` |
| `NEURALHUD_MCP_TOKEN` | One of the tokens in the server's `NEURALHUD_MCP_TOKENS` |

Restart Claude after setting them. To check the connection, ask "what's the pipeline doing?".

## Safety

The server enforces these rules no matter what the model does:

- Entering `tts_pending` or `render_pending` (paid steps) requires `confirm_spend=true`. The skills ask you before setting it.
- Regenerating audio or video that already succeeded is refused unless explicitly forced.
- Every write needs an idempotency key, so retries never act twice.
- Status changes are compare-and-set, so a stale view can't overwrite a newer state.
- Every change is logged in `job_events` with the token label that made it.
