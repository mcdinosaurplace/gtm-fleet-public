#!/usr/bin/env python3
"""scripts/pm/standup_post.py — render the Monday stand-up master post and the
single consolidated tag that @-mentions every member once.

Pure and deterministic: given the cadence config and the stand-up date, it returns
fixed message text. The monday-standup-post skill does the Slack I/O; this core
never posts. Templates are fixed (v1 decision: the broadcast does not vary). The
tag is one in-thread reply that @-mentions all members — no per-member scheduling
(Slack has no sub-threads, so four separate tags only created dead-end pings).
"""

import json
from datetime import datetime, timezone

MASTER_TEMPLATE = """\
*Weekly Marketing Standup - Week of {week_of}*

:information_source: Remember: your updates are due by the end of today.

We'll tag everyone in this thread with 4 sections to fill in:
•  What you did last week
•  What you're doing this week
•  Anything you're blocked or need help on
•  Any external dependencies you need to note

Link to projects or issues where they apply, even if it's a simple text reference to a Linear ticket. Project work must be tracked in Linear; if you're intentionally not tracking something there, just say so and we'll note it going forward."""

TAG_TEMPLATE = """\
_{mentions}, your stand-up for the week ({short_date})._ Reply in this thread by the end of the day (PT) using this template:

:ballot_box_with_check: _Last Week:_
:clipboard: _This Week:_
:warning: _Blockers?:_
:grey_question: _External Dependencies_ (who it is / what we owe to unblock them / expected date):"""


def _ordinal(day: int) -> str:
    if 11 <= (day % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
    return f"{day}{suffix}"


def format_week_of(standup_date) -> str:
    """e.g. 'June 8th 2026'."""
    return f"{standup_date.strftime('%B')} {_ordinal(standup_date.day)} {standup_date.year}"


def format_short_date(standup_date) -> str:
    """e.g. '6/8/26'."""
    return f"{standup_date.month}/{standup_date.day}/{standup_date.strftime('%y')}"


def render_master_post(standup_date) -> str:
    return MASTER_TEMPLATE.format(week_of=format_week_of(standup_date))


def render_tag(members, standup_date) -> str:
    """The single consolidated tag: every member @-mentioned once (in roster order),
    then the fill-in template once. Native `<@id>` mentions notify each person."""
    mentions = ", ".join(f"<@{m.slack_user_id}>" for m in members)
    return TAG_TEMPLATE.format(mentions=mentions, short_date=format_short_date(standup_date))


def plan(config, standup_date) -> dict:
    """Everything the skill needs to post: master text + the single consolidated tag.
    Pure. The tag is one in-thread reply @-mentioning every member, posted right after
    the master (no per-member local-time scheduling)."""
    return {
        "channel_id": config.team_channel_id,
        "week_starting": standup_date.isoformat(),
        "master_text": render_master_post(standup_date),
        "tag_text": render_tag(config.members, standup_date),
    }


def main(argv=None):
    """CLI: print the post plan as JSON for the skill to consume.

    Usage: python -m scripts.pm.standup_post [YYYY-MM-DD]   (defaults to today, UTC)
    """
    import sys
    from datetime import date as _date

    from scripts.pm.config import load_config

    args = argv if argv is not None else sys.argv[1:]
    standup_date = _date.fromisoformat(args[0]) if args else datetime.now(timezone.utc).date()
    print(json.dumps(plan(load_config(), standup_date), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
