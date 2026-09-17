#!/usr/bin/env python3
"""
demo/connector.py — the no-MCP fallback the agent routers name.

Same fixtures, same outbox, same `_provenance` as the MCP servers — it just calls
the functions in fixture_mcp.py directly and prints the JSON, so a demo still runs
when `mcp/demo.json` did not load (no `--mcp-config`, a stale session, a fixture
server that failed to start).

    python3 scripts/demo/connector.py <connector> <tool> ['<json-args>']

    python3 scripts/demo/connector.py slack slack_search_channels
    python3 scripts/demo/connector.py hubspot search_crm_objects '{"objectType":"contacts"}'
    python3 scripts/demo/connector.py --list

Exit 0 on success; 2 on an unknown connector/tool or malformed arguments.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.demo.fixture_mcp import REGISTRY  # noqa: E402


def call(connector: str, tool: str, args: dict) -> dict:
    """Invoke one fixture tool. Raises KeyError if the connector or tool is unknown."""
    return REGISTRY[connector][tool](**args)


def main() -> int:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if argv[0] == "--list":
        for connector, tools in REGISTRY.items():
            print(f"{connector}: {' '.join(tools)}")
        return 0
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    connector, tool = argv[0], argv[1]
    if connector not in REGISTRY:
        print(f"unknown connector {connector!r} — one of: {', '.join(sorted(REGISTRY))}", file=sys.stderr)
        return 2
    if tool not in REGISTRY[connector]:
        print(f"unknown tool {tool!r} for {connector} — one of: {', '.join(REGISTRY[connector])}", file=sys.stderr)
        return 2
    try:
        args = json.loads(argv[2]) if len(argv) > 2 and argv[2].strip() else {}
    except json.JSONDecodeError as e:
        print(f"argument 3 must be a JSON object: {e}", file=sys.stderr)
        return 2
    if not isinstance(args, dict):
        print("argument 3 must be a JSON object, e.g. '{\"objectType\":\"contacts\"}'", file=sys.stderr)
        return 2
    try:
        print(json.dumps(call(connector, tool, args), indent=2))
    except TypeError as e:
        print(f"{connector} {tool}: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
