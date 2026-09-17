#!/usr/bin/env python3
"""scripts/paid/publish.py — pending→published supersession for performance-marketer artifacts.

When performance-marketer writes a NEW artifact of a given type, the previous pending file of
that type is *superseded*: moved to the mirror published/ folder. So
`docs/publications/pending/performance-marketer/<type>/` always holds exactly the current
artifact and `published/<type>/` is the archive of everything prior — the folder
itself is the source of truth for status (no "status:" frontmatter to keep in
sync).

The move is a plain filesystem move; git records it as a rename on the next
`add`, and the Tick's normal commit captures it. This module never calls git.

Used by:
  - `scripts/paid/dossier.write_dossier` (calls `supersede()` directly before it
    writes the new dossier)
  - the `performance-marketer:traffic-scorecard` and `performance-marketer:creative-optimizer` skills, via the
    CLI below, before they write their new draft:
        python3 scripts/paid/publish.py gtm_scorecards
"""
from pathlib import Path
import shutil
import sys

PENDING_ROOT = "docs/publications/pending/performance-marketer"
PUBLISHED_ROOT = "docs/publications/published/performance-marketer"

ARTIFACT_TYPES = (
    "optimization_dossiers",
    "gtm_scorecards",
    "creative_variations",
    "change_lists",
)


def supersede(artifact_type, pending_root=PENDING_ROOT, published_root=PUBLISHED_ROOT):
    """Move any existing pending file of `artifact_type` to the published mirror.

    Returns the list of destination Paths moved (empty if pending held nothing but
    a `.gitkeep`, or the pending dir does not exist). `.gitkeep` and non-files are
    left in place; the published dir is created only when there is something to
    move into it.
    """
    pending_dir = Path(pending_root) / artifact_type
    published_dir = Path(published_root) / artifact_type
    if not pending_dir.is_dir():
        return []
    moved = []
    for f in sorted(pending_dir.iterdir()):
        if not f.is_file() or f.name == ".gitkeep":
            continue
        published_dir.mkdir(parents=True, exist_ok=True)
        dest = published_dir / f.name
        shutil.move(str(f), str(dest))
        moved.append(dest)
    return moved


def main(argv):
    if len(argv) != 1 or argv[0] not in ARTIFACT_TYPES:
        print("usage: python3 scripts/paid/publish.py <artifact_type>\n"
              f"  artifact_type one of: {', '.join(ARTIFACT_TYPES)}", file=sys.stderr)
        return 2
    moved = supersede(argv[0])
    for m in moved:
        print(f"superseded -> {m}")
    if not moved:
        print(f"nothing to supersede in pending/{argv[0]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
