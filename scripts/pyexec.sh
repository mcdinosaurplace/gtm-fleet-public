#!/bin/sh
# pyexec.sh — run repo Python: the kit venv when present, else python3.
# Used as the MCP server command in .claude-plugin/plugin.json and mcp/demo.json so
# servers get the pinned deps (mcp, httpx) without requiring them system-wide.
here="$(cd "$(dirname "$0")/.." && pwd)"
if [ -x "$here/.venv/bin/python" ]; then
  exec "$here/.venv/bin/python" "$@"
fi
exec python3 "$@"
