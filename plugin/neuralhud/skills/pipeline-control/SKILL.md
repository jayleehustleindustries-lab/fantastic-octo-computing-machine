---
name: pipeline-control
description: >
  This skill should be used when the user asks to "create a job", "queue this
  script", "start TTS", "kick off the render", "retry that job", "cancel the
  job", "mark it delivered", "advance the job", "attach this MP4", or
  otherwise wants to change job state in NeuralHUD. It covers every write
  action and the safety protocol for credit-spending steps.
metadata:
  version: "0.1.0"
---

# Pipeline control

Change NeuralHUD job state safely. Every write follows the protocol below. The server enforces most of it too, but follow it anyway so the user is never surprised by a refusal or a charge.

## Write protocol

1. **Read first.** Call `get_job`, or `list_jobs` to find the job, immediately before writing. Pass the status you just saw as `expected_status`. If the server says the job moved, re-read it and tell the user. Never retry blindly with the new status.
2. **One key per intended action.** Generate a fresh `idempotency_key` (for example `cowork-<job-short-id>-<action>-<random 8 chars>`) for each action the user approves. Reuse the same key only to retry that same call after a network error. A replayed key returns `"replayed": true` and does nothing new.
3. **Spending needs explicit consent.** Moving into `tts_pending` (ElevenLabs) or `render_pending` (Remotion) costs money. Before setting `confirm_spend=true`, tell the user which job and which provider, and get a clear yes in this conversation. Approving a batch counts only for the jobs listed in it.
4. **Never force regeneration on your own.** Set `force_regenerate=true` only when the user explicitly says the existing audio or video is bad and wants a new one. If the server refuses because audio or video already exists, offer the existing asset instead.
5. **Write a real reason.** `reason` goes into the audit log. Write what happened and why, for example "ElevenLabs webhook lost; audio confirmed in dashboard", not "user asked".
6. **Report the result.** State the job's new status, and say "replayed" if the call was a replay.

## Actions

| User intent | Tool | Spends credits |
|---|---|---|
| Queue a new script | `create_job` | No |
| Start voiceover | `transition_job` queued -> tts_pending | **Yes** |
| Audio is ready | `register_asset` (audio), then `transition_job` tts_pending -> tts_done | No |
| Start render | `transition_job` tts_done -> render_pending | **Yes** |
| Render is ready | `register_asset` (video), then `transition_job` render_pending -> rendered | No |
| Hand off for review | `transition_job` rendered -> delivered | No |
| Mark broken | `transition_job` <current> -> failed, with the error as `reason` | No |
| Retry failed | `retry_job` (resumes at `failed_stage`) | If that stage spends |
| Stop a job | `cancel_job` | No, but in-flight provider calls still bill |

`create_job` refuses when a live job has the same script. Show the user the existing job. Pass `allow_duplicate_script=true` only if they want a separate copy.

For the full state machine and its edge cases, read `references/state-machine.md`.

## Batches

For requests like "retry all failed renders", first list the exact jobs and the total number that will spend credits, then get one approval for that list. Execute one call per job with its own key. If any call fails, stop and report before continuing.
