import json
import logging
from functools import partial

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool

from . import db, mcp
from .config import SERVER_VERSION, Settings, load_settings

log = logging.getLogger("neuralhud")


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="NeuralHUD", version=SERVER_VERSION, docs_url=None, redoc_url=None, openapi_url=None)
    conn_factory = partial(db.connect, settings.database_url)

    @app.get("/health")
    def health() -> dict:
        return {"ok": True, "version": SERVER_VERSION}

    @app.api_route("/mcp", methods=["GET", "DELETE"])
    def mcp_not_streaming() -> Response:
        # Stateless server: no server-initiated SSE stream and no sessions to delete.
        return Response(status_code=405, headers={"Allow": "POST"})

    @app.post("/mcp")
    async def mcp_endpoint(request: Request) -> Response:
        origin = request.headers.get("origin")
        if origin and settings.allowed_origins and origin not in settings.allowed_origins:
            return JSONResponse({"error": "origin not allowed"}, status_code=403)

        if not settings.tokens or not settings.database_url:
            # Fail closed: never serve unauthenticated because config is missing.
            return JSONResponse({"error": "server not configured"}, status_code=503)
        scheme, _, presented = request.headers.get("authorization", "").partition(" ")
        actor = settings.actor_for(presented.strip()) if scheme.lower() == "bearer" and presented else None
        if actor is None:
            return JSONResponse(
                {"error": "invalid or missing bearer token"},
                status_code=401,
                headers={"WWW-Authenticate": 'Bearer realm="neuralhud"'},
            )

        version = request.headers.get("mcp-protocol-version")
        if version and version not in mcp.SUPPORTED_PROTOCOL_VERSIONS:
            return JSONResponse({"error": f"unsupported MCP-Protocol-Version {version}"}, status_code=400)

        try:
            body = json.loads(await request.body())
        except (ValueError, UnicodeDecodeError):
            return JSONResponse(mcp._error(None, mcp.PARSE_ERROR, "Parse error"), status_code=400)

        handle = partial(_handle_safely, actor=f"mcp:{actor}", conn_factory=conn_factory)
        if isinstance(body, list):
            if not body:
                return JSONResponse(mcp._error(None, mcp.INVALID_REQUEST, "Empty batch"), status_code=400)
            replies = [r for r in [await _run(handle, m) for m in body] if r is not None]
            return JSONResponse(replies) if replies else Response(status_code=202)
        reply = await _run(handle, body)
        return JSONResponse(reply) if reply is not None else Response(status_code=202)

    return app


async def _run(handle, msg):
    # Tool handlers use blocking psycopg; keep them off the event loop.
    return await run_in_threadpool(handle, msg)


def _handle_safely(msg, actor, conn_factory):
    try:
        return mcp.handle_message(msg, actor, conn_factory)
    except Exception:
        log.exception("unhandled MCP error")
        msg_id = msg.get("id") if isinstance(msg, dict) else None
        return mcp._error(msg_id, -32603, "Internal error")
