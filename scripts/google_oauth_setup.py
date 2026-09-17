#!/usr/bin/env python3
"""
One-time OAuth refresh-token generator — Calendar + Gmail (read-only).

Run this ONCE on a machine with a browser to mint the refresh token the headless
chief-of-staff routine uses. It opens a Google consent screen, then prints the refresh
token. Put that value in the routine's environment as GOOGLE_OAUTH_REFRESH_TOKEN
(and the OAuth client's id/secret as GOOGLE_OAUTH_CLIENT_ID / _CLIENT_SECRET).

This script is NOT used at runtime and is not needed in the headless environment.

Usage:
    export GOOGLE_OAUTH_CLIENT_ID=...
    export GOOGLE_OAUTH_CLIENT_SECRET=...
    python3 scripts/google_oauth_setup.py

Requires (local, one-time only):
    python3 -m pip install google-auth-oauthlib

See docs/google-api-setup.md for creating the OAuth client and the
publish/Internal-app caveat (External + Testing apps expire refresh tokens in
7 days, which silently breaks the scheduled pull).
"""

import os
import sys

SCOPES = [
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def main():
    client_id = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
    if not client_id or not client_secret:
        print(
            "Set GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET first "
            "(from your OAuth desktop-app client). See docs/google-api-setup.md.",
            file=sys.stderr,
        )
        return 2

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print(
            "google-auth-oauthlib is not installed. This one-time step needs it:\n"
            "    python3 -m pip install google-auth-oauthlib",
            file=sys.stderr,
        )
        return 2

    flow = InstalledAppFlow.from_client_config(
        {
            "installed": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        },
        scopes=SCOPES,
    )
    creds = flow.run_local_server(port=0)
    if not creds.refresh_token:
        print(
            "No refresh token returned. Google only issues one on FIRST consent: "
            "revoke the app at https://myaccount.google.com/permissions and re-run.",
            file=sys.stderr,
        )
        return 1

    print("\nGOOGLE_OAUTH_REFRESH_TOKEN=" + creds.refresh_token)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
