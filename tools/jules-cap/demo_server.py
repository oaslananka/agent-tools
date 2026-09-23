#!/usr/bin/env python3
"""Local MCP server used to validate arbitrary MCP access from a Jules VM."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from mcp.server.mcpserver import MCPServer

mcp = MCPServer(
    "jules-cap-demo",
    instructions="Read-only demo server for validating MCP access from a Jules VM.",
)

_SESSION_COUNTER = 0


@mcp.tool()
def echo(text: str) -> str:
    """Return text unchanged."""
    return text


@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two integers."""
    return a + b


@mcp.tool()
def session_counter(delta: int = 1) -> int:
    """Increment process-local state to validate persistent MCP client/server sessions."""
    global _SESSION_COUNTER
    _SESSION_COUNTER += delta
    return _SESSION_COUNTER


@mcp.tool()
def repo_summary() -> dict[str, object]:
    """Return a small read-only summary of the current Git repository."""
    root = Path.cwd()
    status = subprocess.run(
        ["git", "status", "--short", "--branch"],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    head = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=root,
        check=False,
        text=True,
        capture_output=True,
    )
    return {
        "cwd": str(root),
        "head": head.stdout.strip(),
        "status": status.stdout.strip().splitlines(),
    }


@mcp.resource("lab://about")
def about() -> str:
    """Describe this MCP server."""
    return "Jules Capability Runtime local MCP validation server."


@mcp.prompt()
def inspect_repo(focus: str = "architecture") -> str:
    """Return a short repository-inspection prompt."""
    return (
        "Inspect the repository read-only. Focus on "
        f"{focus}. Batch independent discovery commands and report evidence."
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8767)
    args = parser.parse_args()

    if args.http:
        mcp.run(
            transport="streamable-http",
            host=args.host,
            port=args.port,
            stateless_http=True,
            json_response=True,
        )
    else:
        mcp.run()
