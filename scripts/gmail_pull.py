#!/usr/bin/env python3
"""
Gmail pull — GTM Fleet Marketing Agent Fleet.

Reads unread + starred inbox messages and prints JSON metadata (sender, subject,
snippet, labels, date, deep link). This is the *headless* path for chief-of-staff's AM
routine: it authenticates with an OAuth refresh token (google_auth.get_gmail_
service), independent of the interactive claude.ai Gmail connector, which does
not survive unattended runs. Classification (which mail is worth surfacing)
stays in chief-of-staff's prompt; this script returns raw metadata only.

Usage:
    python3 scripts/gmail_pull.py                    # unread + starred, default caps
    python3 scripts/gmail_pull.py --unread-max 30 --starred-max 25
    python3 scripts/gmail_pull.py --output -

Output: JSON on stdout. On failure: {"error": "..."} on stdout + a message on
stderr, exit 1.

Env vars (see docs/google-api-setup.md):
    GOOGLE_OAUTH_CLIENT_ID
    GOOGLE_OAUTH_CLIENT_SECRET
    GOOGLE_OAUTH_REFRESH_TOKEN
"""

import argparse
import json
import sys
from pathlib import Path

from google_auth import get_gmail_service


def _header(headers, name):
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value")
    return None


def _fetch(service, query, max_results):
    """List message IDs for a Gmail query, then fetch metadata for each."""
    listed = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    messages = []
    for stub in listed.get("messages", []):
        msg = service.users().messages().get(
            userId="me",
            id=stub["id"],
            format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        headers = msg.get("payload", {}).get("headers", [])
        messages.append({
            "id": msg.get("id"),
            "thread_id": msg.get("threadId"),
            "from": _header(headers, "From"),
            "subject": _header(headers, "Subject"),
            "date": _header(headers, "Date"),
            "snippet": msg.get("snippet"),
            "labels": msg.get("labelIds", []),
            "link": f"https://mail.google.com/mail/u/0/#inbox/{msg.get('id')}",
        })
    return messages


def main():
    parser = argparse.ArgumentParser(description="Pull unread + starred Gmail metadata as JSON.")
    parser.add_argument("--unread-max", type=int, default=30, help="Max unread messages. Default 30.")
    parser.add_argument("--starred-max", type=int, default=25, help="Max starred messages. Default 25.")
    parser.add_argument("--unread-query", default="is:unread in:inbox")
    parser.add_argument("--starred-query", default="is:starred in:inbox")
    parser.add_argument("--output", default="-", help="Output path or '-' for stdout. Default '-'.")
    args = parser.parse_args()

    try:
        service = get_gmail_service()
        unread = _fetch(service, args.unread_query, args.unread_max)
        starred = _fetch(service, args.starred_query, args.starred_max)
    except Exception as e:
        sys.stdout.write(json.dumps({"error": f"{type(e).__name__}: {e}", "source": "gmail"}) + "\n")
        print(f"ERROR: gmail pull failed: {e}", file=sys.stderr)
        return 1

    payload = {
        "unread": {"query": args.unread_query, "count": len(unread), "messages": unread},
        "starred": {"query": args.starred_query, "count": len(starred), "messages": starred},
    }
    body = json.dumps(payload, indent=2, default=str)
    if args.output == "-":
        sys.stdout.write(body + "\n")
    else:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body)
        print(f"Wrote {len(unread)} unread + {len(starred)} starred to {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
