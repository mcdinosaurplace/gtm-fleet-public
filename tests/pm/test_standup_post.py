"""Golden tests for scripts/pm/standup_post.py.

The master post and the single consolidated tag are pinned (any wording change must
update these goldens). The tag @-mentions every member once, in roster order.
"""
from datetime import date

import pytest

from scripts.pm.config import _build_config
from scripts.pm.standup_post import (
    _ordinal,
    format_short_date,
    format_week_of,
    plan,
    render_master_post,
    render_tag,
)

CONFIG = _build_config(
    {
        "team": {
            "monday_post_pt": "05:00",
            "monday_response_deadline_pt": "23:59",
            "weekday_pulse_pt": "08:00",
            "thursday_agenda_pt": "06:30",
        },
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

MONDAY = date(2026, 6, 8)

EXPECTED_MASTER = """\
*Weekly Marketing Standup - Week of June 8th 2026*

:information_source: Remember: your updates are due by the end of today.

We'll tag everyone in this thread with 4 sections to fill in:
•  What you did last week
•  What you're doing this week
•  Anything you're blocked or need help on
•  Any external dependencies you need to note

Link to projects or issues where they apply, even if it's a simple text reference to a Linear ticket. Project work must be tracked in Linear; if you're intentionally not tracking something there, just say so and we'll note it going forward."""

EXPECTED_TAG = """\
_<@U0DEMO0001>, <@U0DEMO0002>, <@U0DEMO0003>, <@U0DEMO0004>, your stand-up for the week (6/8/26)._ Reply in this thread by the end of the day (PT) using this template:

:ballot_box_with_check: _Last Week:_
:clipboard: _This Week:_
:warning: _Blockers?:_
:grey_question: _External Dependencies_ (who it is / what we owe to unblock them / expected date):"""


@pytest.mark.parametrize(
    "day,exp",
    [(1, "1st"), (2, "2nd"), (3, "3rd"), (4, "4th"), (11, "11th"), (12, "12th"),
     (13, "13th"), (21, "21st"), (22, "22nd"), (23, "23rd"), (30, "30th")],
)
def test_ordinal(day, exp):
    assert _ordinal(day) == exp


def test_date_formats():
    assert format_week_of(MONDAY) == "June 8th 2026"
    assert format_short_date(MONDAY) == "6/8/26"


def test_master_golden():
    assert render_master_post(MONDAY) == EXPECTED_MASTER


def test_tag_golden():
    # All four members @-mentioned once, in roster order, then the template once.
    assert render_tag(CONFIG.members, MONDAY) == EXPECTED_TAG


def test_render_is_deterministic():
    assert render_master_post(MONDAY) == render_master_post(MONDAY)
    assert render_tag(CONFIG.members, MONDAY) == render_tag(CONFIG.members, MONDAY)


def test_plan_shape():
    p = plan(CONFIG, MONDAY)
    assert p["channel_id"] == "C0DEMO0001"
    assert p["week_starting"] == "2026-06-08"
    assert p["master_text"] == EXPECTED_MASTER
    assert p["tag_text"] == EXPECTED_TAG
