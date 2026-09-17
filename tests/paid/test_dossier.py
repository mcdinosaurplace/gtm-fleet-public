"""Golden tests for scripts/paid/dossier.py (build plan Block A2).

Pins the dossier's section structure and byte-stable rendering. The full output
is compared against a committed golden (tests/paid/fixtures/dossier_basic.md);
regenerate it deliberately via `_regen_golden()` if the format changes.

Runs under pytest (future CI gate) AND standalone via
`python3 tests/paid/test_dossier.py`.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # repo root (standalone run)

from scripts.paid.dossier import (  # noqa: E402
    render_dossier,
    write_dossier,
)

GOLDEN = Path(__file__).resolve().parent / "fixtures" / "dossier_basic.md"

# Canonical fixture: one move in each bucket, plus a creative move that already
# has a Linear ref (post-greenlight) to exercise the clickable-link path.
BASIC_DOSSIER = {
    "date_range": "Jun 2-15, 2026",
    "dossier_date": "2026-06-16",
    "objective": "Efficiency",
    "thesis": "Cut competitor-term waste; protect Nonbrand — Incident Mgmt volume.",
    "confidence": "Medium",
    "wow_snapshot": [
        {"metric": "Spend", "last_week": "$1,240", "this_week": "$1,080", "delta": "-13%"},
        {"metric": "CPL", "last_week": "$62", "this_week": "$74", "delta": "+19%"},
    ],
    "campaign_health": [
        {"tier": "🔍", "campaign": "Search - Competitors", "metric": "CPL",
         "delta": "+41%", "diagnosis": "CPL spike, cause unknown — investigate first"},
        {"tier": "🟢", "campaign": "Nonbrand — Incident Mgmt", "metric": "Conv. rate",
         "delta": "+4%", "diagnosis": "stable, within range"},
    ],
    "moves": [
        {"bucket": "auto_3a", "platform": "google_ads", "op_type": "add_negative",
         "campaign_name": "Search - Generic", "summary": "Negate 'free crm'",
         "reason": "add_negative is additive/structure-only on Google Ads",
         "expected_effect": "cuts ~$40/wk wasted spend", "reversal_if": "CTR drops >15%"},
        {"bucket": "human_3b", "platform": "google_ads", "op_type": "budget",
         "campaign_name": "Nonbrand — Incident Mgmt", "summary": "Shift $1.5k/wk into Nonbrand — Incident Mgmt",
         "reason": "'budget' is always human-applied (budget/pause/strategy/cross-channel)",
         "change": "raise weekly budget $3,000 -> $4,500"},
        {"bucket": "creative", "platform": "google_ads", "op_type": "creative",
         "campaign_name": "Search - Competitors", "summary": "Founder-POV RSA refresh",
         "reason": "involves new/changed ad copy — copy review required",
         "linear_ref": "MAR-7076"},
    ],
    "budget_view": "Google: $310/day across 4 campaigns. LinkedIn: $0 (paused). "
                   "All budget changes are 3b.",
    "rollback": [
        "Global kill: set PERFORMANCE_MARKETER_EXECUTE=off to disable all mutates.",
        "Each 3a change logs its prior value; one-command rollback within 72h.",
    ],
    "hypotheses": [
        "Negating 'free crm' cuts wasted spend ~$40/wk with no CTR loss.",
        "Nonbrand — Incident Mgmt budget lift restores lost impression share within a week.",
    ],
}


def test_render_is_byte_stable():
    assert render_dossier(BASIC_DOSSIER) == render_dossier(BASIC_DOSSIER)


def test_render_matches_golden():
    assert GOLDEN.exists(), f"golden missing — run _regen_golden() ({GOLDEN})"
    assert render_dossier(BASIC_DOSSIER) == GOLDEN.read_text()


def test_section_headers_in_order():
    out = render_dossier(BASIC_DOSSIER)
    headers = [
        "# Paid Optimization Dossier",
        "## WoW Snapshot",
        "## Campaign Health",
        "## Proposed Moves",
        "### 🟢 Auto on greenlight",
        "### 🟠 Human-applied",
        "### ✍️ Blocked on creative review",
        "## Budget View (read-only)",
        "## Rollback / Abort",
        "## Next-Week Hypotheses",
    ]
    positions = [out.find(h) for h in headers]
    assert all(p != -1 for p in positions), f"missing header: {positions}"
    assert positions == sorted(positions), "headers out of order"


def test_auto_move_renders_reversal_clause():
    out = render_dossier(BASIC_DOSSIER)
    assert "reversal if CTR drops >15%" in out


def test_creative_renders_clickable_linear_link():
    out = render_dossier(BASIC_DOSSIER)
    assert "[MAR-7076](https://linear.app/orrery/issue/MAR-7076)" in out


def test_creative_without_ref_shows_task_on_greenlight():
    d = dict(BASIC_DOSSIER)
    d["moves"] = [{"bucket": "creative", "platform": "google_ads", "op_type": "creative",
                   "campaign_name": "X", "summary": "New RSA"}]
    out = render_dossier(d)
    assert "task created on greenlight" in out
    assert "linear.app" not in out


def test_empty_bucket_shows_placeholder():
    d = dict(BASIC_DOSSIER)
    d["moves"] = [m for m in BASIC_DOSSIER["moves"] if m["bucket"] != "human_3b"]
    out = render_dossier(d)
    # The human-applied section should show the placeholder.
    human_section = out.split("### 🟠 Human-applied")[1].split("### ✍️")[0]
    assert "_None this run._" in human_section


def test_ends_with_single_newline():
    out = render_dossier(BASIC_DOSSIER)
    assert out.endswith("\n") and not out.endswith("\n\n")


def test_write_dossier_path_and_content():
    with tempfile.TemporaryDirectory() as tmp:
        pend, pub = Path(tmp) / "pending", Path(tmp) / "published"
        path = write_dossier(BASIC_DOSSIER, pending_root=pend, published_root=pub)
        assert path.name == "2026-06-16-optimization-dossier.md"
        assert path.parent == pend / "optimization_dossiers"
        assert path.read_text() == render_dossier(BASIC_DOSSIER)


def test_write_dossier_supersedes_prior():
    # A second dossier moves the first out of pending into published.
    with tempfile.TemporaryDirectory() as tmp:
        pend, pub = Path(tmp) / "pending", Path(tmp) / "published"
        p1 = write_dossier(dict(BASIC_DOSSIER, dossier_date="2026-06-16"),
                           pending_root=pend, published_root=pub)
        p2 = write_dossier(dict(BASIC_DOSSIER, dossier_date="2026-06-23"),
                           pending_root=pend, published_root=pub)
        pend_md = sorted(p.name for p in (pend / "optimization_dossiers").glob("*.md"))
        pub_md = sorted(p.name for p in (pub / "optimization_dossiers").glob("*.md"))
        assert pend_md == ["2026-06-23-optimization-dossier.md"]
        assert pub_md == ["2026-06-16-optimization-dossier.md"]
        assert not p1.exists() and p2.exists()


def test_trigger_reason_renders_when_present():
    d = dict(BASIC_DOSSIER)
    d["trigger_reason"] = "1 HIGH anomaly(ies) — Zero spend on Nonbrand — Incident Mgmt"
    out = render_dossier(d)
    assert "**Triggered by:** 1 HIGH anomaly(ies) — Zero spend on Nonbrand — Incident Mgmt" in out


def test_no_trigger_reason_leaves_page_unchanged():
    # Absent trigger_reason must keep the page byte-identical to the golden.
    assert "Triggered by" not in render_dossier(BASIC_DOSSIER)


def _regen_golden():
    """Regenerate the committed golden from the current renderer + fixture."""
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN.write_text(render_dossier(BASIC_DOSSIER))
    print(f"wrote golden: {GOLDEN}")


if __name__ == "__main__":
    if "--regen" in sys.argv:
        _regen_golden()
        sys.exit(0)
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
    print(f"\n{'PASS' if not failures else 'FAIL'} — "
          f"{0 if not failures else failures} failure(s)")
    sys.exit(1 if failures else 0)
