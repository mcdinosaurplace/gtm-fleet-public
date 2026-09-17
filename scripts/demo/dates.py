#!/usr/bin/env python3
"""Date-token rendering for DEMO_MODE fixtures.

Fixtures would go stale the day after they were written, so date-shaped strings are
written as tokens and substituted at read time, over the raw text, before it is
parsed. Shared by the fixture MCP servers (scripts/demo/fixture_mcp.py) and the
Google pull scripts' DEMO_MODE branch, which serve CSVs rather than JSON.

Token reference: fixtures/README.md.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from typing import Optional

_TOKEN_RE = re.compile(r"\{\{(TODAY|NOW|MONDAY|T([+-])(\d+)d)\}\}")


def render_tokens(text: str, today: Optional[date] = None, now: Optional[datetime] = None) -> str:
    """Substitute the date tokens a fixture may carry, over the raw JSON text.

    Written in double braces: TODAY and `{{T+0d}}` → YYYY-MM-DD · `{{T-3d}}`,
    `{{T+2d}}` → that many days off today · MONDAY → this week's Monday · NOW → an
    ISO-8601 Z timestamp. Substituting before json.loads keeps the tokens usable
    anywhere a string appears, including inside longer prose.
    """
    today = today or datetime.now(timezone.utc).date()
    now = now or datetime.now(timezone.utc)

    def sub(m: re.Match) -> str:
        name = m.group(1)
        if name == "TODAY":
            return today.isoformat()
        if name == "NOW":
            return now.strftime("%Y-%m-%dT%H:%M:%SZ")
        if name == "MONDAY":
            return (today - timedelta(days=today.weekday())).isoformat()
        sign, days = m.group(2), int(m.group(3))
        return (today + timedelta(days=days if sign == "+" else -days)).isoformat()

    return _TOKEN_RE.sub(sub, text)
