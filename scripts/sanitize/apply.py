#!/usr/bin/env python3
"""
apply.py — map-driven, re-runnable sanitization pass.

Applies an ordered replace map (YAML) to every text file under --root:

    python3 scripts/sanitize/apply.py --map <replace_map.yaml> --root . [--dry-run]
           [--renames-only] [--report <report.md>]

Map format (see scripts/sanitize/replace_map.example.yaml):

    renames:                       # filesystem renames, applied first (paths relative to root)
      - {from: "context/Old Name.yaml", to: "context/new-name.yaml"}
    concrete_paths: ["tests/**", "state/**"]   # globs where `concrete` replacements are used
    code_extensions: [".py", ".sql", ...]       # extensions where `code` replacements are used
    rules:                         # applied top-to-bottom, per file
      - id: repo-url
        find: "contact2@example.com:org/repo.git"     # literal  (or: regex: '...')
        replace: "{{REPO_URL}}"                 # default replacement (prose)
        code: "https://example.invalid/repo"    # optional: used in code files
        concrete: "Maya Lindqvist"              # optional: used in concrete_paths
        paths: ["tests/**"]                     # optional: restrict rule to globs
        review: true                            # optional: list every hit in the report
        type: flag | email_map | renumber       # optional special rule types

Special types:
  flag       — report only, never replaces (regex required)
  email_map  — any email not matching `allow` domains → contact{N}@example.com (deterministic)
  renumber   — regex with one numeric group → replaced by a deterministic renumbering

Design notes: idempotent (a second run reports 0 changes); never touches binaries
(extension blocklist + NUL sniff); quotes YAML scalars that start with `{{` or `#`
so the files still parse; the map itself may contain sensitive terms, so keep it
outside the repository (the kit ships only replace_map.example.yaml).
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path

import yaml

TEXT_EXT = {
    ".md", ".txt", ".yaml", ".yml", ".json", ".py", ".sql", ".sh", ".mmd", ".mermaid",
    ".csv", ".html", ".svg", ".js", ".ts", ".tsx", ".mjs", ".toml", ".cfg", ".ini",
    ".env", ".example", ".gitignore", ".gitkeep", ".plist", ".xml", ".css", ".mcp",
}
BINARY_EXT = {
    ".png", ".jpg", ".jpeg", ".gif", ".db", ".zip", ".plugin", ".skill", ".docx",
    ".pdf", ".pyc", ".ico", ".woff", ".woff2", ".ttf", ".otf", ".sqlite",
}
SKIP_DIRS = {".git", "build", ".venv", "__pycache__", ".pytest_cache", "node_modules"}
SKIP_FILES = {"state/working/demo-mcp.resolved.json"}  # generated locally; absolute paths by design
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def is_text_file(p: Path) -> bool:
    if p.suffix.lower() in BINARY_EXT:
        return False
    if p.suffix.lower() in TEXT_EXT or p.suffix == "":
        try:
            head = p.read_bytes()[:8192]
        except OSError:
            return False
        return b"\x00" not in head
    return False


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if is_text_file(p):
            yield p


def match_any(rel: str, globs) -> bool:
    return any(fnmatch.fnmatch(rel, g) for g in (globs or []))


class Stats:
    def __init__(self):
        self.per_rule: dict[str, int] = {}
        self.review: list[str] = []
        self.flags: list[str] = []
        self.changed_files: list[str] = []
        self.renamed: list[str] = []
        self.email_map: dict[str, str] = {}


def apply_rules(text: str, rel: str, rules, cfg, stats: Stats) -> str:
    is_code = Path(rel).suffix.lower() in set(cfg.get("code_extensions", []))
    is_concrete = match_any(rel, cfg.get("concrete_paths", []))
    for rule in rules:
        rid = rule["id"]
        if rule.get("paths") and not match_any(rel, rule["paths"]):
            continue
        rtype = rule.get("type", "replace")
        if rtype != "email_map":
            pattern = re.compile(rule["regex"]) if "regex" in rule else re.compile(re.escape(rule["find"]))

        if rtype == "flag":
            for m in pattern.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                stats.flags.append(f"{rid}\t{rel}:{line}\t{m.group(0)}")
            continue

        if rtype == "email_map":
            allow = tuple(d.lower() for d in rule.get("allow", []))

            def email_sub(m):
                addr = m.group(0)
                dom = addr.split("@", 1)[1].lower()
                if dom.endswith(allow) or "{{" in addr:
                    return addr
                if addr not in stats.email_map:
                    stats.email_map[addr] = f"contact{len(stats.email_map) + 1}@example.com"
                stats.per_rule[rid] = stats.per_rule.get(rid, 0) + 1
                return stats.email_map[addr]

            text = EMAIL_RE.sub(email_sub, text)
            continue

        if rtype == "renumber":
            base = int(rule.get("base", 1000))
            mod = int(rule.get("mod", 900))
            mult = int(rule.get("mult", 37))

            def renum(m):
                n = int(m.group(1))
                stats.per_rule[rid] = stats.per_rule.get(rid, 0) + 1
                return m.group(0)[: m.start(1) - m.start(0)] + str(base + (n * mult) % mod)

            text = pattern.sub(renum, text)
            continue

        # plain replace
        if is_concrete and "concrete" in rule:
            repl = rule["concrete"]
        elif is_code and "code" in rule:
            repl = rule["code"]
        else:
            repl = rule["replace"]
        if "regex" not in rule:
            repl_fn = lambda m, r=repl: r  # noqa: E731 — literal, no backrefs
        else:
            repl_fn = lambda m, r=repl: m.expand(r)  # noqa: E731

        def counting(m, rf=repl_fn, rid=rid, review=rule.get("review", False)):
            stats.per_rule[rid] = stats.per_rule.get(rid, 0) + 1
            if review:
                line = text.count("\n", 0, m.start()) + 1
                ctx = text[max(0, m.start() - 40): m.end() + 40].replace("\n", " ")
                stats.review.append(f"{rid}\t{rel}:{line}\t…{ctx}…")
            return rf(m)

        text = pattern.sub(counting, text)
    return text


YAML_KEY_VALUE = re.compile(r"^(\s*(?:- )?[^#\s][^:\n]*:\s+)(\{\{.*|#[0-9A-Fa-f]{3,8}\b.*)$")
YAML_LIST_ITEM = re.compile(r"^(\s*- )(\{\{.*|#[0-9A-Fa-f]{3,8}\b.*)$")


TOKEN_IN_FLOW = re.compile(r"\{\{[A-Za-z_]+\}\}")


def quote_flow_tokens(line: str) -> str:
    """Quote unquoted flow-collection scalars that contain a {{TOKEN}} ([a, {{X}}] / {k: {{X}} y})."""
    pos = 0
    while True:
        m = TOKEN_IN_FLOW.search(line, pos)
        if not m:
            return line
        left = m.start()
        while left > 0 and line[left - 1] not in "[{,":
            if line[left - 1] == " " and left >= 2 and line[left - 2] == ":":
                break
            left -= 1
        right = m.end()
        while right < len(line) and line[right] not in ",]}":
            right += 1
        raw = line[left:right]
        span = raw.strip()
        if span.startswith(('"', "'")) or not span:
            pos = right
            continue
        lead = raw[: len(raw) - len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        quoted = f'{lead}"{span.replace(chr(34), chr(92) + chr(34))}"{trail}'
        line = line[:left] + quoted + line[right:]
        pos = left + len(quoted)


def quote_yaml_scalars(text: str) -> str:
    out = []
    for line in text.split("\n"):
        m = YAML_KEY_VALUE.match(line) or YAML_LIST_ITEM.match(line)
        if m and not m.group(2).startswith(('"', "'")):
            val = m.group(2).rstrip()
            # keep trailing YAML comments outside the quotes when obvious
            comment = ""
            if "  #" in val:
                val, comment = val.split("  #", 1)
                comment = "  #" + comment
            line = f'{m.group(1)}"{val.replace(chr(34), chr(92) + chr(34))}"{comment}'
        elif "{{" in line and ("[" in line or "{ " in line) and not line.lstrip().startswith("#"):
            line = quote_flow_tokens(line)
        out.append(line)
    return "\n".join(out)


def do_renames(root: Path, renames, stats: Stats, dry: bool):
    for r in renames or []:
        src = root / r["from"]
        dst = root / r["to"]
        if not src.exists() or dst.exists():
            continue  # already renamed on a previous run (or the destination is in use)
        stats.renamed.append(f"{r['from']} -> {r['to']}")
        if not dry:
            dst.parent.mkdir(parents=True, exist_ok=True)
            src.rename(dst)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--map", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--report")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--renames-only", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    cfg = yaml.safe_load(Path(args.map).read_text())
    stats = Stats()

    do_renames(root, cfg.get("renames"), stats, args.dry_run)
    if not args.renames_only:
        rules = cfg.get("rules", [])
        for p in iter_files(root):
            rel = p.relative_to(root).as_posix()
            if rel in SKIP_FILES:
                continue
            try:
                original = p.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            new = apply_rules(original, rel, rules, cfg, stats)
            if p.suffix.lower() in {".yaml", ".yml"}:
                new = quote_yaml_scalars(new)
            if new != original:
                stats.changed_files.append(rel)
                if not args.dry_run:
                    p.write_text(new, encoding="utf-8")

    total = sum(stats.per_rule.values())
    lines = [f"# sanitize report — root={root}", ""]
    lines.append(f"renames: {len(stats.renamed)}")
    lines += [f"  {r}" for r in stats.renamed]
    lines.append(f"\nfiles changed: {len(stats.changed_files)}")
    lines.append(f"replacements: {total}")
    lines.append("\n## per rule")
    for rid, n in sorted(stats.per_rule.items(), key=lambda kv: -kv[1]):
        lines.append(f"  {n:6d}  {rid}")
    if stats.email_map:
        lines.append("\n## email map")
        lines += [f"  {k} -> {v}" for k, v in stats.email_map.items()]
    lines.append(f"\n## review hits ({len(stats.review)})")
    lines += [f"  {r}" for r in stats.review]
    lines.append(f"\n## flags ({len(stats.flags)})")
    lines += [f"  {f}" for f in stats.flags]
    report = "\n".join(lines) + "\n"
    if args.report and not args.dry_run:
        Path(args.report).write_text(report)
    print(report if args.report is None or args.dry_run else report.split("\n## per rule")[0])
    print(f"{total} changes{' (dry-run)' if args.dry_run else ''}" if total else "0 changes (idempotent)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
