---
name: credit-audit
description: >
  This skill should be used when the user asks "are we wasting ElevenLabs
  credits", "audit our spend", "find duplicate generations", "how much did we
  burn on renders", "credit audit", "why is the ElevenLabs bill high", or
  wants to find duplicate or wasted TTS and render calls in NeuralHUD.
metadata:
  version: "0.1.0"
---

# Credit and dedup audit

Find money lost to duplicate, orphaned, or abandoned provider calls, and name the fix that stops each leak.

## Steps

1. Call `credit_audit`. Default `since_hours` to 168 (7 days); use the user's window if given.
2. Read each section:
   - `duplicate_generations`: the same job, provider, and request succeeded more than once. This is pure waste, and the tool gives `wasted_cost_units` for each.
   - `duplicate_scripts_across_jobs`: different jobs with an identical script, so the same audio was paid for twice across jobs.
   - `spend_on_cancelled_jobs`: money spent on work that was thrown away.
   - `orphaned_calls`: calls started but never recorded as finished. Either the result was lost or the worker didn't record it. Both risk a paid retry.
   - `totals_by_provider`: overall volume and failure rate.
3. For the worst duplicate, call `get_job` to read its events and see what caused the repeat: a retry, a webhook replay, or a manual force.

## Output

Lead with the total `wasted_cost_units` and the failure rate per provider. Then rank the leaks by cost, and for each give the job, what happened, and the root-cause fix. Typical fixes:

- Duplicates on one job: the worker is not checking `generation_calls` before calling the provider, or it reuses no idempotency key. Fix the worker.
- Duplicate scripts across jobs: whoever creates jobs should check before creating. NeuralHUD's `create_job` already blocks this, so duplicates mean jobs are being created outside it.
- Orphans: the worker must mark calls succeeded or failed in a `finally` block.
- High failure rate: check rate limits or input validation before retrying blindly.

State cost in the units the tool returns, which are whatever the workers record. Do not convert to dollars unless the user gives a rate.

## Rules

- Stay read-only. Do not cancel or retry jobs from this skill.
- If `generation_calls` is empty, say the workers are not recording provider calls. Every guard in NeuralHUD depends on that table, so treat this as the top finding.
