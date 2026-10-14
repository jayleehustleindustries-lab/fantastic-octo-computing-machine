# NeuralHUD state machine

```
queued -> tts_pending -> tts_done -> render_pending -> rendered -> delivered
   \           \            \              \              \
    +-----------+------------+--------------+--------------+--> failed --(retry)--> failed_stage
    +-----------+------------+--------------+--------------+--> cancelled
                                                       failed --> cancelled
```

- `delivered` and `cancelled` are terminal. Nothing leaves them.
- `failed` records `failed_stage` (where the job was) and `last_error` (the reason given). `retry_job` returns the job to exactly `failed_stage` and adds 1 to `attempt`.
- Every transition is compare-and-set: it succeeds only if the job is still in `expected_status`. That's how two actors (a webhook and Claude, say) are kept from both advancing the same job.
- Every transition writes a `job_events` row with the actor. MCP writes show as `mcp:<token label>`.

## Spend states

| State | Provider | Server guard |
|---|---|---|
| `tts_pending` | ElevenLabs | needs `confirm_spend`; refused if a succeeded ElevenLabs call exists for this exact script, unless `force_regenerate` is set |
| `render_pending` | Remotion | needs `confirm_spend`; refused if the job already has a `video` asset, unless `force_regenerate` is set |

The regeneration guard depends on workers writing `generation_calls` rows, and for ElevenLabs on setting `request_hash` to the job's `script_hash`. If workers skip this, the guard can't see prior spend. The credit-audit skill flags that case.

## Common refusals and what to do

| Server message | Meaning | Response |
|---|---|---|
| "job X is Y, expected Z" | Someone else moved it | Re-read the job and re-confirm with the user |
| "transition A -> B is not allowed" | Illegal edge | Pick a legal path from the diagram |
| "Moving to ... triggers a paid ... call" | Missing `confirm_spend` | Ask the user, then resend with the flag |
| "already generated" / "already has ... video" | Regeneration guard | Offer the existing asset |
| "idempotency_key was already used for a different request" | Key reused | Generate a new key |
| "A live job already has this exact script" | Duplicate script | Show the existing job |
