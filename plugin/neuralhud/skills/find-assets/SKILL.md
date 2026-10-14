---
name: find-assets
description: >
  This skill should be used when the user asks "where's the MP4 for", "get me
  the audio for", "find the render of", "link to the final video", "what
  assets does this job have", or needs ElevenLabs audio URLs, Remotion project
  paths, or rendered video files from NeuralHUD.
metadata:
  version: "0.1.0"
---

# Find assets

Locate generated files for a job and return usable links.

## Steps

1. If the user gave a job id, call `find_assets` with `job_id`. Otherwise call it with `search` set to the title words they used.
2. Set `kind` when they asked for one type: "audio" or "voiceover" -> `audio`; "project" or "composition" -> `remotion_project`; "video", "MP4", or "final" -> `video`.
3. If several jobs match, list them with their status and ask which one. Do not guess.
4. If nothing matches, call `list_jobs` with the same `search` to tell apart two cases: no such job, or a job that hasn't produced that asset yet. For the second case, report the job's current stage.

## Output

For each asset, give the job title, the kind, the URL as a clickable link, and when it was created. If a job has several assets of the same kind, list the newest first and say it is newest. Older entries usually come from regenerations.

## Rules

- Stay read-only. To attach a missing asset URL, use the pipeline-control skill.
- Never fabricate or "fix up" URLs. Return them exactly as stored.
