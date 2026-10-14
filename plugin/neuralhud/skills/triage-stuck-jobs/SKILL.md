---
name: triage-stuck-jobs
description: >
  This skill should be used when the user asks "what's stuck", "why did this
  job fail", "which renders are hung", "triage the pipeline", "fix the failed
  jobs", "a video never came out", or needs stuck or failed NeuralHUD jobs
  diagnosed with a recommended fix.
metadata:
  version: "0.1.0"
---

# Triage stuck and failed jobs

Diagnose jobs that stopped moving, then recommend the cheapest safe fix for each one.

## Steps

1. Call `find_stuck_jobs`. Pass `thresholds_minutes` only if the user gave their own limits.
2. For each stuck or failed job, use the evidence the tool returns (`generation_calls` by provider and status, `asset_kinds`). Call `get_job` only when you need the event history or `last_error`.
3. Classify each job with the table below.
4. Present findings, then offer actions. Do not take any write action from this skill without the user's explicit approval. Execute approved actions by following the pipeline-control skill's write protocol.

## Diagnosis table

| Stage | Evidence | Likely cause | Recommended action |
|---|---|---|---|
| queued, stuck | no calls | dispatcher never picked it up | Check the dispatcher. If the user approves, move it to tts_pending (spends credits). |
| tts_pending, stuck | elevenlabs `started`, never finished | ElevenLabs webhook lost or worker crashed | Check ElevenLabs for the request first. If audio exists, register the asset and move to tts_done. That's free. |
| tts_pending, stuck | elevenlabs `succeeded` | worker forgot to advance | Register the audio asset if missing, then move to tts_done. Never regenerate. |
| tts_pending, stuck | no calls | worker never started | Mark failed with that reason, then retry (spends credits). |
| tts_done, stuck | audio asset present | render dispatcher idle | If the user approves, move to render_pending (spends credits). |
| render_pending, stuck | remotion `started` | render hung or callback lost | Check Remotion first. If an MP4 exists, register it and move to rendered. |
| render_pending, stuck | `video` asset present | worker forgot to advance | Move to rendered. Free. |
| rendered, stuck | video present | delivery webhook failed | Move to delivered after confirming the review dashboard has the video. |
| failed | any | see `last_error` and `failed_stage` | Retry only if the error is transient (timeout, 5xx, rate limit). Otherwise fix the input first. |

Prefer free actions (registering an existing asset, advancing a stalled state) over anything that spends credits. A stuck job whose provider call already succeeded almost never needs a regeneration.

## Output

Group jobs by recommended action. For each, give the title, stage, minutes stuck, a one-line cause, and the action. Mark any action that spends credits with **(spends credits)**. End by asking which actions to run.

## Rules

- Treat `failed` calls in `generation_calls` as spent money too. Mention repeated failures on the same job (2 or more) as a cost problem.
- Never suggest `force_regenerate` unless the user says the existing audio or video is bad.
