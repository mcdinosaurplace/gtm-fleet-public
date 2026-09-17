#!/usr/bin/env python3
"""
render_config.py — turn mcp/demo.json into a config Claude Code can load.

`mcp/demo.json` is a template: it names the fixture servers with the literal
placeholders `{PLUGIN_ROOT}` and `{FLEET_ROOT}` so the file stays portable and
committable. Claude Code needs absolute paths, so both callers — `scripts/tick.py`
(headless) and the Makefile's `demo` target (interactive) — render it here first:

    python3 scripts/demo/render_config.py [--out <path>]

Output defaults to `FLEET_ROOT/state/working/demo-mcp.resolved.json` (gitignored
scratch, next to the database the demo reads). Prints the rendered path.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts import fleet_paths  # noqa: E402

TEMPLATE = fleet_paths.PLUGIN_ROOT / "mcp" / "demo.json"
OUT_NAME = "demo-mcp.resolved.json"


def render_config(template: Path | None = None, out: Path | None = None) -> Path:
    """Substitute {PLUGIN_ROOT} / {FLEET_ROOT} in `template`, write `out`, return it.

    Both roots are absolute and resolved at call time, so an external FLEET_ROOT
    (or a test's throwaway root) is honored rather than whatever was current at
    import. Raises FileNotFoundError if the template is missing — callers that
    treat demo config as optional should check `TEMPLATE.exists()` first.
    """
    template = Path(template) if template else TEMPLATE
    root = fleet_paths.fleet_root(strict=False)
    out = Path(out) if out else root / "state" / "working" / OUT_NAME
    text = (template.read_text()
            .replace("{PLUGIN_ROOT}", str(fleet_paths.PLUGIN_ROOT))
            .replace("{FLEET_ROOT}", str(root)))
    json.loads(text)  # fail here, not inside the agent session, if the template is malformed
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--template", help=f"default: {TEMPLATE}")
    ap.add_argument("--out", help=f"default: FLEET_ROOT/state/working/{OUT_NAME}")
    args = ap.parse_args()
    print(render_config(args.template, args.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
