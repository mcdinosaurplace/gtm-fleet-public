#!/usr/bin/env python3
"""
verify.py — the zero-leak gate. Exit 0 only when nothing is found.

    python3 scripts/sanitize/verify.py --root . [--terms <terms.yaml>] [--secrets-only]
                                       [--skip-history] [--json] [--report <md>]

Scans, in order:
  1. text files (every extension, dotfiles included) for: secret patterns, emails outside the
     allowlist, absolute home paths, opaque MCP ids, live-looking ids (32-hex / UUID that are
     not zero-filled placeholders, Slack ids that are not DEMO ids), and every banned term
  2. file and directory names (banned terms, non-ASCII)
  3. archive members (.zip/.plugin/.skill/.docx) — names and text contents
  4. SQLite databases — every TEXT column of every table, plus a raw-bytes pass over the file
     (free pages keep deleted strings)
  5. every *.yaml parses
  6. git history, if the root is a repository (`git grep` across all revisions) — unless
     --skip-history, for terms that may live in this repo's history but not its tree

The committed terms.example.yaml holds only generic patterns. A sanitization of a
specific source needs its own private terms file (kept outside the repo) passed via
--terms; the Makefile's `verify` target refuses to run without one.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import re
import sqlite3
import subprocess
import sys
import zipfile
from pathlib import Path

import yaml

SKIP_DIRS = {".git", ".venv", "build", "__pycache__", ".pytest_cache", "node_modules",
             "demo-outbox", "localwork"}  # demo/agent scratch: local-only, may hold file:// paths
SKIP_FILES = {"state/working/demo-mcp.resolved.json"}  # generated locally; holds absolute paths by design
SKIP_FILE_GLOBS = ("state/working/last-session-*.json",)  # runner post-mortem artifacts
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".pyc", ".ico", ".woff", ".woff2", ".ttf", ".otf"}
ARCHIVE_EXT = {".zip", ".plugin", ".skill", ".docx"}
DB_EXT = {".db", ".sqlite", ".sqlite3"}

SECRET_PATTERNS = {
    "private-key": r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "json-private-key": r'"private_key"\s*:',
    "slack-token": r"xox[bap]-[0-9]{8,}-[0-9A-Za-z-]{8,}",
    "hubspot-pat": r"pat-na1-[0-9a-f-]{20,}",
    "google-client-secret": r"GOCSPX-[0-9A-Za-z_-]{10,}",
    "google-api-key": r"AIza[0-9A-Za-z_-]{30,}",
    "google-oauth-token": r"ya29\.[0-9A-Za-z_-]{20,}",
    "google-refresh-token": r"1//0[0-9A-Za-z_-]{20,}",
    "anthropic-key": r"sk-ant-[0-9A-Za-z_-]{20,}",
    "generic-bearer": r"Bearer [0-9A-Za-z_.-]{30,}",
}
ID_PATTERNS = {
    "abs-home-path": r"/Users/[a-z][a-z0-9_-]+/",
    "mcp-opaque-id": r"mcp__[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}__",
    "hex32-id": r"\b(?!0{16})[0-9a-f]{32}\b",
    "uuid": r"\b(?!0{8}-)[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
    "slack-id": r"\b[UCDW]0(?!DEMO)[0-9A-Z]{8,10}\b",
}
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
ALLOW_EMAIL_DEFAULT = ["example.com", "example.org", "example.invalid", "fleet.local", "anthropic.com", "google.com"]
ALLOW_HEX32 = {"00000000000000000000000000000299"}


class Findings:
    def __init__(self):
        self.items: list[dict] = []

    def add(self, kind: str, where: str, what: str):
        self.items.append({"kind": kind, "where": where, "what": what[:120]})

    def __len__(self):
        return len(self.items)


def load_terms(path: str | None):
    terms, allow = [], list(ALLOW_EMAIL_DEFAULT)
    if path:
        data = yaml.safe_load(Path(path).read_text()) or {}
        for t in data.get("terms", []):
            flags = 0 if t.get("case_sensitive") else re.I
            terms.append((t["id"], re.compile(t["regex"], flags)))
        allow += data.get("allow_emails", [])
    return terms, tuple(a.lower() for a in allow)


def is_text(p: Path) -> bool:
    if p.suffix.lower() in BINARY_EXT | ARCHIVE_EXT | DB_EXT:
        return False
    try:
        return b"\x00" not in p.read_bytes()[:8192]
    except OSError:
        return False


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in p.relative_to(root).parts):
            continue
        if p.is_file():
            yield p


def scan_text(label: str, text: str, f: Findings, terms, allow_emails, secrets_only: bool):
    for name, pat in SECRET_PATTERNS.items():
        for m in re.finditer(pat, text):
            f.add(f"secret:{name}", label, m.group(0))
    if secrets_only:
        return
    for m in EMAIL_RE.finditer(text):
        addr = m.group(0)
        dom = addr.split("@", 1)[1].lower()
        if not dom.endswith(allow_emails) and "{{" not in addr and "example" not in dom:
            f.add("email", label, addr)
    for name, pat in ID_PATTERNS.items():
        for m in re.finditer(pat, text):
            if name == "hex32-id" and m.group(0) in ALLOW_HEX32:
                continue
            if name in ("uuid", "hex32-id") and text[max(0, m.start() - 12):m.start()].endswith("session="):
                continue  # harness footers record the run's own session id
            f.add(f"id:{name}", label, m.group(0))
    for tid, rx in terms:
        for m in rx.finditer(text):
            f.add(f"term:{tid}", label, m.group(0))


def scan_root(root: Path, terms, allow_emails, secrets_only: bool, skip_history: bool = False) -> tuple[Findings, dict]:
    f = Findings()
    stats = {"files": 0, "archives": 0, "tables": 0, "yaml": 0}
    for p in iter_files(root):
        rel = p.relative_to(root).as_posix()
        if rel in SKIP_FILES or any(fnmatch.fnmatch(rel, g) for g in SKIP_FILE_GLOBS):
            continue
        if not secrets_only:
            if not rel.isascii():
                f.add("filename:non-ascii", rel, rel)
            for tid, rx in terms:
                if rx.search(rel):
                    f.add(f"filename:{tid}", rel, rel)
        suf = p.suffix.lower()
        if suf in ARCHIVE_EXT:
            stats["archives"] += 1
            try:
                with zipfile.ZipFile(p) as z:
                    for info in z.infolist():
                        for tid, rx in terms:
                            if rx.search(info.filename):
                                f.add(f"archive-member:{tid}", f"{rel}!{info.filename}", info.filename)
                        if info.file_size < 5_000_000:
                            data = z.read(info)
                            if b"\x00" not in data[:4096]:
                                scan_text(f"{rel}!{info.filename}", data.decode("utf-8", "ignore"), f, terms, allow_emails, secrets_only)
            except zipfile.BadZipFile:
                f.add("archive:unreadable", rel, "not a zip")
            continue
        if suf in DB_EXT:
            con = sqlite3.connect(f"file:{p}?mode=ro", uri=True)
            try:
                tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
                for t in tables:
                    stats["tables"] += 1
                    cols = [c[1] for c in con.execute(f'PRAGMA table_info("{t}")')]
                    for row in con.execute(f'SELECT rowid, * FROM "{t}"'):
                        for c, v in zip(["rowid"] + cols, row):
                            if isinstance(v, str) and v:
                                scan_text(f"{rel}:{t}.{c}#{row[0]}", v, f, terms, allow_emails, secrets_only)
            finally:
                con.close()
            # raw bytes (free pages)
            raw = p.read_bytes().decode("latin-1")
            for tid, rx in terms:
                for m in rx.finditer(raw):
                    f.add(f"db-raw:{tid}", rel, m.group(0))
            continue
        if not is_text(p):
            continue
        stats["files"] += 1
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        scan_text(rel, text, f, terms, allow_emails, secrets_only)
        if suf in {".yaml", ".yml"} and not secrets_only:
            stats["yaml"] += 1
            try:
                list(yaml.safe_load_all(text))
            except Exception as e:  # noqa: BLE001
                f.add("yaml:parse", rel, str(e).splitlines()[0])
    # git history
    if (root / ".git").exists() and terms and not secrets_only and not skip_history:
        revs = subprocess.run(["git", "-C", str(root), "rev-list", "--all"], capture_output=True, text=True)
        if revs.returncode == 0 and revs.stdout.strip():
            pattern = "|".join(rx.pattern for _, rx in terms)
            g = subprocess.run(["git", "-C", str(root), "grep", "-I", "-i", "-E", "-l", pattern] + revs.stdout.split(),
                               capture_output=True, text=True)
            for line in g.stdout.splitlines()[:50]:
                f.add("git-history", line, "banned term in a committed revision")
    return f, stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--terms", help="private terms yaml (see terms.example.yaml)")
    ap.add_argument("--secrets-only", action="store_true")
    ap.add_argument("--skip-history", action="store_true",
                    help="tree-only scanning for second-tier terms on the canonical repo")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--report")
    ap.add_argument("--max", type=int, default=200, help="max findings to print")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    terms, allow_emails = load_terms(args.terms)
    f, stats = scan_root(root, terms, allow_emails, args.secrets_only, args.skip_history)

    if args.json:
        print(json.dumps({"findings": f.items, "stats": stats}, indent=2))
    else:
        lines = []
        by_kind: dict[str, int] = {}
        for it in f.items:
            by_kind[it["kind"]] = by_kind.get(it["kind"], 0) + 1
        for it in f.items[: args.max]:
            lines.append(f"  {it['kind']:<28} {it['where']}  →  {it['what']}")
        summary = (f"{'OK' if not f.items else 'LEAK'}: {len(f)} findings across {stats['files']} files, "
                   f"{stats['tables']} tables, {stats['archives']} archives, {stats['yaml']} yaml"
                   + ("" if args.terms else "  (no --terms file: generic patterns only)"))
        if by_kind:
            lines.append("  by kind: " + ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())))
        out = "\n".join(lines + [summary])
        print(out)
        if args.report:
            Path(args.report).write_text("# verify report\n\n```\n" + out + "\n```\n")
    return 1 if f.items else 0


if __name__ == "__main__":
    sys.exit(main())
