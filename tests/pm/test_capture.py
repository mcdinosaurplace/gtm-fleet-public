"""Tests for scripts/pm/capture.py — the anchor-first deterministic parse.

Covers: section detection by emoji + keyword, the rule path (template-conforming
reply), the model-fallback flag (free-form reply), '/'-structured external deps vs
sentence deps, member aggregation (ignoring non-roster authors), and date parsing.
"""
from datetime import date

from scripts.pm import standup_post
from scripts.pm.capture import (
    _parse_simple_date,
    aggregate_by_member,
    capture,
    detect_section,
    has_linear_link,
    is_bot_post,
    parse_external_dep_line,
    parse_external_deps,
    parse_reply,
    split_sections,
)
from scripts.pm.config import _build_config

CONFIG = _build_config(
    {
        "team": {"monday_post_pt": "05:00", "monday_response_deadline_pt": "23:59",
                 "weekday_pulse_pt": "08:00", "thursday_agenda_pt": "06:30"},
        "accountability_mode": "state_only",
        "team_channel_id": "C0DEMO0001",
        "default_external_owner": "Maya Lindqvist",
        "members": [
            {"name": "Scott McKeighen", "slack_user_id": "U0DEMO0001", "slack_alias": "Scott McKeighen",
             "timezone": "America/Los_Angeles", "standup_tag_local": "08:00"},
            {"name": "Maya Lindqvist", "slack_user_id": "U0DEMO0002", "slack_alias": "Maya Lindqvist",
             "timezone": "America/Los_Angeles", "standup_tag_local": "08:00"},
            {"name": "Priya Natarajan", "slack_user_id": "U0DEMO0003", "slack_alias": "Priya Natarajan",
             "timezone": "America/Denver", "standup_tag_local": "10:00"},
            {"name": "Tomas Reyes", "slack_user_id": "U0DEMO0004", "slack_alias": "tomas",
             "timezone": "Europe/Athens", "standup_tag_local": "09:00"},
        ],
    }
)

CONFORMING = (
    ":ballot_box_with_check: Last Week:\nShipped MAR-7076\n"
    ":clipboard: This Week:\nLaunch prep\n"
    ":warning: Blockers?:\nNone\n"
    ":grey_question: External Dependencies:\nJules / blog revisions / 2026-06-11"
)
FREEFORM = "did site work last week and this week, no blockers, waiting on Mateo by end of tomorrow"


def test_detect_section_by_emoji():
    assert detect_section(":warning: Blockers?:") == "blockers"
    assert detect_section(":grey_question: External Dependencies:") == "external_deps"


def test_detect_section_by_keyword():
    assert detect_section("*Last Week:*") == "last_week"
    assert detect_section("This week - here's what I'm doing") == "this_week"
    assert detect_section("just some text") is None


def test_split_sections_conforming():
    sections, matched = split_sections(CONFORMING)
    assert matched == 4
    assert sections["last_week"] == "Shipped MAR-7076"
    assert sections["this_week"] == "Launch prep"
    assert sections["external_deps"] == "Jules / blog revisions / 2026-06-11"


def test_parse_reply_conforming_vs_freeform():
    assert parse_reply(CONFORMING)["needs_model"] is False
    assert parse_reply(CONFORMING)["linear_links_present"] is True
    assert parse_reply(FREEFORM)["needs_model"] is True       # no anchors -> model fallback
    assert parse_reply(FREEFORM)["linear_links_present"] is False


def test_has_linear_link():
    assert has_linear_link("see MAR-7076") is True
    assert has_linear_link("https://linear.app/orrery/project/x") is True
    assert has_linear_link("nothing here") is False


def test_external_deps_slash_vs_sentence():
    out = parse_external_deps("Jules / blog revisions / 2026-06-11\nwaiting on Mateo by tomorrow")
    assert len(out["rule"]) == 1
    assert out["rule"][0]["external_party"] == "Jules"
    assert out["rule"][0]["expected_delivery"] == "2026-06-11"
    assert out["rule"][0]["parsed_by"] == "rule"
    assert out["needs_model"] == ["waiting on Mateo by tomorrow"]   # sentence -> model fallback


def test_parse_external_dep_line_non_structured():
    assert parse_external_dep_line("just a sentence about Mateo") is None


def test_external_deps_negative_response_is_zero_deps_not_model_fallback():
    for text in ("None", "none.", "N/A", "n/a", "Nothing", "Not applicable", "No dependencies", "No"):
        assert parse_external_deps(text) == {"rule": [], "needs_model": []}, text


def test_external_deps_negative_response_does_not_swallow_real_content():
    out = parse_external_deps("No, still waiting on Design for the mockups")
    assert out["rule"] == []
    assert out["needs_model"] == ["No, still waiting on Design for the mockups"]


def test_simple_date():
    assert _parse_simple_date("2026-06-11") == "2026-06-11"
    assert _parse_simple_date("6/11/26") == "2026-06-11"
    assert _parse_simple_date("6/11/2026") == "2026-06-11"
    assert _parse_simple_date("June 11th") is None        # NL -> model fallback
    assert _parse_simple_date("13/40/99") is None


def test_aggregate_ignores_non_roster():
    thread = [
        {"user_id": "UBOT", "text": "master post"},          # Scribe -> ignored
        {"user_id": "U0DEMO0001", "text": "part one"},
        {"user_id": "U0DEMO0001", "text": "part two"},
    ]
    agg = aggregate_by_member(thread, CONFIG)
    assert agg == {"Scott McKeighen": "part one\npart two"}


def test_capture_end_to_end():
    thread = [
        {"user_id": "UBOT", "text": "master"},
        {"user_id": "U0DEMO0001", "text": CONFORMING},
        {"user_id": "U0DEMO0003", "text": FREEFORM},
    ]
    result = capture(thread, CONFIG)
    by = {m["owner"]: m for m in result["members"]}
    assert by["Scott McKeighen"]["external_deps_rule"][0]["external_party"] == "Jules"
    assert "Priya Natarajan" not in by  # zero anchors matched -> chatter, not a response
    ctx = {c["owner"]: c for c in result["context"]}
    assert ctx["Priya Natarajan"]["raw_text"] == FREEFORM
    # chatter does not count as a response: Priya stays a non-responder alongside Maya/Tomas
    assert set(result["non_responders"]) == {"Priya Natarajan", "Maya Lindqvist", "Tomas Reyes"}


def test_chatter_reply_to_someone_elses_blocker_is_context_not_a_response():
    """Real 2026-07-13 thread shape: Scott's blocker section asks Priya a question, and
    Priya replies in-thread answering it -- never touching her own template. That reply
    is chatter, not her stand-up: it must not create a `members` entry or clear her from
    `non_responders`, but it should still be preserved for the context/commitment-mining
    pass (see capture()'s docstring)."""
    chatter = (
        "> Priya Natarajan / Maya Lindqvist should I assume the copy for founder nurture "
        "email(s) that Jules was working on is done and ready?\n"
        "Scott McKeighen I answered all of Jules's questions for me on those emails "
        "and have been out of the loop on those otherwise. Can you check with her to "
        "confirm they're fine to go?"
    )
    thread = [
        {"user_id": "U0DEMO0001", "text": CONFORMING},
        {"user_id": "U0DEMO0003", "text": chatter},
    ]
    result = capture(thread, CONFIG)
    assert [m["owner"] for m in result["members"]] == ["Scott McKeighen"]
    assert result["context"] == [{"owner": "Priya Natarajan", "raw_text": chatter}]
    assert "Priya Natarajan" in result["non_responders"]


def test_is_bot_post_recognizes_master_and_tag():
    monday = date(2026, 6, 8)
    assert is_bot_post(standup_post.render_master_post(monday)) is True
    assert is_bot_post(standup_post.render_tag(CONFIG.members, monday)) is True
    assert is_bot_post(CONFORMING) is False
    assert is_bot_post("just a normal reply about last week") is False


def test_bot_posts_under_member_uid_are_skipped():
    """The bot posts the master + tag AS the operator's user_id (no separate bot account).
    Those must not be folded into that member's captured reply — only the real human
    messages are. Renders the real templates so a future template change trips this test."""
    monday = date(2026, 6, 8)
    scott = "U0DEMO0001"
    thread = [
        {"user_id": scott, "text": standup_post.render_master_post(monday)},           # bot
        {"user_id": scott, "text": standup_post.render_tag(CONFIG.members, monday)},    # bot
        {"user_id": scott, "text": "FYI ignore the dupes"},                            # human chatter
        {"user_id": scott, "text": CONFORMING},                                        # the real reply
    ]
    result = capture(thread, CONFIG)
    scott_row = next(m for m in result["members"] if m["owner"] == "Scott McKeighen")
    # bot posts excluded from the audit raw_text...
    assert "Weekly Marketing Standup" not in scott_row["raw_text"]
    assert "using this template" not in scott_row["raw_text"]
    # ...but the human reply is kept and parsed cleanly
    assert scott_row["sections"]["last_week"] == "Shipped MAR-7076"
    assert scott_row["sections"]["external_deps"].startswith("Jules /")
