#!/usr/bin/env python3
"""
Google Calendar pull — GTM Fleet Marketing Agent Fleet.

Reads the running user's calendar for a single day and prints JSON. This is the
*headless* path for chief-of-staff's AM routine: it authenticates with an OAuth refresh
token (google_auth.get_calendar_service), independent of the interactive
claude.ai Calendar connector, which does not survive unattended runs. In
interactive runs chief-of-staff uses the MCP connector; this script is the headless
fallback (see roster/chief-of-staff/prompt.md step 8a).

Usage:
    python3 scripts/gcal_pull.py                       # today, America/Los_Angeles
    python3 scripts/gcal_pull.py --date 2026-07-10
    python3 scripts/gcal_pull.py --tz America/New_York --output -

Output: JSON on stdout. On failure: {"error": "..."} on stdout + a message on
stderr, exit 1 — so the caller can tell a clean failure from real (empty) data.

Env vars (see docs/google-api-setup.md):
    GOOGLE_OAUTH_CLIENT_ID
    GOOGLE_OAUTH_CLIENT_SECRET
    GOOGLE_OAUTH_REFRESH_TOKEN
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from google_auth import get_calendar_service


def _day_bounds(date_str, tz):
    """Return (timeMin, timeMax, iso_date) spanning the local day in RFC3339."""
    tzinfo = ZoneInfo(tz)
    if date_str:
        day = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        day = datetime.now(tzinfo).date()
    start = datetime(day.year, day.month, day.day, tzinfo=tzinfo)
    end = start + timedelta(days=1)
    return start.isoformat(), end.isoformat(), day.isoformat()


def _join_link(event):
    """A video join link from conferenceData or the legacy hangoutLink."""
    if event.get("hangoutLink"):
        return event["hangoutLink"]
    for ep in event.get("conferenceData", {}).get("entryPoints", []):
        if ep.get("entryPointType") == "video" and ep.get("uri"):
            return ep["uri"]
    return None


def _self_rsvp(event):
    for a in event.get("attendees", []):
        if a.get("self"):
            return a.get("responseStatus")
    return None


def _shape(event):
    start = event.get("start", {})
    end = event.get("end", {})
    return {
        "id": event.get("id"),
        "title": event.get("summary", "(no title)"),
        "event_type": event.get("eventType", "default"),
        "all_day": "date" in start,  # 'date' (not 'dateTime') means all-day
        "start": start.get("dateTime") or start.get("date"),
        "end": end.get("dateTime") or end.get("date"),
        "attendees": [
            {
                "email": a.get("email"),
                "name": a.get("displayName"),
                "response": a.get("responseStatus"),
                "self": bool(a.get("self")),
                "organizer": bool(a.get("organizer")),
            }
            for a in event.get("attendees", [])
        ],
        "self_rsvp": _self_rsvp(event),
        "join_link": _join_link(event),
        "location": event.get("location"),
        "description": event.get("description"),
        "attachments": [
            {"title": at.get("title"), "url": at.get("fileUrl")}
            for at in event.get("attachments", [])
        ],
        "html_link": event.get("htmlLink"),
        "status": event.get("status"),
    }


def main():
    parser = argparse.ArgumentParser(description="Pull one day of Google Calendar events as JSON.")
    parser.add_argument("--date", default=None, help="YYYY-MM-DD. Default: today in --tz.")
    parser.add_argument("--tz", default="America/Los_Angeles", help="IANA timezone. Default America/Los_Angeles.")
    parser.add_argument("--calendar-id", default="primary", help="Calendar ID. Default 'primary'.")
    parser.add_argument("--output", default="-", help="Output path or '-' for stdout. Default '-'.")
    args = parser.parse_args()

    try:
        time_min, time_max, day = _day_bounds(args.date, args.tz)
        service = get_calendar_service()
        events = []
        page_token = None
        while True:
            resp = service.events().list(
                calendarId=args.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy="startTime",
                timeZone=args.tz,
                pageToken=page_token,
                maxResults=250,
            ).execute()
            events.extend(resp.get("items", []))
            page_token = resp.get("nextPageToken")
            if not page_token:
                break
    except Exception as e:
        sys.stdout.write(json.dumps({"error": f"{type(e).__name__}: {e}", "source": "gcal"}) + "\n")
        print(f"ERROR: calendar pull failed: {e}", file=sys.stderr)
        return 1

    payload = {
        "date": day,
        "timezone": args.tz,
        "calendar_id": args.calendar_id,
        "event_count": len(events),
        "events": [_shape(e) for e in events],
    }
    body = json.dumps(payload, indent=2, default=str)
    if args.output == "-":
        sys.stdout.write(body + "\n")
    else:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body)
        print(f"Wrote {len(events)} events to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
