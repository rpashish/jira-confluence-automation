#!/usr/bin/env python3
"""Minimal MCP stdio server with three tools: echo, reverse, and upper."""

import json
import sys

PROTOCOL_FALLBACK = "2024-11-05"

TOOLS = [
    {
        "name": "echo",
        "description": "Return the input text unchanged.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to return unchanged."}
            },
            "required": ["text"],
        },
    },
    {
        "name": "reverse",
        "description": "Return the input text reversed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to reverse."}
            },
            "required": ["text"],
        },
    },
    {
        "name": "upper",
        "description": "Return the input text in uppercase.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to convert to uppercase."}
            },
            "required": ["text"],
        },
    },
]


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def tool_text(name: str, arguments: dict) -> str:
    text = arguments.get("text")
    if not isinstance(text, str):
        raise ValueError("text must be a string")
    if name == "echo":
        return text
    if name == "reverse":
        return text[::-1]
    if name == "upper":
        return text.upper()
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
                    "serverInfo": {"name": "echo", "version": "1.0.0"},
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
        arguments = params.get("arguments") or {}
        try:
            text = tool_text(name, arguments)
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
