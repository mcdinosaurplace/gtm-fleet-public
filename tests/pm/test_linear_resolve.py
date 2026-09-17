"""Tests for scripts/pm/linear_resolve.py — ref detection + conservative name matching."""
from scripts.pm.linear_resolve import detect_refs, resolve, score_candidates

CANDS = [
    {"id": "proj-mops", "name": "MOPS Inbox and New Requests", "type": "project", "due_date": "2026-07-01"},
    {"id": "proj-web", "name": "Website Repositioning", "type": "project", "due_date": "2026-08-01"},
    {"id": "iss-1", "name": "Refresh pricing meta", "type": "issue", "due_date": None},
]


def test_detect_issue_key():
    refs = detect_refs("finish MAR-7076 this week")
    assert refs == [{"raw": "MAR-7076", "kind": "issue_key", "key": "MAR-7076"}]


def test_detect_project_url():
    refs = detect_refs("https://linear.app/orrery/project/mops-inbox-and-new-requests-000000000000/overview")
    assert refs[0]["kind"] == "project_url"
    assert refs[0]["slug"].startswith("mops-inbox-and-new-requests")


def test_detect_issue_url_not_double_counted():
    refs = detect_refs("see https://linear.app/orrery/issue/MAR-7076")
    assert len(refs) == 1 and refs[0]["kind"] == "issue_url" and refs[0]["key"] == "MAR-7076"


def test_resolve_by_ref():
    r = resolve("finish MAR-7076", CANDS)
    assert r["resolution"] == "by_ref"


def test_resolve_by_name_exact():
    r = resolve("MOPS Inbox and New Requests", CANDS)
    assert r["resolution"] == "by_name"
    assert r["match"]["id"] == "proj-mops"


def test_resolve_by_name_substring():
    r = resolve("working on MOPS Inbox and New Requests this week", CANDS)
    assert r["resolution"] == "by_name" and r["match"]["id"] == "proj-mops"


def test_resolve_needs_model_low_overlap():
    r = resolve("the new requests inbox", CANDS)   # 0.5 Jaccard, below threshold
    assert r["resolution"] == "needs_model"
    assert any(c["id"] == "proj-mops" for c in r["shortlist"])


def test_resolve_needs_model_vague():
    assert resolve("synced with the team and shipped things", CANDS)["resolution"] == "needs_model"


def test_substring_respects_word_boundary():
    # "Web" must not spuriously substring-match "website work"
    r = resolve("website work", [{"id": "w", "name": "Web", "type": "project", "due_date": None}])
    assert r["resolution"] == "needs_model"


def test_score_ordering():
    ranked = score_candidates("MOPS Inbox and New Requests", CANDS)
    assert ranked[0]["candidate"]["id"] == "proj-mops"
    assert ranked[0]["exact"] is True
