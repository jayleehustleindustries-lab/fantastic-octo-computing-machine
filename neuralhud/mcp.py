"""Stateless MCP over Streamable HTTP (JSON responses, no SSE, no sessions).

Serverless functions can't keep sessions or open streams, so every POST is
handled on its own and answered with a single JSON body. That covers what
this server needs: initialize, ping, tools/list, tools/call.
"""

import json
from typing import Any, Callable

from . import tools
from .config import SERVER_NAME, SERVER_VERSION

SUPPORTED_PROTOCOL_VERSIONS = ("2025-11-25", "2025-06-18", "2025-03-26")
LATEST_PROTOCOL_VERSION = SUPPORTED_PROTOCOL_VERSIONS[0]

INSTRUCTIONS = (
    "NeuralHUD is the state engine for an automated vertical-video pipeline "
    "(script -> ElevenLabs TTS -> Remotion render -> delivery). Use read tools freely. "
    "Before any write, read the job first and pass the status you saw as expected_status. "
    "Entering tts_pending or render_pending spends real credits: get the user's explicit "
    "go-ahead before setting confirm_spend=true, and never set force_regenerate=true "
    "unless the user asked for new audio/video. Generate a fresh idempotency_key per "
    "intended action and reuse it only when retrying that same action."
)

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602


def _error(msg_id: Any, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}


def _result(msg_id: Any, result: dict) -> dict:
    return {"jsonrpc": "2.0", "id": msg_id, "result": result}


def handle_message(msg: Any, actor: str, conn_factory: Callable) -> dict | None:
    """Handle one JSON-RPC message. Returns None for notifications/responses."""
    if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
        return _error(None, INVALID_REQUEST, "Invalid JSON-RPC message")
    if "method" not in msg:
        return None  # a response from the client; nothing to do
    method, msg_id, params = msg["method"], msg.get("id"), msg.get("params") or {}
    if "id" not in msg:
        return None  # notification (e.g. notifications/initialized)
    if not isinstance(params, dict):
        return _error(msg_id, INVALID_PARAMS, "params must be an object")

    if method == "initialize":
        requested = params.get("protocolVersion")
        version = requested if requested in SUPPORTED_PROTOCOL_VERSIONS else LATEST_PROTOCOL_VERSION
        return _result(msg_id, {
            "protocolVersion": version,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "title": "NeuralHUD", "version": SERVER_VERSION},
            "instructions": INSTRUCTIONS,
        })
    if method == "ping":
        return _result(msg_id, {})
    if method == "tools/list":
        return _result(msg_id, {"tools": tools.tool_descriptors()})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments")
        if not isinstance(name, str) or (arguments is not None and not isinstance(arguments, dict)):
            return _error(msg_id, INVALID_PARAMS, "tools/call needs a string name and object arguments")
        try:
            data, is_error = tools.call_tool(conn_factory, name, arguments, actor)
        except KeyError:
            return _error(msg_id, INVALID_PARAMS, f"Unknown tool: {name}")
        result = {
            "content": [{"type": "text", "text": json.dumps(data, indent=2)}],
            "isError": is_error,
        }
        if not is_error:
            result["structuredContent"] = data
        return _result(msg_id, result)
    return _error(msg_id, METHOD_NOT_FOUND, f"Method not found: {method}")
