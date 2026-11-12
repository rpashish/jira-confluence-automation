#!/usr/bin/env python3
"""Minimal MCP stdio server with one tool: get_time."""

import json
import sys
from datetime import datetime

PROTOCOL_FALLBACK = "2024-11-05"

TOOLS = [
    {
        "name": "get_time",
        "description": "Return the current local time as an ISO 8601 timestamp.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
]


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def tool_text(name: str) -> str:
    if name == "get_time":
        return datetime.now().astimezone().isoformat()
    raise ValueError(f"unknown tool: {name}")


def handle(message: dict) -> None:
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        version = params.get("protocolVersion") or PROTOCOL_FALLBACK
        send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": version,
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "time", "version": "1.0.0"},
                },
            }
        )
        return

    if method in ("notifications/initialized", "initialized"):
        return

    if method == "ping":
        send({"jsonrpc": "2.0", "id": request_id, "result": {}})
        return

    if method == "tools/list":
        send({"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}})
        return

    if method == "tools/call":
        name = params.get("name")
        try:
            text = tool_text(name)
        except ValueError as exc:
            send(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{"type": "text", "text": str(exc)}],
                        "isError": True,
                    },
                }
            )
            return
        send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": text}]},
            }
        )
        return

    if request_id is not None:
        send(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        )


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(message, dict):
            handle(message)


if __name__ == "__main__":
    main()
