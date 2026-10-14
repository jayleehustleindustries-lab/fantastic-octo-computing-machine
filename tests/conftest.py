import itertools
import json
import os
import pathlib

import psycopg
import pytest
from fastapi.testclient import TestClient

from neuralhud.app import create_app
from neuralhud.config import Settings

DB_URL = os.environ.get("NEURALHUD_TEST_DATABASE_URL")
TOKEN = "t" * 40
SCHEMA = pathlib.Path(__file__).resolve().parent.parent / "db" / "schema.sql"


@pytest.fixture(scope="session")
def db_url():
    if not DB_URL:
        pytest.skip("set NEURALHUD_TEST_DATABASE_URL to a disposable Postgres database")
    with psycopg.connect(DB_URL, autocommit=True) as conn:
        conn.execute(SCHEMA.read_text())
    return DB_URL


@pytest.fixture
def sql(db_url):
    with psycopg.connect(db_url, autocommit=True) as conn:
        conn.execute("truncate jobs, mcp_requests cascade")

        def run(query, params=None):
            cur = conn.execute(query, params)
            return cur.fetchall() if cur.description else None

        yield run


@pytest.fixture
def client(sql, db_url):
    settings = Settings(database_url=db_url, tokens={"tester": TOKEN}, allowed_origins=frozenset())
    return TestClient(create_app(settings))


@pytest.fixture
def rpc(client):
    ids = itertools.count(1)

    def call(method, params=None, token=TOKEN):
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json, text/event-stream"}
        return client.post("/mcp", headers=headers, json={"jsonrpc": "2.0", "id": next(ids), "method": method, "params": params or {}})

    return call


@pytest.fixture
def tool(rpc):
    """Call a tool; returns (data, is_error)."""

    def call(name, **arguments):
        r = rpc("tools/call", {"name": name, "arguments": arguments})
        assert r.status_code == 200, r.text
        result = r.json()["result"]
        return json.loads(result["content"][0]["text"]), result["isError"]

    return call
