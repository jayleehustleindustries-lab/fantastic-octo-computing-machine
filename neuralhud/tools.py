"""MCP tools for the media state engine.

Read tools are side-effect free. Write tools:
  * require an idempotency_key; replaying a key returns the stored result,
  * refuse to move a job into a credit-spending state without confirm_spend,
  * refuse to regenerate audio/video that already succeeded unless forced.
"""

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Literal
from uuid import UUID

import psycopg
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class JobStatus(str, Enum):
    queued = "queued"
    tts_pending = "tts_pending"
    tts_done = "tts_done"
    render_pending = "render_pending"
    rendered = "rendered"
    delivered = "delivered"
    failed = "failed"
    cancelled = "cancelled"


SPEND_STATES = {JobStatus.tts_pending, JobStatus.render_pending}
TERMINAL_STATES = {JobStatus.delivered, JobStatus.cancelled}
IN_FLIGHT_STATES = [s.value for s in JobStatus if s not in TERMINAL_STATES and s != JobStatus.failed]

DEFAULT_STUCK_MINUTES = {
    "queued": 30,
    "tts_pending": 15,
    "tts_done": 30,
    "render_pending": 45,
    "rendered": 60,
}


class ToolError(Exception):
    """A failure the caller can act on; returned as an isError tool result."""


class Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


IdempotencyKey = Field(
    min_length=8,
    max_length=200,
    description="Unique key for this write. Reusing a key returns the original result instead of acting twice.",
)


# ---------------------------------------------------------------- read args

class PipelineStatusArgs(Args):
    since_hours: int = Field(24, ge=1, le=720, description="Window for delivered/failed counts.")


class ListJobsArgs(Args):
    status: list[JobStatus] | None = Field(None, description="Only these statuses.")
    search: str | None = Field(None, max_length=200, description="Case-insensitive match on title.")
    updated_within_hours: int | None = Field(None, ge=1, le=8760)
    limit: int = Field(25, ge=1, le=100)


class GetJobArgs(Args):
    job_id: UUID


class FindStuckJobsArgs(Args):
    thresholds_minutes: dict[str, int] | None = Field(
        None,
        description="Per-status minutes before a job counts as stuck. Defaults: "
        + json.dumps(DEFAULT_STUCK_MINUTES),
    )
    include_failed: bool = True
    failed_within_hours: int = Field(72, ge=1, le=720)
    limit: int = Field(50, ge=1, le=200)


class FindAssetsArgs(Args):
    job_id: UUID | None = None
    search: str | None = Field(None, max_length=200, description="Case-insensitive match on job title.")
    kind: Literal["audio", "remotion_project", "video"] | None = None
    limit: int = Field(25, ge=1, le=100)


class CreditAuditArgs(Args):
    since_hours: int = Field(168, ge=1, le=2160)
    orphan_after_minutes: int = Field(60, ge=5, le=1440, description="A started call with no result after this long is an orphan.")


# --------------------------------------------------------------- write args

class CreateJobArgs(Args):
    title: str = Field(min_length=1, max_length=300)
    script_text: str = Field(min_length=1, max_length=100_000)
    idempotency_key: str = IdempotencyKey
    allow_duplicate_script: bool = Field(
        False, description="Create even if a live job already has this exact script."
    )


class TransitionJobArgs(Args):
    job_id: UUID
    expected_status: JobStatus = Field(description="Status you saw. The write fails if it changed since.")
    to_status: JobStatus
    reason: str = Field(min_length=3, max_length=2000)
    idempotency_key: str = IdempotencyKey
    confirm_spend: bool = Field(False, description="Required to enter tts_pending or render_pending (spends credits).")
    force_regenerate: bool = Field(False, description="Allow spending again although a successful generation exists.")


class RetryJobArgs(Args):
    job_id: UUID
    reason: str = Field(min_length=3, max_length=2000)
    idempotency_key: str = IdempotencyKey
    confirm_spend: bool = False
    force_regenerate: bool = False


class CancelJobArgs(Args):
    job_id: UUID
    reason: str = Field(min_length=3, max_length=2000)
    idempotency_key: str = IdempotencyKey


class RegisterAssetArgs(Args):
    job_id: UUID
    kind: Literal["audio", "remotion_project", "video"]
    url: str = Field(pattern=r"^https://", max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str = IdempotencyKey


# ------------------------------------------------------------------ helpers

def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (UUID, Enum)):
        return value.value if isinstance(value, Enum) else str(value)
    if isinstance(value, Decimal):
        return float(value)
    return value


def _job_summary(row: dict) -> dict:
    return {k: row[k] for k in (
        "id", "title", "status", "failed_stage", "last_error", "attempt",
        "script_hash", "created_at", "updated_at", "status_changed_at",
    )}


def _load_job(conn: psycopg.Connection, job_id: UUID, lock: bool = False) -> dict:
    row = conn.execute(
        "select * from jobs where id = %s" + (" for update" if lock else ""), (job_id,)
    ).fetchone()
    if row is None:
        raise ToolError(f"Job {job_id} not found.")
    return row


def _guard_spend(conn, job: dict, to_status: JobStatus, confirm_spend: bool, force: bool) -> None:
    if to_status not in SPEND_STATES:
        return
    provider = "elevenlabs" if to_status == JobStatus.tts_pending else "remotion"
    if not confirm_spend:
        raise ToolError(
            f"Moving to {to_status.value} triggers a paid {provider} call. "
            "Confirm with the user, then call again with confirm_spend=true."
        )
    if force:
        return
    if provider == "elevenlabs":
        prior = conn.execute(
            """select count(*) as n from generation_calls
               where job_id = %s and provider = 'elevenlabs'
                 and request_hash = %s and status = 'succeeded'""",
            (job["id"], job["script_hash"]),
        ).fetchone()["n"]
        if prior:
            raise ToolError(
                "Audio for this exact script was already generated successfully "
                f"({prior} call(s)). Use the existing audio asset. Only if the user "
                "explicitly wants new audio, call again with force_regenerate=true."
            )
    else:
        prior = conn.execute(
            """select count(*) as n from assets where job_id = %s and kind = 'video'""",
            (job["id"],),
        ).fetchone()["n"]
        if prior:
            raise ToolError(
                f"This job already has {prior} rendered video asset(s). Only if the user "
                "explicitly wants a re-render, call again with force_regenerate=true."
            )


def _transition(conn, job_id: UUID, expected: JobStatus, to: JobStatus, actor: str, reason: str) -> dict:
    try:
        with conn.transaction():
            return conn.execute(
                "select * from transition_job(%s, %s, %s, %s, %s)",
                (job_id, expected.value, to.value, actor, reason),
            ).fetchone()
    except psycopg.errors.RaiseException as e:
        raise ToolError(e.diag.message_primary or str(e)) from None
    except psycopg.errors.NoDataFound:
        raise ToolError(f"Job {job_id} not found.") from None


def _with_idempotency(conn, tool: str, args: BaseModel, actor: str, fn: Callable[[], dict]) -> dict:
    payload = args.model_dump(mode="json", exclude={"idempotency_key"})
    request_hash = hashlib.sha256(json.dumps([tool, payload], sort_keys=True).encode()).hexdigest()
    key = args.idempotency_key
    inserted = conn.execute(
        """insert into mcp_requests (idempotency_key, tool, request_hash, actor)
           values (%s, %s, %s, %s) on conflict do nothing returning idempotency_key""",
        (key, tool, request_hash, actor),
    ).fetchone()
    if inserted is None:
        prior = conn.execute(
            "select tool, request_hash, response from mcp_requests where idempotency_key = %s", (key,)
        ).fetchone()
        if prior["tool"] != tool or prior["request_hash"] != request_hash:
            raise ToolError("idempotency_key was already used for a different request. Use a new key.")
        if prior["response"] is None:
            raise ToolError("A request with this idempotency_key is still in progress. Try again shortly.")
        return {**prior["response"], "replayed": True}
    result = _jsonable(fn())
    conn.execute(
        "update mcp_requests set response = %s where idempotency_key = %s",
        (json.dumps(result), key),
    )
    return result


# --------------------------------------------------------------- read tools

def pipeline_status(conn, a: PipelineStatusArgs, actor: str) -> dict:
    by_status = {
        r["status"]: r["n"]
        for r in conn.execute("select status, count(*) as n from jobs group by status").fetchall()
    }
    window = conn.execute(
        """select to_status, count(*) as n from job_events
           where created_at > now() - make_interval(hours => %s)
             and to_status in ('delivered', 'failed', 'cancelled', 'queued')
           group by to_status""",
        (a.since_hours,),
    ).fetchall()
    oldest = conn.execute(
        """select id, title, status, status_changed_at,
                  round(extract(epoch from now() - status_changed_at) / 60) as minutes_in_state
           from jobs where status = any(%s::job_status[])
           order by status_changed_at limit 1""",
        (IN_FLIGHT_STATES,),
    ).fetchone()
    return {
        "jobs_by_status": {s.value: by_status.get(s.value, 0) for s in JobStatus},
        "in_flight": sum(by_status.get(s, 0) for s in IN_FLIGHT_STATES),
        "window_hours": a.since_hours,
        "events_in_window": {r["to_status"]: r["n"] for r in window},
        "oldest_in_flight": oldest,
    }


def list_jobs(conn, a: ListJobsArgs, actor: str) -> dict:
    where, params = [], []
    if a.status:
        where.append("status = any(%s::job_status[])")
        params.append([s.value for s in a.status])
    if a.search:
        where.append("title ilike %s")
        params.append(f"%{a.search}%")
    if a.updated_within_hours:
        where.append("updated_at > now() - make_interval(hours => %s)")
        params.append(a.updated_within_hours)
    sql = "select * from jobs"
    if where:
        sql += " where " + " and ".join(where)
    sql += " order by updated_at desc limit %s"
    params.append(a.limit)
    rows = conn.execute(sql, params).fetchall()
    return {"jobs": [_job_summary(r) for r in rows], "count": len(rows)}


def get_job(conn, a: GetJobArgs, actor: str) -> dict:
    job = _load_job(conn, a.job_id)
    return {
        "job": {**_job_summary(job), "script_text": job["script_text"]},
        "assets": conn.execute(
            "select id, kind, url, metadata, created_at from assets where job_id = %s order by created_at",
            (a.job_id,),
        ).fetchall(),
        "events": conn.execute(
            """select from_status, to_status, actor, reason, created_at from job_events
               where job_id = %s order by created_at desc, id desc limit 50""",
            (a.job_id,),
        ).fetchall(),
        "generation_calls": conn.execute(
            """select provider, status, cost_units, request_hash = %s as matches_current_script,
                      created_at, completed_at
               from generation_calls where job_id = %s order by created_at""",
            (job["script_hash"], a.job_id),
        ).fetchall(),
    }


def find_stuck_jobs(conn, a: FindStuckJobsArgs, actor: str) -> dict:
    thresholds = dict(DEFAULT_STUCK_MINUTES)
    for k, v in (a.thresholds_minutes or {}).items():
        if k not in thresholds:
            raise ToolError(f"thresholds_minutes key '{k}' must be one of {sorted(thresholds)}.")
        if not 1 <= v <= 10080:
            raise ToolError("thresholds_minutes values must be between 1 and 10080.")
        thresholds[k] = v
    rows = conn.execute(
        """with t(status, minutes) as (select key::job_status, value::int from jsonb_each_text(%s::jsonb))
           select j.*, round(extract(epoch from now() - j.status_changed_at) / 60) as minutes_in_state,
                  t.minutes as threshold_minutes
           from jobs j join t on j.status = t.status
           where j.status_changed_at < now() - make_interval(mins => t.minutes)
           order by j.status_changed_at limit %s""",
        (json.dumps(thresholds), a.limit),
    ).fetchall()
    failed = []
    if a.include_failed:
        failed = conn.execute(
            """select * from jobs where status = 'failed'
               and status_changed_at > now() - make_interval(hours => %s)
               order by status_changed_at desc limit %s""",
            (a.failed_within_hours, a.limit),
        ).fetchall()

    def evidence(job: dict) -> dict:
        calls = conn.execute(
            """select provider, status, count(*) as n from generation_calls
               where job_id = %s group by provider, status""",
            (job["id"],),
        ).fetchall()
        kinds = [r["kind"] for r in conn.execute(
            "select distinct kind from assets where job_id = %s", (job["id"],)
        ).fetchall()]
        return {"generation_calls": calls, "asset_kinds": kinds}

    return {
        "thresholds_minutes": thresholds,
        "stuck": [
            {**_job_summary(r), "minutes_in_state": r["minutes_in_state"],
             "threshold_minutes": r["threshold_minutes"], **evidence(r)}
            for r in rows
        ],
        "failed": [{**_job_summary(r), **evidence(r)} for r in failed],
    }


def find_assets(conn, a: FindAssetsArgs, actor: str) -> dict:
    if a.job_id is None and not a.search:
        raise ToolError("Give a job_id or a search term.")
    where, params = [], []
    if a.job_id:
        where.append("a.job_id = %s")
        params.append(a.job_id)
    if a.search:
        where.append("j.title ilike %s")
        params.append(f"%{a.search}%")
    if a.kind:
        where.append("a.kind = %s")
        params.append(a.kind)
    params.append(a.limit)
    rows = conn.execute(
        f"""select a.id, a.job_id, j.title, j.status as job_status, a.kind, a.url, a.metadata, a.created_at
            from assets a join jobs j on j.id = a.job_id
            where {' and '.join(where)}
            order by a.created_at desc limit %s""",
        params,
    ).fetchall()
    return {"assets": rows, "count": len(rows)}


def credit_audit(conn, a: CreditAuditArgs, actor: str) -> dict:
    window = (a.since_hours,)
    totals = conn.execute(
        """select provider, count(*) as calls,
                  count(*) filter (where status = 'succeeded') as succeeded,
                  count(*) filter (where status = 'failed') as failed,
                  coalesce(sum(cost_units), 0) as cost_units
           from generation_calls where created_at > now() - make_interval(hours => %s)
           group by provider""",
        window,
    ).fetchall()
    duplicates = conn.execute(
        """select g.job_id, j.title, g.provider, g.request_hash, count(*) as successful_calls,
                  sum(g.cost_units) - min(g.cost_units) as wasted_cost_units
           from generation_calls g join jobs j on j.id = g.job_id
           where g.status = 'succeeded' and g.created_at > now() - make_interval(hours => %s)
           group by g.job_id, j.title, g.provider, g.request_hash
           having count(*) > 1
           order by wasted_cost_units desc""",
        window,
    ).fetchall()
    duplicate_scripts = conn.execute(
        """select script_hash, count(*) as jobs, array_agg(id order by created_at) as job_ids,
                  min(title) as example_title
           from jobs where created_at > now() - make_interval(hours => %s) and status <> 'cancelled'
           group by script_hash having count(*) > 1""",
        window,
    ).fetchall()
    cancelled_spend = conn.execute(
        """select j.id as job_id, j.title, sum(g.cost_units) as cost_units, count(*) as calls
           from generation_calls g join jobs j on j.id = g.job_id
           where j.status = 'cancelled' and g.created_at > now() - make_interval(hours => %s)
           group by j.id, j.title order by cost_units desc""",
        window,
    ).fetchall()
    orphans = conn.execute(
        """select g.job_id, j.title, g.provider, g.created_at,
                  round(extract(epoch from now() - g.created_at) / 60) as minutes_open
           from generation_calls g join jobs j on j.id = g.job_id
           where g.status = 'started' and g.created_at < now() - make_interval(mins => %s)
           order by g.created_at""",
        (a.orphan_after_minutes,),
    ).fetchall()
    return {
        "window_hours": a.since_hours,
        "totals_by_provider": totals,
        "duplicate_generations": duplicates,
        "wasted_cost_units": float(sum(d["wasted_cost_units"] for d in duplicates)),
        "duplicate_scripts_across_jobs": duplicate_scripts,
        "spend_on_cancelled_jobs": cancelled_spend,
        "orphaned_calls": orphans,
    }


# -------------------------------------------------------------- write tools

def create_job(conn, a: CreateJobArgs, actor: str) -> dict:
    def run() -> dict:
        existing = conn.execute(
            "select * from jobs where idempotency_key = %s", (a.idempotency_key,)
        ).fetchone()
        if existing:
            return {"job": _job_summary(existing), "created": False}
        if not a.allow_duplicate_script:
            dupes = conn.execute(
                """select id, title, status from jobs
                   where script_hash = encode(sha256(convert_to(%s, 'UTF8')), 'hex')
                     and status <> 'cancelled' limit 5""",
                (a.script_text,),
            ).fetchall()
            if dupes:
                raise ToolError(
                    "A live job already has this exact script: "
                    + json.dumps(_jsonable(dupes))
                    + ". Reuse it, or call again with allow_duplicate_script=true."
                )
        job = conn.execute(
            """insert into jobs (idempotency_key, title, script_text) values (%s, %s, %s) returning *""",
            (a.idempotency_key, a.title, a.script_text),
        ).fetchone()
        conn.execute(
            "insert into job_events (job_id, from_status, to_status, actor, reason) values (%s, null, 'queued', %s, 'created via MCP')",
            (job["id"], actor),
        )
        return {"job": _job_summary(job), "created": True}

    return _with_idempotency(conn, "create_job", a, actor, run)


def transition_job(conn, a: TransitionJobArgs, actor: str) -> dict:
    def run() -> dict:
        if a.expected_status == JobStatus.failed and a.to_status != JobStatus.cancelled:
            raise ToolError("Use retry_job to restart a failed job.")
        job = _load_job(conn, a.job_id, lock=True)
        _guard_spend(conn, job, a.to_status, a.confirm_spend, a.force_regenerate)
        row = _transition(conn, a.job_id, a.expected_status, a.to_status, actor, a.reason)
        return {"job": _job_summary(row)}

    return _with_idempotency(conn, "transition_job", a, actor, run)


def retry_job(conn, a: RetryJobArgs, actor: str) -> dict:
    def run() -> dict:
        job = _load_job(conn, a.job_id, lock=True)
        if job["status"] != JobStatus.failed.value:
            raise ToolError(f"Job is {job['status']}, not failed; nothing to retry.")
        if job["failed_stage"] is None:
            raise ToolError("Job has no recorded failed_stage; transition it manually.")
        target = JobStatus(job["failed_stage"])
        _guard_spend(conn, job, target, a.confirm_spend, a.force_regenerate)
        row = _transition(conn, a.job_id, JobStatus.failed, target, actor, a.reason)
        return {"job": _job_summary(row), "resumed_at": target.value}

    return _with_idempotency(conn, "retry_job", a, actor, run)


def cancel_job(conn, a: CancelJobArgs, actor: str) -> dict:
    def run() -> dict:
        job = _load_job(conn, a.job_id, lock=True)
        row = _transition(conn, a.job_id, JobStatus(job["status"]), JobStatus.cancelled, actor, a.reason)
        open_calls = conn.execute(
            "select provider, count(*) as n from generation_calls where job_id = %s and status = 'started' group by provider",
            (a.job_id,),
        ).fetchall()
        return {
            "job": _job_summary(row),
            "note": "Cancelling stops further stages; it does not abort provider calls already running.",
            "open_provider_calls": open_calls,
        }

    return _with_idempotency(conn, "cancel_job", a, actor, run)


def register_asset(conn, a: RegisterAssetArgs, actor: str) -> dict:
    def run() -> dict:
        _load_job(conn, a.job_id)
        row = conn.execute(
            """insert into assets (job_id, kind, url, metadata) values (%s, %s, %s, %s)
               on conflict (job_id, kind, url) do update set metadata = assets.metadata
               returning id, job_id, kind, url, metadata, created_at, (xmax = 0) as created""",
            (a.job_id, a.kind, a.url, json.dumps(a.metadata)),
        ).fetchone()
        return {"asset": row}

    return _with_idempotency(conn, "register_asset", a, actor, run)


# ----------------------------------------------------------------- registry

class Tool(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    title: str
    description: str
    args: type[Args]
    handler: Callable
    read_only: bool
    destructive: bool = False


TOOLS: dict[str, Tool] = {t.name: t for t in [
    Tool(name="pipeline_status", title="Pipeline status", read_only=True, args=PipelineStatusArgs, handler=pipeline_status,
         description="Counts of jobs per status, deliveries/failures in a time window, and the oldest in-flight job."),
    Tool(name="list_jobs", title="List jobs", read_only=True, args=ListJobsArgs, handler=list_jobs,
         description="List jobs, newest activity first, filtered by status, title search, or recency."),
    Tool(name="get_job", title="Get job", read_only=True, args=GetJobArgs, handler=get_job,
         description="Full detail for one job: script, assets, status history, and paid generation calls."),
    Tool(name="find_stuck_jobs", title="Find stuck jobs", read_only=True, args=FindStuckJobsArgs, handler=find_stuck_jobs,
         description="Jobs sitting in a stage longer than its threshold, plus recent failures, with evidence (provider calls, assets) for diagnosis."),
    Tool(name="find_assets", title="Find assets", read_only=True, args=FindAssetsArgs, handler=find_assets,
         description="Look up audio, Remotion project, and rendered video URLs by job id or job title."),
    Tool(name="credit_audit", title="Credit audit", read_only=True, args=CreditAuditArgs, handler=credit_audit,
         description="Provider spend totals, duplicate generations with wasted cost, duplicate scripts across jobs, spend on cancelled jobs, and orphaned calls."),
    Tool(name="create_job", title="Create job", read_only=False, args=CreateJobArgs, handler=create_job,
         description="Create a job in 'queued'. Spends nothing. Refuses if a live job has the same script unless allow_duplicate_script=true."),
    Tool(name="transition_job", title="Transition job", read_only=False, destructive=True, args=TransitionJobArgs, handler=transition_job,
         description="Move a job along the state machine with compare-and-set on expected_status. Entering tts_pending/render_pending spends credits and needs confirm_spend=true."),
    Tool(name="retry_job", title="Retry failed job", read_only=False, destructive=True, args=RetryJobArgs, handler=retry_job,
         description="Resume a failed job at the stage where it failed. Needs confirm_spend=true if that stage spends credits."),
    Tool(name="cancel_job", title="Cancel job", read_only=False, destructive=True, args=CancelJobArgs, handler=cancel_job,
         description="Cancel a job (terminal). Does not abort provider calls already running."),
    Tool(name="register_asset", title="Register asset", read_only=False, args=RegisterAssetArgs, handler=register_asset,
         description="Attach an https asset URL (audio, Remotion project, or video) to a job. Re-registering the same URL is a no-op."),
]}


def tool_descriptors() -> list[dict]:
    out = []
    for t in TOOLS.values():
        out.append({
            "name": t.name,
            "title": t.title,
            "description": t.description,
            "inputSchema": t.args.model_json_schema(),
            "annotations": {
                "title": t.title,
                "readOnlyHint": t.read_only,
                "destructiveHint": t.destructive,
                "idempotentHint": True,
                "openWorldHint": False,
            },
        })
    return out


def call_tool(conn_factory, name: str, arguments: dict | None, actor: str) -> tuple[dict, bool]:
    """Run a tool. Returns (structured_result, is_error)."""
    tool = TOOLS.get(name)
    if tool is None:
        raise KeyError(name)
    try:
        args = tool.args.model_validate(arguments or {})
    except ValidationError as e:
        problems = "; ".join(f"{'.'.join(map(str, err['loc'])) or 'arguments'}: {err['msg']}" for err in e.errors())
        return {"error": f"Invalid arguments: {problems}"}, True
    try:
        with conn_factory() as conn:
            return _jsonable(tool.handler(conn, args, actor)), False
    except ToolError as e:
        return {"error": str(e)}, True
