"""Tests for scripts/pm/linear_create.py — G2 accountability-driven Linear creation.

Pure-core coverage: keyword intent detection (+ the inferred/confirm-once flag), exact
dedup, payload assembly with fixed defaults, validation, and the idempotency decision.
"""
import pytest

from scripts.pm.linear_create import (
    build_payload,
    creation_action,
    dedup_match,
    detect_intent,
)


# ── detect_intent ────────────────────────────────────────────────────────────
def test_intent_link_existing_by_ref():
    r = detect_intent("MAR-7075 is right for the grow sync piece")
    assert r["intent"] == "link_existing" and r["inferred"] is False


def test_intent_link_existing_by_phrase():
    assert detect_intent("link it to the budgeting project")["intent"] == "link_existing"


def test_intent_incidental():
    assert detect_intent("incidental")["intent"] == "incidental"
    assert detect_intent("no need to track, it's untracked")["intent"] == "incidental"


def test_intent_roll_in():
    assert detect_intent("roll into agentic-skill-gaps")["intent"] == "roll_in"
    assert detect_intent("fold in with the hub")["intent"] == "roll_in"


def test_intent_create_project_explicit():
    r = detect_intent("track as a new project")
    assert r["intent"] == "create_project" and r["inferred"] is False


def test_intent_create_issue_explicit():
    r = detect_intent("track the other as a new ticket")
    assert r["intent"] == "create_issue" and r["inferred"] is False


def test_intent_bare_track_is_inferred_issue():
    # Bare "track it" with no kind signal -> create_issue but must confirm once.
    r = detect_intent("track it")
    assert r["intent"] == "create_issue" and r["inferred"] is True


def test_intent_bare_affirmative_is_inferred_issue():
    r = detect_intent("yes")
    assert r["intent"] == "create_issue" and r["inferred"] is True


def test_intent_explicit_ticket_beats_bare_track():
    # "track it, new ticket" -> explicit issue, NOT inferred.
    r = detect_intent("track it, new ticket please")
    assert r["intent"] == "create_issue" and r["inferred"] is False


def test_intent_project_beats_bare_track():
    r = detect_intent("track it as a project")
    assert r["intent"] == "create_project" and r["inferred"] is False


def test_intent_needs_model_when_ambiguous():
    assert detect_intent("let's chat about this at our next sync")["intent"] == "needs_model"
    assert detect_intent("")["intent"] == "needs_model"


# ── dedup_match ──────────────────────────────────────────────────────────────
CANDS = [
    {"id": "i1", "name": "Budgeting + strategic planning with Maya and Noah", "type": "issue"},
    {"id": "p1", "name": "Lead Scoring Model 2.0", "type": "project"},
]


def test_dedup_exact_normalized_match():
    m = dedup_match("budgeting + strategic planning with maya and noah", CANDS)
    assert m and m["id"] == "i1"


def test_dedup_no_match_returns_none():
    assert dedup_match("Some brand new unrelated thing", CANDS) is None


def test_dedup_containment_does_not_match():
    # Exact-only: a partial/substring title must NOT auto-link.
    assert dedup_match("Budgeting", CANDS) is None


def test_dedup_empty_title():
    assert dedup_match("", CANDS) is None


# ── build_payload ────────────────────────────────────────────────────────────
def test_build_issue_orphan_defaults_to_inbox():
    tool, p = build_payload(
        entity_kind="issue", title="HubSpot freemail associator", owner="scott@example.com",
        team="MAR", default_project="MOPS Inbox", commitment="freemail associator",
    )
    assert tool == "save_issue"
    assert p["project"] == "MOPS Inbox"        # orphan -> default home
    assert p["assignee"] == "scott@example.com"
    assert p["team"] == "MAR"


def test_build_issue_explicit_parent_wins():
    _, p = build_payload(entity_kind="issue", title="X", owner="o", team="MAR",
                         parent_project="Website repositioning", default_project="MOPS Inbox")
    assert p["project"] == "Website repositioning"


def test_build_issue_subscribers_and_relations():
    _, p = build_payload(entity_kind="issue", title="Budgeting", owner="o", team="MAR",
                        default_project="MOPS Inbox", subscribers=["Maya Lindqvist"],
                        related_to=["MAR-7075"], commitment="budgeting work")
    assert "@Maya Lindqvist" in p["description"]
    assert "subscriber" in p["description"].lower()
    assert p["relatedTo"] == ["MAR-7075"]


def test_build_project_shape():
    tool, p = build_payload(entity_kind="project", title="Lead Scoring Model 2.0",
                          owner="scott@example.com", team="MAR", notes="blocked pending strategy")
    assert tool == "save_project"
    assert p["name"] == "Lead Scoring Model 2.0"
    assert p["addTeams"] == ["MAR"]
    assert p["lead"] == "scott@example.com"
    assert "blocked pending strategy" in p["description"]


def test_build_description_prefers_notes_over_commitment():
    _, p = build_payload(entity_kind="issue", title="X", owner="o", team="MAR",
                        default_project="Inbox", commitment="raw commitment text",
                        notes="curated scope note")
    assert "curated scope note" in p["description"]
    assert "raw commitment text" not in p["description"]


def test_build_validation_errors():
    with pytest.raises(ValueError):
        build_payload(entity_kind="bogus", title="X", owner="o", team="MAR")
    with pytest.raises(ValueError):
        build_payload(entity_kind="issue", title="  ", owner="o", team="MAR", default_project="I")
    with pytest.raises(ValueError):
        build_payload(entity_kind="issue", title="X", owner="o", team="", default_project="I")
    with pytest.raises(ValueError):  # issue with no parent and no default -> never project-less
        build_payload(entity_kind="issue", title="X", owner="o", team="MAR")


# ── creation_action (idempotency) ────────────────────────────────────────────
def test_action_skip_when_linked():
    assert creation_action({"linear_link": "https://linear.app/x", "create_requested_at": "t"}) == "skip"


def test_action_reconcile_when_requested_but_unlinked():
    assert creation_action({"linear_link": None, "create_requested_at": "2026-06-30T00:00:00Z"}) == "reconcile"


def test_action_create_when_fresh():
    assert creation_action({"linear_link": None, "create_requested_at": None}) == "create"
