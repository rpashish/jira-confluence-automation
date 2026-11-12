#!/usr/bin/env python3
"""Minimal MCP stdio server with one tool: calculator."""

import json
import sys

PROTOCOL_FALLBACK = "2024-11-05"

TOOLS = [
    {
        "name": "calculator",
        "description": "Add, subtract, multiply, or divide two numbers.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "Arithmetic operation to apply to a and b.",
                },
                "a": {"type": "number", "description": "First operand."},
                "b": {"type": "number", "description": "Second operand."},
            },
            "required": ["operation", "a", "b"],
        },
    },
]


def send(message: dict) -> None:
    sys.stdout.write(json.dumps(message, separators=(",", ":")) + "\n")
    sys.stdout.flush()


def as_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")
    return float(value)


def format_result(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return str(value)


def tool_text(name: str, arguments: dict) -> str:
    if name != "calculator":
        raise ValueError(f"unknown tool: {name}")
    operation = arguments.get("operation")
    if operation not in ("add", "subtract", "multiply", "divide"):
        raise ValueError("operation must be add, subtract, multiply, or divide")
    a = as_number(arguments.get("a"), "a")
    b = as_number(arguments.get("b"), "b")
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    else:
        if b == 0:
            raise ValueError("division by zero")
        result = a / b
    return format_result(result)


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
                    "serverInfo": {"name": "calculator", "version": "1.0.0"},
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
