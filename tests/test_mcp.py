import uuid

from neuralhud.config import parse_tokens

import pytest

from .conftest import TOKEN


def key():
    return f"test-{uuid.uuid4()}"


def make_job(tool, title="Episode 1", script="Hello world"):
    data, err = tool("create_job", title=title, script_text=script, idempotency_key=key())
    assert not err, data
    return data["job"]


def move(tool, job, frm, to, **extra):
    return tool("transition_job", job_id=job["id"], expected_status=frm, to_status=to,
                reason="test step", idempotency_key=key(), **extra)


# ---------------------------------------------------------------- transport

def test_rejects_missing_and_wrong_token(client, rpc):
    assert client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"}).status_code == 401
    r = rpc("ping", token="x" * 40)
    assert r.status_code == 401
    assert r.headers["www-authenticate"].startswith("Bearer")


def test_fails_closed_without_tokens(db_url):
    from fastapi.testclient import TestClient
    from neuralhud.app import create_app
    from neuralhud.config import Settings

    c = TestClient(create_app(Settings(database_url=db_url, tokens={}, allowed_origins=frozenset())))
    assert c.post("/mcp", json={}).status_code == 503


def test_initialize_negotiates_version(rpc):
    r = rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}})
    body = r.json()["result"]
    assert body["protocolVersion"] == "2025-06-18"
    assert body["capabilities"] == {"tools": {"listChanged": False}}
    r = rpc("initialize", {"protocolVersion": "1999-01-01"})
    assert r.json()["result"]["protocolVersion"] == "2025-11-25"


def test_notification_gets_202(client):
    r = client.post("/mcp", headers={"Authorization": f"Bearer {TOKEN}"},
                    json={"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert r.status_code == 202 and r.content == b""


def test_get_is_405_and_bad_json_is_400(client):
    assert client.get("/mcp").status_code == 405
    r = client.post("/mcp", headers={"Authorization": f"Bearer {TOKEN}"}, content=b"{nope")
    assert r.status_code == 400 and r.json()["error"]["code"] == -32700


def test_unsupported_protocol_header(client):
    r = client.post("/mcp", headers={"Authorization": f"Bearer {TOKEN}", "MCP-Protocol-Version": "1999-01-01"},
                    json={"jsonrpc": "2.0", "id": 1, "method": "ping"})
    assert r.status_code == 400


def test_tools_list_has_annotations(rpc):
    tools = {t["name"]: t for t in rpc("tools/list").json()["result"]["tools"]}
    assert len(tools) == 11
    assert tools["pipeline_status"]["annotations"]["readOnlyHint"] is True
    assert tools["transition_job"]["annotations"]["destructiveHint"] is True
    assert tools["create_job"]["inputSchema"]["additionalProperties"] is False


def test_unknown_method_and_tool(rpc):
    assert rpc("resources/list").json()["error"]["code"] == -32601
    assert rpc("tools/call", {"name": "drop_tables"}).json()["error"]["code"] == -32602


def test_invalid_arguments_are_tool_errors(tool):
    data, err = tool("get_job", job_id="not-a-uuid")
    assert err and "job_id" in data["error"]
    data, err = tool("list_jobs", limit=5, surprise=True)
    assert err and "surprise" in data["error"]


def test_parse_tokens():
    assert parse_tokens("a" * 32) == {"default": "a" * 32}
    assert parse_tokens(f"ops:{'b' * 32}, bot:{'c' * 32}") == {"ops": "b" * 32, "bot": "c" * 32}
    with pytest.raises(ValueError):
        parse_tokens("short")


# ------------------------------------------------------------------ writes

def test_create_job_idempotent_and_audited(tool, sql):
    k = key()
    first, err = tool("create_job", title="A", script_text="S", idempotency_key=k)
    assert not err and first["created"]
    again, err = tool("create_job", title="A", script_text="S", idempotency_key=k)
    assert again["replayed"] and again["job"]["id"] == first["job"]["id"]
    assert sql("select count(*) as n from jobs")[0][0] == 1
    assert sql("select actor from job_events")[0][0] == "mcp:tester"


def test_idempotency_key_reuse_with_other_args_rejected(tool):
    k = key()
    tool("create_job", title="A", script_text="S", idempotency_key=k)
    data, err = tool("create_job", title="B", script_text="S2", idempotency_key=k)
    assert err and "different request" in data["error"]


def test_duplicate_script_blocked(tool):
    make_job(tool, script="same script")
    data, err = tool("create_job", title="dupe", script_text="same script", idempotency_key=key())
    assert err and "already has this exact script" in data["error"]
    data, err = tool("create_job", title="dupe", script_text="same script", idempotency_key=key(),
                     allow_duplicate_script=True)
    assert not err


def test_spend_requires_confirmation(tool):
    job = make_job(tool)
    data, err = move(tool, job, "queued", "tts_pending")
    assert err and "confirm_spend" in data["error"]
    data, err = move(tool, job, "queued", "tts_pending", confirm_spend=True)
    assert not err and data["job"]["status"] == "tts_pending"


def test_failed_guard_does_not_consume_key(tool):
    job = make_job(tool)
    k = key()
    args = dict(job_id=job["id"], expected_status="queued", to_status="tts_pending", reason="go now", idempotency_key=k)
    data, err = tool("transition_job", **args)
    assert err and "confirm_spend" in data["error"]
    data, err = tool("transition_job", **args, confirm_spend=True)
    # Different args (confirm_spend changed) but the failed call was rolled back, so the key is free.
    assert not err and data["job"]["status"] == "tts_pending"


def test_compare_and_set_rejects_stale_status(tool):
    job = make_job(tool)
    move(tool, job, "queued", "tts_pending", confirm_spend=True)
    data, err = move(tool, job, "queued", "cancelled")
    assert err and "expected queued" in data["error"]


def test_illegal_edge_rejected(tool):
    job = make_job(tool)
    data, err = move(tool, job, "queued", "delivered")
    assert err and "not allowed" in data["error"]


def test_regenerating_audio_blocked(tool, sql):
    job = make_job(tool, script="regen me")
    move(tool, job, "queued", "tts_pending", confirm_spend=True)
    sql("""insert into generation_calls (job_id, provider, request_hash, idempotency_key, status, cost_units)
           select id, 'elevenlabs', script_hash, 'el-1', 'succeeded', 3 from jobs where id = %s""", (job["id"],))
    move(tool, job, "tts_pending", "failed")
    data, err = tool("retry_job", job_id=job["id"], reason="retry", idempotency_key=key(), confirm_spend=True)
    assert err and "already generated" in data["error"]
    data, err = tool("retry_job", job_id=job["id"], reason="retry", idempotency_key=key(),
                     confirm_spend=True, force_regenerate=True)
    assert not err and data["resumed_at"] == "tts_pending" and data["job"]["attempt"] == 1


def test_full_lifecycle_and_reads(tool, sql):
    job = make_job(tool, title="Lifecycle", script="full run")
    move(tool, job, "queued", "tts_pending", confirm_spend=True)
    move(tool, job, "tts_pending", "tts_done")
    asset, err = tool("register_asset", job_id=job["id"], kind="audio", url="https://cdn.example/a.mp3", idempotency_key=key())
    assert not err and asset["asset"]["created"]
    again, _ = tool("register_asset", job_id=job["id"], kind="audio", url="https://cdn.example/a.mp3", idempotency_key=key())
    assert again["asset"]["created"] is False
    move(tool, job, "tts_done", "render_pending", confirm_spend=True)
    move(tool, job, "render_pending", "rendered")
    move(tool, job, "rendered", "delivered")

    detail, _ = tool("get_job", job_id=job["id"])
    assert detail["job"]["status"] == "delivered"
    assert [e["to_status"] for e in detail["events"]][0] == "delivered"
    assert len(detail["events"]) == 6

    found, _ = tool("find_assets", search="lifecycle")
    assert found["count"] == 1 and found["assets"][0]["url"].endswith("a.mp3")

    status, err = tool("pipeline_status", since_hours=1)
    assert not err and status["jobs_by_status"]["delivered"] == 1
    assert status["events_in_window"]["delivered"] == 1

    listed, _ = tool("list_jobs", status=["delivered"], search="life")
    assert listed["count"] == 1

    data, err = tool("cancel_job", job_id=job["id"], reason="too late", idempotency_key=key())
    assert err and "not allowed" in data["error"]


def test_register_asset_requires_https(tool):
    job = make_job(tool)
    data, err = tool("register_asset", job_id=job["id"], kind="video", url="http://x/y.mp4", idempotency_key=key())
    assert err


def test_find_stuck_and_failed(tool, sql):
    job = make_job(tool, title="Stuck one", script="stuck")
    move(tool, job, "queued", "tts_pending", confirm_spend=True)
    sql("update jobs set status_changed_at = now() - interval '2 hours' where id = %s", (job["id"],))
    other = make_job(tool, title="Broken", script="broken")
    move(tool, other, "queued", "failed")

    data, err = tool("find_stuck_jobs")
    assert not err
    assert [j["id"] for j in data["stuck"]] == [job["id"]]
    assert data["stuck"][0]["minutes_in_state"] >= 119
    assert [j["id"] for j in data["failed"]] == [other["id"]]
    assert data["failed"][0]["failed_stage"] == "queued"

    data, err = tool("find_stuck_jobs", thresholds_minutes={"tts_pending": 500})
    assert data["stuck"] == []
    data, err = tool("find_stuck_jobs", thresholds_minutes={"delivered": 5})
    assert err


def test_credit_audit(tool, sql):
    job = make_job(tool, title="Spendy", script="spendy")
    for i, cost in enumerate([5, 5, 7]):
        sql("""insert into generation_calls (job_id, provider, request_hash, idempotency_key, status, cost_units)
               select id, 'elevenlabs', script_hash, %s, 'succeeded', %s from jobs where id = %s""",
            (f"dup-{i}", cost, job["id"]))
    sql("""insert into generation_calls (job_id, provider, request_hash, idempotency_key, status, created_at)
           values (%s, 'remotion', 'r', 'orphan-1', 'started', now() - interval '3 hours')""", (job["id"],))
    tool("cancel_job", job_id=job["id"], reason="abandoned", idempotency_key=key())

    data, err = tool("credit_audit", since_hours=24)
    assert not err
    assert data["wasted_cost_units"] == 12
    assert data["duplicate_generations"][0]["successful_calls"] == 3
    assert data["spend_on_cancelled_jobs"][0]["cost_units"] == 17
    assert len(data["orphaned_calls"]) == 1
    providers = {t["provider"]: t for t in data["totals_by_provider"]}
    assert providers["elevenlabs"]["succeeded"] == 3


def test_find_assets_needs_filter(tool):
    data, err = tool("find_assets")
    assert err


def test_rls_enabled_on_every_table(sql):
    rows = sql("""select relname from pg_class c join pg_namespace n on n.oid = c.relnamespace
                  where n.nspname = 'public' and c.relkind = 'r' and not c.relrowsecurity""")
    assert rows == []
