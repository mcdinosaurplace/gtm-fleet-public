"""Tests for scripts/paid/publish.py — pending→published supersession.

Runs under pytest AND standalone via `python3 tests/paid/test_publish.py`.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root (standalone run)

from scripts.paid.publish import supersede  # noqa: E402


def _seed(pending_root, artifact_type, *names):
    d = Path(pending_root) / artifact_type
    d.mkdir(parents=True)
    (d / ".gitkeep").write_text("")
    for n in names:
        (d / n).write_text(n)


def test_supersede_moves_files_and_keeps_gitkeep():
    with tempfile.TemporaryDirectory() as tmp:
        pend, pub = Path(tmp) / "pending", Path(tmp) / "published"
        _seed(pend, "gtm_scorecards", "2026-08-05-gtm-scorecard.md")
        moved = supersede("gtm_scorecards", pending_root=pend, published_root=pub)
        assert [m.name for m in moved] == ["2026-08-05-gtm-scorecard.md"]
        assert (pend / "gtm_scorecards" / ".gitkeep").exists()          # gitkeep untouched
        assert not (pend / "gtm_scorecards" / "2026-08-05-gtm-scorecard.md").exists()
        assert (pub / "gtm_scorecards" / "2026-08-05-gtm-scorecard.md").read_text() == \
            "2026-08-05-gtm-scorecard.md"


def test_supersede_empty_pending_is_noop():
    with tempfile.TemporaryDirectory() as tmp:
        pend, pub = Path(tmp) / "pending", Path(tmp) / "published"
        _seed(pend, "optimization_dossiers")  # only .gitkeep present
        assert supersede("optimization_dossiers", pending_root=pend, published_root=pub) == []
        assert not (pub / "optimization_dossiers").exists()  # published dir not created for a no-op


def test_supersede_missing_dir_is_noop():
    with tempfile.TemporaryDirectory() as tmp:
        pend, pub = Path(tmp) / "pending", Path(tmp) / "published"
        assert supersede("change_lists", pending_root=pend, published_root=pub) == []


if __name__ == "__main__":
    failures = 0
    for name in sorted(k for k in dict(globals()) if k.startswith("test_")):
        fn = globals()[name]
        if not callable(fn):
            continue
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as e:  # noqa: BLE001
            failures += 1
            print(f"  FAIL {name}: {e}")
    print(f"\n{'PASS' if not failures else 'FAIL'} — {failures} failure(s)")
    sys.exit(1 if failures else 0)
