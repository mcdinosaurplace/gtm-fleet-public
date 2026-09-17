#!/usr/bin/env python3
"""
schedule_render.py — print scheduler snippets from schedule.yaml. Never installs anything.

    python3 scripts/schedule_render.py --format crontab [--only NAME]
    python3 scripts/schedule_render.py --format launchd --only revops-watchdog-daily
    python3 scripts/schedule_render.py --format routine --only chief-of-staff-am
    python3 scripts/schedule_render.py --list

crontab  — one commented line per entry (uncomment to enable). Uses CRON_TZ where supported.
launchd  — a complete com.gtm-fleet.<name>.plist on stdout (StartCalendarInterval from the cron fields).
routine  — the prompt + cadence you would paste into a Claude Code cloud routine (no local machine).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable


def load():
    data = yaml.safe_load((PLUGIN_ROOT / "schedule.yaml").read_text())
    defaults = data.get("defaults", {})
    entries = []
    for e in data.get("entries", []):
        merged = dict(defaults)
        merged.update(e)
        entries.append(merged)
    return entries


def cron_fields(cron: str):
    minute, hour, dom, month, dow = cron.split()
    return minute, hour, dom, month, dow


def render_crontab(entries):
    out = ["# gtm-fleet schedule (all entries disabled — copy the lines you want into `crontab -e`)",
           f"# cwd + venv are explicit so cron's minimal environment works. FLEET_ROOT defaults to the plugin root.",
           "SHELL=/bin/bash", ""]
    tz = None
    for e in entries:
        if e.get("tz") != tz:
            tz = e["tz"]
            out.append(f"CRON_TZ={tz}")
        cmd = f"cd {PLUGIN_ROOT} && {PYTHON} scripts/tick.py --agent {e['agent']} --mode {e['mode']} >> state/working/tick-{e['name']}.log 2>&1"
        prefix = "" if e.get("enabled") else "# "
        out.append(f"{prefix}{e['cron']} {cmd}   # {e['name']}: {e.get('notes', '')[:70]}")
    return "\n".join(out) + "\n"


def render_launchd(e):
    minute, hour, dom, month, dow = cron_fields(e["cron"])
    intervals = []
    dows = range(0, 7) if dow == "*" else ([int(x) for x in dow.split(",")] if "," in dow else
                                             list(range(int(dow.split("-")[0]), int(dow.split("-")[1]) + 1)) if "-" in dow else [int(dow)])
    for d in dows:
        intervals.append(f"    <dict><key>Weekday</key><integer>{d}</integer><key>Hour</key><integer>{int(hour)}</integer><key>Minute</key><integer>{int(minute)}</integer></dict>")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.gtm-fleet.{e['name']}</string>
  <key>ProgramArguments</key>
  <array>
    <string>{PYTHON}</string>
    <string>{PLUGIN_ROOT}/scripts/tick.py</string>
    <string>--agent</string><string>{e['agent']}</string>
    <string>--mode</string><string>{e['mode']}</string>
  </array>
  <key>WorkingDirectory</key><string>{PLUGIN_ROOT}</string>
  <key>EnvironmentVariables</key>
  <dict><key>FLEET_ROOT</key><string>{PLUGIN_ROOT}</string><key>PATH</key><string>/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:{Path.home()}/.local/bin</string></dict>
  <key>StartCalendarInterval</key>
  <array>
{chr(10).join(intervals)}
  </array>
  <key>StandardOutPath</key><string>{PLUGIN_ROOT}/state/working/tick-{e['name']}.log</string>
  <key>StandardErrorPath</key><string>{PLUGIN_ROOT}/state/working/tick-{e['name']}.log</string>
  <key>RunAtLoad</key><false/>
</dict>
</plist>
<!-- {e['name']}: {e.get('notes', '')} — install with `launchctl load ~/Library/LaunchAgents/com.gtm-fleet.{e['name']}.plist` (timezone {e['tz']} is the machine's) -->
"""


def render_routine(e):
    return f"""# Claude Code cloud routine — {e['name']}
Cadence: cron `{e['cron']}` ({e['tz']})
Repository: this fleet's state repo (set FLEET_REMOTE/FLEET_BRANCH so commits land on a branch the rest of the fleet reads)
Plugin: gtm-fleet (install from the repo's .claude-plugin/marketplace.json)

Prompt:
  /gtm-fleet:{e['agent']} {e['mode']}

Notes: {e.get('notes', '')}
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--format", choices=("crontab", "launchd", "routine"), default="crontab")
    ap.add_argument("--only", help="entry name")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    entries = load()
    if args.list:
        for e in entries:
            print(f"{e['name']:<22} {e['agent']:<10} {e['mode']:<8} {e['cron']:<14} {e['tz']}  enabled={e.get('enabled', False)}")
        return 0
    if args.only:
        entries = [e for e in entries if e["name"] == args.only]
        if not entries:
            sys.exit(f"no entry named {args.only!r} (try --list)")
    if args.format == "crontab":
        print(render_crontab(entries), end="")
    elif args.format == "launchd":
        if len(entries) != 1:
            sys.exit("--format launchd needs --only <name> (one plist per entry)")
        print(render_launchd(entries[0]), end="")
    else:
        for e in entries:
            print(render_routine(e))
    return 0


if __name__ == "__main__":
    sys.exit(main())
