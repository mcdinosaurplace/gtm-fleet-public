#!/usr/bin/env python3
"""
profile_render.py — render the tokenized base kit for one profile.

    python3 scripts/profile_render.py --profile orrery [--out build/orrery] [--check]

What it does
  1. copies the kit (minus state/, wbr/, localwork/, build/, .git, .venv, tests, private files) to --out
  2. substitutes every profile token ({{UPPER_CASE}} and {{company_slug}}) from
     profiles/<name>/profile.yaml + connectors.yaml in every text file
  3. copies profiles/<name>/overrides/<relpath> over the rendered tree (whole-file replace)
  4. fails (exit 2) if any profile token is still unresolved — the token set is the contract

--check only reports which tokens the base kit uses vs. which the profile defines.
Lowercase {{placeholders}} (e.g. {{url}}, {{topic}}) are runtime template variables
used by skills and are deliberately left alone.
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

import yaml

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
TOKEN_RE = re.compile(r"\{\{([A-Z][A-Z0-9_]+|company_slug)\}\}")
SKIP = {".git", ".venv", "build", "__pycache__", ".pytest_cache", "node_modules", "state", "tests",
        "localwork", "wbr"}  # localwork/ + wbr/ are run-time state: never template them into a render
BINARY = {".png", ".jpg", ".jpeg", ".gif", ".db", ".zip", ".pdf", ".pyc", ".ico", ".woff", ".woff2", ".ttf", ".otf"}
# Uppercase placeholders that are NOT profile tokens: template slots in content templates
# and the words this tooling uses to describe tokens.
IGNORE_TOKENS = {"H2", "H3", "TBD", "TOKEN", "TOKENS", "UPPER_CASE", "TODAY", "NOW", "MONDAY"}
SKIP_FILES = {"scripts/profile_render.py", "scripts/sanitize/apply.py", "scripts/sanitize/verify.py",
              "scripts/sanitize/replace_map.example.yaml", "scripts/sanitize/README.md"}


def load_tokens(profile: str) -> dict[str, str]:
    pdir = PLUGIN_ROOT / "profiles" / profile
    if not pdir.is_dir():
        sys.exit(f"profile not found: {pdir}")
    tokens: dict[str, str] = {}
    for fn in ("profile.yaml", "connectors.yaml"):
        f = pdir / fn
        if f.exists():
            data = yaml.safe_load(f.read_text()) or {}
            tokens.update({k: str(v) for k, v in (data.get("tokens") or {}).items()})
    return tokens


def iter_text_files(root: Path):
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in SKIP for part in rel.parts) or rel.parts[0] == "profiles" or rel.as_posix() in SKIP_FILES:
            continue
        if p.suffix.lower() in BINARY:
            continue
        try:
            head = p.read_bytes()[:4096]
        except OSError:
            continue
        if b"\x00" in head:
            continue
        yield p


def tokens_used(root: Path) -> dict[str, set[str]]:
    used: dict[str, set[str]] = {}
    for p in iter_text_files(root):
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in TOKEN_RE.finditer(text):
            if m.group(1) not in IGNORE_TOKENS:
                used.setdefault(m.group(1), set()).add(p.relative_to(root).as_posix())
    return used


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check", action="store_true", help="report token coverage only")
    args = ap.parse_args()

    tokens = load_tokens(args.profile)
    used = tokens_used(PLUGIN_ROOT)
    missing = sorted(t for t in used if t not in tokens)
    unused = sorted(t for t in tokens if t not in used)
    if args.check or missing:
        print(f"profile={args.profile}: {len(tokens)} tokens defined, {len(used)} used in kit")
        for t in missing:
            print(f"  MISSING {t}  (used in {', '.join(sorted(used[t])[:3])}{'…' if len(used[t]) > 3 else ''})")
        for t in unused:
            print(f"  unused  {t}")
        if missing:
            return 2
        if args.check:
            print("OK: every token used by the kit is defined")
            return 0

    out = Path(args.out or (PLUGIN_ROOT / "build" / args.profile)).resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for p in sorted(PLUGIN_ROOT.rglob("*")):
        rel = p.relative_to(PLUGIN_ROOT)
        if any(part in SKIP for part in rel.parts) or rel.parts[0] == "profiles":
            continue
        dst = out / rel
        if p.is_dir():
            dst.mkdir(parents=True, exist_ok=True)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dst)
    # state/ skeleton (identity + migrations are part of a runnable fleet; journals/db come from the seeder)
    for sub in ("state/identity", "state/working/migrations", "state/working/queries"):
        src = PLUGIN_ROOT / sub
        if src.is_dir():
            shutil.copytree(src, out / sub, dirs_exist_ok=True)
    for sub in ("state/journal", "state/pending", "state/published", "state/working/briefs", "state/working/google", "wbr"):
        (out / sub).mkdir(parents=True, exist_ok=True)
        (out / sub / ".gitkeep").touch()
    if (PLUGIN_ROOT / "state/working/schema.sql").exists():
        shutil.copy2(PLUGIN_ROOT / "state/working/schema.sql", out / "state/working/schema.sql")

    n_files = n_subs = 0
    for p in iter_text_files(out):
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new, n = TOKEN_RE.subn(lambda m: tokens.get(m.group(1), m.group(0)), text)
        if n:
            p.write_text(new, encoding="utf-8")
            n_files += 1
            n_subs += n
    overrides = PLUGIN_ROOT / "profiles" / args.profile / "overrides"
    n_over = 0
    if overrides.is_dir():
        for p in overrides.rglob("*"):
            if p.is_file():
                dst = out / p.relative_to(overrides)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dst)
                n_over += 1
    left = tokens_used(out)
    print(f"rendered {args.profile} → {out}: {n_subs} substitutions in {n_files} files, {n_over} override files")
    if left:
        for t, files in left.items():
            print(f"  UNRESOLVED {t} in {sorted(files)[:3]}")
        return 2
    print("OK: 0 unresolved tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
