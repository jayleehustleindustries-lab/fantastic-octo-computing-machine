---
name: pipeline-status
description: >
  This skill should be used when the user asks "what's the pipeline doing",
  "what's in flight", "what shipped today", "how many videos are rendering",
  "pipeline status", "give me a NeuralHUD update", or wants a snapshot of
  jobs moving through the script -> TTS -> render -> delivery pipeline.
metadata:
  version: "0.1.0"
---

# Pipeline status

Produce a short, decision-ready snapshot of the NeuralHUD pipeline.

## Steps

1. Call `pipeline_status`. Default `since_hours` to 24; use the user's window if they named one ("this week" = 168).
2. If `oldest_in_flight` has been in its state longer than its stuck threshold (queued 30m, tts_pending 15m, tts_done 30m, render_pending 45m, rendered 60m), or `jobs_by_status.failed` is above 0, call `find_stuck_jobs` with `limit` 10 to name the problem jobs.
3. If the user asked about specific jobs or titles, call `list_jobs` with `search` or `status` filters.

## Output

Lead with one sentence that answers "is the pipeline healthy?". Then:

- **Flow:** queued -> tts_pending -> tts_done -> render_pending -> rendered -> delivered, with counts at each stage.
- **Window:** delivered, failed, and cancelled counts for the window, and new jobs queued.
- **Attention:** each stuck or failed job with title, stage, and minutes in state. Omit this section when there are none.

Keep it under 12 lines. Use job titles, not UUIDs, unless the user asks for ids.

## Rules

- Stay read-only. If the user wants to act on a stuck or failed job, hand off to the triage-stuck-jobs or pipeline-control skill.
- Report numbers exactly as the tools return them. Never estimate counts.
- If a tool call fails with 401, tell the user their NeuralHUD token is wrong or expired. If it fails with 503, the server is missing configuration.
