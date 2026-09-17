#!/usr/bin/env python3
"""
compose_fleet.py — compose a bespoke client fleet from a fleet.yaml selection.

    python3 scripts/compose_fleet.py --fleet fleet.yaml [--out build/<plugin>]
                                     [--seed empty|demo] [--terms <private terms.yaml>]
                                     [--terms2 <second-tier terms.yaml>]

Renders the profile (scripts/profile_render.py), overlays the profile's identity notes,
prunes everything the selection left out (roster dirs, skills, constitutions, the
funnel-stats subagent, the Luma MCP server, schedule entries, preflight rows, the
CLAUDE.md registry, the fleet diagram), renames the plugin, writes the composed
fleet.yaml, seeds state, optionally runs the zero-leak gate, and prints a manifest
(also written to <out>/compose-manifest.json).

Overlay precedence (highest first): overrides/<relpath> → identity-notes/<agent>.md →
profile.yaml tokens → base. See docs/composer.md.

Exit 2 on a validation error, an unresolved token, a failed seed, or a gate finding.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
BASE_PLUGIN = "gtm-fleet"
AGENTS = ("chief-of-staff", "revops-watchdog", "performance-marketer", "scribe",
          "content-researcher", "content-producer", "brand-designer")
CAPABILITIES = ("funnel-stats", "luma-events")
OPERATOR_SKILLS = ("triage", "help-me")
# Auto-loaded knowledge skills (CLAUDE.md): always kept, whatever `skills` selects.
KNOWLEDGE_SKILLS = ("brand-voice", "content-creation", "campaign-planning",
                    "competitive-analysis", "performance-analytics", "gtm-ops")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
JOURNAL_HEADER = ('# {title}\n\nAppend-only journal. One `## <ISO-8601Z> | <label>` entry per '
                  'Tick; the harness reads the last header as its "since" marker.\n\n')
JOURNAL_TITLES = {"scribe": "Scribe — Journal"}
# (filename, title, agent that must be selected — None = always)
SHARED_JOURNALS = (
    ("handoffs.md", "Handoffs — fleet message bus (append-only)", None),
    ("ops-incidents.md", "Ops Incidents", None),
    ("chief-of-staff-meditations.md", "chief-of-staff — Evening Meditations", "chief-of-staff"),
    ("scribe_project_management.md", "Scribe — Project Management Journal", "scribe"),
)


def fail(msg: str):
    print(f"compose_fleet: {msg}", file=sys.stderr)
    sys.exit(2)


def one_shot_skills(root: Path) -> list[str]:
    """Skill dirs that are neither agent/capability routers, operator tools, nor knowledge."""
    reserved = set(AGENTS) | set(CAPABILITIES) | set(OPERATOR_SKILLS) | set(KNOWLEDGE_SKILLS)
    return sorted(p.name for p in (root / "skills").iterdir()
                  if (p / "SKILL.md").is_file() and p.name not in reserved)


def schedule_entries(root: Path) -> dict[str, str]:
    """schedule.yaml entry name → agent."""
    data = yaml.safe_load((root / "schedule.yaml").read_text()) or {}
    return {e["name"]: e["agent"] for e in (data.get("entries") or [])}


# ------------------------------------------------------------------ 1. validate

def load_fleet(path: Path) -> dict:
    """Validate a fleet.yaml and return the resolved selection (defaults filled in)."""
    if not path.is_file():
        fail(f"fleet file not found: {path} — pass --fleet <path to a fleet.yaml>")
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        fail(f"{path} must be a YAML mapping with name / profile / agents")

    name = str(data.get("name") or "").strip()
    if not SLUG_RE.match(name):
        fail(f"name {name!r} is not a slug — lowercase letters, digits and hyphens only (e.g. acme)")

    profile = str(data.get("profile") or "").strip()
    if not (PLUGIN_ROOT / "profiles" / profile).is_dir():
        avail = ", ".join(sorted(p.name for p in (PLUGIN_ROOT / "profiles").iterdir() if p.is_dir()))
        fail(f"profile {profile!r} not found under profiles/ — available: {avail}")

    agents = data.get("agents")
    if not isinstance(agents, list) or not agents:
        fail(f"agents must be a non-empty list — valid agents: {', '.join(AGENTS)}")
    for a in agents:
        if a not in AGENTS:
            fail(f"unknown agent {a!r} — valid agents: {', '.join(AGENTS)}")

    caps = data.get("capabilities") or []
    if not isinstance(caps, list):
        fail(f"capabilities must be a list — valid capabilities: {', '.join(CAPABILITIES)}")
    for c in caps:
        if c not in CAPABILITIES:
            fail(f"unknown capability {c!r} — valid capabilities: {', '.join(CAPABILITIES)}")

    skills = data.get("skills", "all")
    if skills != "all":
        valid = one_shot_skills(PLUGIN_ROOT)
        if not isinstance(skills, list):
            fail(f"skills must be the string 'all' or a list — valid one-shot skills: {', '.join(valid)}")
        for s in skills:
            if s not in valid:
                fail(f"unknown skill {s!r} — valid one-shot skills: {', '.join(valid)} "
                     "(the six knowledge skills and triage / help-me are always kept)")

    for key in ("connectors", "runner"):
        if data.get(key) is not None and not isinstance(data[key], dict):
            fail(f"{key} must be a mapping (it is recorded, not enforced)")

    sched = data.get("schedule") or {}
    if not isinstance(sched, dict):
        fail("schedule must be a mapping with an enabled_entries list")
    enabled = sched.get("enabled_entries") or []
    if not isinstance(enabled, list):
        fail("schedule.enabled_entries must be a list of schedule.yaml entry names")
    by_name = schedule_entries(PLUGIN_ROOT)
    for n in enabled:
        if n not in by_name:
            fail(f"unknown schedule entry {n!r} — valid entries: {', '.join(sorted(by_name))}")
        if by_name[n] not in agents:
            kept = sorted(k for k, v in by_name.items() if v in agents)
            fail(f"schedule entry {n!r} belongs to {by_name[n]!r}, which this fleet does not include — "
                 f"add that agent or enable one of: {', '.join(kept) or '(none)'}")

    return {
        "name": name,
        "plugin_name": name if name.endswith("-fleet") else f"{name}-fleet",
        "profile": profile,
        "agents": list(agents),
        "capabilities": list(caps),
        "skills": "all" if skills == "all" else list(skills),
        "connectors": data.get("connectors") or {},
        "runner": data.get("runner") or {},
        "enabled_entries": list(enabled),
    }


# ------------------------------------------------------------------ 3-4. overlays

def apply_identity_notes(profile_dir: Path, out: Path, agents) -> list[str]:
    """Append profiles/<p>/identity-notes/<agent>.md to the composed constitution.

    Skipped when the profile ships a whole-file override for that constitution:
    overrides win over identity notes.
    """
    applied = []
    for agent in agents:
        note = profile_dir / "identity-notes" / f"{agent}.md"
        target = out / "state" / "identity" / f"{agent}.md"
        override = profile_dir / "overrides" / "state" / "identity" / f"{agent}.md"
        if not note.is_file() or not target.is_file() or override.exists():
            continue
        target.write_text(target.read_text().rstrip("\n") + "\n\n---\n\n" + note.read_text().lstrip("\n"))
        applied.append(agent)
    return applied


# ------------------------------------------------------------------ 5. prune

def rm(out: Path, rel: str) -> list[str]:
    """Delete out/<rel>; return [rel] when something was there."""
    p = out / rel
    if p.is_dir():
        shutil.rmtree(p)
        return [rel]
    if p.exists():
        p.unlink()
        return [rel]
    return []


def drop_luma_mcp(out: Path):
    path = out / ".claude-plugin" / "plugin.json"
    data = json.loads(path.read_text())
    servers = data.get("mcpServers") or {}
    servers.pop("luma", None)
    if servers:
        data["mcpServers"] = servers
    else:
        data.pop("mcpServers", None)
    path.write_text(json.dumps(data, indent=2) + "\n")


def prune_schedule(out: Path, agents, enabled) -> list[str]:
    """Keep entries whose agent survived; enable exactly `enabled`. Comments are lost."""
    path = out / "schedule.yaml"
    data = yaml.safe_load(path.read_text()) or {}
    entries = [e for e in (data.get("entries") or []) if e.get("agent") in agents]
    for e in entries:
        e["enabled"] = e["name"] in enabled
    data["entries"] = entries
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=120))
    return [e["name"] for e in entries]


def prune_table_rows(path: Path, section: str, dropped):
    """Drop markdown rows whose first cell names a dropped agent/capability."""
    names = {d.lower() for d in dropped}
    kept, in_section = [], False
    for line in path.read_text().splitlines():
        if line.startswith("## "):
            in_section = line.strip().lower() == section.lower()
        if in_section and line.startswith("|") and line.split("|")[1].strip().strip("`*").lower() in names:
            continue
        kept.append(line)
    path.write_text("\n".join(kept) + "\n")


def prune_skill_prose(path: Path, pruned):
    """Remove the backticked names of pruned one-shot skills from the paragraph
    that follows the Agent Registry, repairing the commas it leaves behind."""
    blocks = path.read_text().split("\n\n")
    for i, block in enumerate(blocks):
        if not pruned or "one-shot marketing skills" not in block:
            continue
        for name in pruned:
            block = re.sub(r"`" + re.escape(name) + r"`(,[ ]*)?", "", block)
        block = re.sub(r"\(\s*,\s*", "(", re.sub(r",(\s*,)+", ",", block))
        blocks[i] = "\n".join(l.rstrip() for l in block.splitlines() if l.strip())
        path.write_text("\n\n".join(blocks))
        return


def prune_diagram(path: Path, dropped):
    """Drop every line naming a dropped agent, then any subgraph left with no body."""
    if not dropped:
        return
    pat = re.compile("|".join(rf"(?<![A-Za-z0-9_-]){re.escape(d)}(?![A-Za-z0-9_-])" for d in dropped), re.I)
    kept = [l for l in path.read_text().splitlines() if not pat.search(l)]
    out_lines, i = [], 0
    while i < len(kept):
        if kept[i].strip().startswith("subgraph "):
            j = i + 1
            while j < len(kept) and kept[j].strip() != "end":
                j += 1
            if j < len(kept) and not any(l.strip() for l in kept[i + 1:j]):
                i = j + 1
                continue
        out_lines.append(kept[i])
        i += 1
    path.write_text("\n".join(out_lines) + "\n")


# ------------------------------------------------------------------ 6-7. rename + config

def iter_text_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file() or p.suffix.lower() == ".db":
            continue
        try:
            if b"\x00" in p.read_bytes()[:4096]:
                continue
        except OSError:
            continue
        yield p


def rename_plugin(out: Path, plugin: str) -> int:
    n = 0
    for p in iter_text_files(out):
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if BASE_PLUGIN in text:
            p.write_text(text.replace(BASE_PLUGIN, plugin), encoding="utf-8")
            n += 1
    return n


def write_fleet_yaml(out: Path, sel: dict):
    doc = {
        "name": sel["plugin_name"],
        "profile": sel["profile"],
        "agents": sel["agents"],
        "capabilities": sel["capabilities"],
        "skills": sel["skills"],
        "connectors": sel["connectors"],
        "runner": sel["runner"],
        "schedule": {"enabled_entries": sel["enabled_entries"]},
    }
    (out / "fleet.yaml").write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120))


# ------------------------------------------------------------------ 8-9. seed + gate

def seed_empty(out: Path, agents) -> int:
    """Apply the composed kit's own migrations, then write header-only journals."""
    db = out / "state" / "working" / "fleet.db"
    db.parent.mkdir(parents=True, exist_ok=True)
    db.touch()
    code = (f"import sys; sys.path.insert(0, {str(out / 'scripts')!r}); "
            "import tick; tick.run_pending_migrations()")
    r = subprocess.run([sys.executable, "-c", code], cwd=str(out),
                       env=dict(os.environ, FLEET_ROOT=str(out)))
    if r.returncode != 0:
        fail("applying the composed kit's migrations failed — check "
             f"{out.name}/state/working/migrations/ and re-run")
    jd = out / "state" / "journal"
    jd.mkdir(parents=True, exist_ok=True)
    n = 0
    for a in agents:
        (jd / f"{a}.md").write_text(JOURNAL_HEADER.format(title=JOURNAL_TITLES.get(a, f"{a} — Journal")))
        n += 1
    for fn, title, needs in SHARED_JOURNALS:
        if needs and needs not in agents:
            continue
        (jd / fn).write_text(JOURNAL_HEADER.format(title=title))
        n += 1
    return n


def seed_demo(out: Path, profile: str):
    r = subprocess.run([sys.executable, str(out / "scripts" / "seed_demo_state.py"),
                        "--profile", profile, "--as-of", "yesterday", "--force"],
                       cwd=str(out), env=dict(os.environ, FLEET_ROOT=str(out)))
    if r.returncode != 0:
        fail(f"demo seed failed (exit {r.returncode}) — run "
             f"{out.name}/scripts/seed_demo_state.py by hand to see why, or use --seed empty")


def run_gate(out: Path, terms: Path) -> int:
    r = subprocess.run([sys.executable, str(PLUGIN_ROOT / "scripts" / "sanitize" / "verify.py"),
                        "--root", str(out), "--terms", str(terms)], capture_output=True, text=True)
    print(r.stdout.rstrip())
    if r.stderr.strip():
        print(r.stderr.rstrip(), file=sys.stderr)
    m = re.search(r"(\d+) findings", r.stdout)
    return int(m.group(1)) if m else (0 if r.returncode == 0 else 1)


# ------------------------------------------------------------------ main

def source_commit() -> str:
    try:
        r = subprocess.run(["git", "-C", str(PLUGIN_ROOT), "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=5)
        return r.stdout.strip() if r.returncode == 0 else "unknown"
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fleet", required=True, help="fleet.yaml describing the selection")
    ap.add_argument("--out", help="output directory (default build/<plugin-name>); rebuilt from scratch")
    ap.add_argument("--seed", choices=("empty", "demo"), default="empty")
    ap.add_argument("--terms", help="private terms yaml — runs the zero-leak gate over the composed tree")
    ap.add_argument("--terms2", help="second-tier terms yaml — a second gate run over the same tree")
    args = ap.parse_args()

    sel = load_fleet(Path(args.fleet).resolve())
    agents, caps, plugin = sel["agents"], sel["capabilities"], sel["plugin_name"]
    if args.seed == "demo" and set(agents) != set(AGENTS):
        fail("demo seed requires the full roster; use --seed empty")
    terms = Path(args.terms).resolve() if args.terms else None
    if terms and not terms.is_file():
        fail(f"terms file not found: {terms} — pass the private terms yaml or drop --terms")
    terms2 = Path(args.terms2).resolve() if args.terms2 else None
    if terms2 and not terms2.is_file():
        fail(f"terms file not found: {terms2} — pass the second-tier terms yaml or drop --terms2")
    out = Path(args.out or PLUGIN_ROOT / "build" / plugin).resolve()

    # 2. render the profile (tokens + whole-file overrides + state skeleton)
    r = subprocess.run([sys.executable, str(PLUGIN_ROOT / "scripts" / "profile_render.py"),
                        "--profile", sel["profile"], "--out", str(out)])
    if r.returncode != 0:
        fail(f"profile_render failed for profile {sel['profile']!r} (exit {r.returncode}) — define the "
             f"tokens it reported in profiles/{sel['profile']}/profile.yaml and re-run")

    # 3-4. identity-notes overlay, then the profile itself so the kit can reseed
    profile_dir = PLUGIN_ROOT / "profiles" / sel["profile"]
    notes = apply_identity_notes(profile_dir, out, agents)
    shutil.copytree(profile_dir, out / "profiles" / sel["profile"], dirs_exist_ok=True)

    # 5. prune everything the selection left out
    dropped_agents = [a for a in AGENTS if a not in agents]
    dropped = dropped_agents + [c for c in CAPABILITIES if c not in caps]
    pruned_one_shot = ([] if sel["skills"] == "all"
                       else [s for s in one_shot_skills(PLUGIN_ROOT) if s not in sel["skills"]])
    pruned = {"roster": [], "skills": [], "identity": [], "other": []}
    for x in dropped:
        pruned["roster"] += rm(out, f"roster/{x}")
        pruned["skills"] += rm(out, f"skills/{x}")
    for a in dropped_agents:
        pruned["identity"] += rm(out, f"state/identity/{a}.md")
        # companion identity files (e.g. scribe-pm.md, scribe-pm-cadence.yaml)
        for p in sorted((out / "state" / "identity").glob(f"{a}-*")):
            pruned["identity"] += rm(out, p.relative_to(out).as_posix())
    for s in pruned_one_shot:
        pruned["skills"] += rm(out, f"skills/{s}")
    if "funnel-stats" not in caps:
        pruned["other"] += rm(out, "agents/funnel-stats.md")
    if "luma-events" not in caps:
        pruned["other"] += rm(out, "scripts/luma_mcp.py")
        drop_luma_mcp(out)
        pruned["other"].append(".claude-plugin/plugin.json:mcpServers.luma")
    kept_entries = prune_schedule(out, agents, sel["enabled_entries"])
    prune_table_rows(out / "docs" / "mcp-preflight.md", "## Per-agent required connectors", dropped)
    prune_table_rows(out / "CLAUDE.md", "## Agent Registry", dropped)
    prune_skill_prose(out / "CLAUDE.md", pruned_one_shot)
    prune_diagram(out / "docs" / "agent-fleet-diagram.mermaid", dropped)

    # 6-7. rename the plugin, then write the composed kit's own config
    renamed = rename_plugin(out, plugin) if plugin != BASE_PLUGIN else 0
    write_fleet_yaml(out, sel)

    # 8. seed
    if args.seed == "demo":
        seed_demo(out, sel["profile"])
        n_journals = len(list((out / "state" / "journal").glob("*.md")))
    else:
        n_journals = seed_empty(out, agents)

    # 9. gate — one run per terms file provided
    findings = run_gate(out, terms) if terms else 0
    findings2 = run_gate(out, terms2) if terms2 else 0

    # 10. manifest + summary — the tier-1 keys never move; tier-2 keys appear only with --terms2
    gate = {"ran": bool(terms or terms2), "terms": terms.name if terms else None, "findings": findings}
    if terms2:
        gate["terms2"] = terms2.name
        gate["findings2"] = findings2
    manifest = {
        "plugin_name": plugin,
        "profile": sel["profile"],
        "composed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source_commit": source_commit(),
        "seed": args.seed,
        "agents": agents,
        "capabilities": caps,
        "skills": sel["skills"],
        "identity_notes_applied": notes,
        "pruned": pruned,
        "schedule": {"entries": kept_entries, "enabled": sel["enabled_entries"]},
        "connectors": sel["connectors"],
        "runner": sel["runner"],
        "gate": gate,
        "files": sum(1 for p in out.rglob("*") if p.is_file()) + 1,  # +1: this manifest
    }
    (out / "compose-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")

    n_pruned = sum(len(v) for v in pruned.values())
    kept_skills = "all" if sel["skills"] == "all" else f"{len(sel['skills'])} one-shot"
    print(f"\ncomposed {plugin} ← profile {sel['profile']} → {out}")
    print(f"  agents ({len(agents)}/{len(AGENTS)}): {', '.join(agents)}")
    print(f"  capabilities ({len(caps)}/{len(CAPABILITIES)}): {', '.join(caps) or '(none)'}")
    print(f"  skills: {kept_skills} kept + {len(KNOWLEDGE_SKILLS)} knowledge + {', '.join(OPERATOR_SKILLS)}")
    print(f"  pruned: {n_pruned} paths" + (f" · identity notes: {', '.join(notes)}" if notes else ""))
    print(f"  schedule: {len(kept_entries)} entries, enabled: {', '.join(sel['enabled_entries']) or '(none)'}")
    print(f"  seed {args.seed}: {n_journals} journals · rename: {renamed} files · {manifest['files']} files total")
    print(f"  gate: {f'{findings} findings (terms: {terms.name})' if terms else 'skipped (no --terms)'}")
    if terms2:
        print(f"  gate (tier-2): {findings2} findings (terms: {terms2.name})")
    print(f"  manifest: {out.name}/compose-manifest.json")
    if findings or findings2:
        fail(f"zero-leak gate found {findings + findings2} finding(s) in {out} — sanitize the source or extend "
             "the profile's overrides, then re-compose")
    print(f"next: claude plugin validate {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
