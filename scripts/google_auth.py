#!/usr/bin/env python3
"""
Google API auth helper — GTM Fleet Marketing Agent Fleet.

Centralizes credential loading for Google Analytics 4, Search Console, and
Google Ads. Each `get_*_client()` returns a ready-to-use SDK client; missing
env vars raise a clear error with the variable name.

GA4 and Search Console use the same service account JSON. Google Ads uses an
OAuth refresh token + developer token because Google Ads doesn't accept
service accounts for most managed-account configurations.

Required env vars:
    GA4 + Search Console:
        GOOGLE_SERVICE_ACCOUNT_JSON  # path to SA key JSON
        GA4_PROPERTY_ID              # numeric, e.g. 123456789
        GSC_SITE_URL                 # exact verified URL, e.g. https://orrery.example/

    Google Ads:
        GOOGLE_ADS_DEVELOPER_TOKEN
        GOOGLE_ADS_CLIENT_ID
        GOOGLE_ADS_CLIENT_SECRET
        GOOGLE_ADS_REFRESH_TOKEN
        GOOGLE_ADS_LOGIN_CUSTOMER_ID  # MCC ID (digits only, no dashes)
        GOOGLE_ADS_CUSTOMER_ID        # account to query (digits only, no dashes)

    Calendar + Gmail (read-only, OAuth refresh token — lets the HEADLESS chief-of-staff
    routine pull them without the interactive claude.ai connector, which does
    not survive unattended runs):
        GOOGLE_OAUTH_CLIENT_ID
        GOOGLE_OAUTH_CLIENT_SECRET
        GOOGLE_OAUTH_REFRESH_TOKEN    # granted calendar.readonly + gmail.readonly

See docs/google-api-setup.md for the one-time setup runbook.
"""

import base64
import json
import os
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import fleet_paths  # noqa: E402
from typing import Optional


REPO_ROOT = fleet_paths.FLEET_ROOT  # .env lives next to state/


# ============================================================
# .env loader
# ============================================================

def _load_dotenv() -> None:
    """Load .env from the repo root if python-dotenv is installed.

    Silent no-op if the package is missing — env vars set in the shell
    still work. Existing env vars are not overridden.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path, override=False)


_load_dotenv()


def _require_env(*names: str) -> dict:
    """Return a dict of the requested env vars; raise if any are missing.

    Error message lists every missing var so the caller fixes them all at
    once, not one-by-one.
    """
    values = {n: os.environ.get(n) for n in names}
    missing = [n for n, v in values.items() if not v]
    if missing:
        raise RuntimeError(
            f"Missing required env vars: {', '.join(missing)}. "
            f"See .env.example and docs/google-api-setup.md."
        )
    return values


# ============================================================
# Service account (GA4 + Search Console share one key)
# ============================================================

def _service_account_info() -> dict:
    """Return the service-account key as a dict.

    Two sources, in priority order, so the same code works locally and in a
    headless/cloud environment without ever putting a key file in git:

      1. GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT — the key's JSON, either raw or
         base64-encoded. Set this as an environment secret in the cloud env;
         no file touches disk or the repo.
      2. GOOGLE_SERVICE_ACCOUNT_JSON — a path to the key file (local dev).
    """
    content = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT")
    if content:
        text = content.strip()
        if not text.startswith("{"):
            text = base64.b64decode(text).decode("utf-8")
        return json.loads(text)

    path = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not path:
        raise RuntimeError(
            "Missing service account credentials: set "
            "GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT (cloud/headless secret) or "
            "GOOGLE_SERVICE_ACCOUNT_JSON (local key-file path). "
            "See .env.example and docs/google-api-setup.md."
        )
    sa_path = Path(path).expanduser()
    if not sa_path.is_file():
        raise RuntimeError(
            f"Service account JSON not found at {sa_path}. "
            f"Check GOOGLE_SERVICE_ACCOUNT_JSON in .env."
        )
    return json.loads(sa_path.read_text())


# ============================================================
# GA4
# ============================================================

def get_ga4_client():
    """Return an authenticated BetaAnalyticsDataClient.

    The service account email must be granted Viewer (or higher) on the GA4
    property. Credentials come from `_service_account_info()`.
    """
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_info(
        _service_account_info()
    )
    return BetaAnalyticsDataClient(credentials=creds)


def get_ga4_property_id() -> str:
    """Return the GA4 property ID as a string (no `properties/` prefix)."""
    env = _require_env("GA4_PROPERTY_ID")
    return env["GA4_PROPERTY_ID"]


# ============================================================
# Search Console
# ============================================================

def get_gsc_service():
    """Return an authenticated Search Console v1 service.

    The service account email must be added as a verified user in Search
    Console → Settings → Users and permissions. Credentials come from
    `_service_account_info()`.
    """
    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    scopes = ["https://www.googleapis.com/auth/webmasters.readonly"]
    creds = service_account.Credentials.from_service_account_info(
        _service_account_info(), scopes=scopes
    )
    return build("searchconsole", "v1", credentials=creds, cache_discovery=False)


def get_gsc_site_url() -> str:
    """Return the verified Search Console site URL."""
    env = _require_env("GSC_SITE_URL")
    return env["GSC_SITE_URL"]


# ============================================================
# Google Ads
# ============================================================

def get_ads_client():
    """Return an authenticated GoogleAdsClient.

    Uses OAuth refresh token + developer token. The refresh token is
    generated once via the google-ads-python OAuth helper (see
    docs/google-api-setup.md).
    """
    env = _require_env(
        "GOOGLE_ADS_DEVELOPER_TOKEN",
        "GOOGLE_ADS_CLIENT_ID",
        "GOOGLE_ADS_CLIENT_SECRET",
        "GOOGLE_ADS_REFRESH_TOKEN",
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID",
    )

    from google.ads.googleads.client import GoogleAdsClient

    config = {
        "developer_token": env["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": env["GOOGLE_ADS_CLIENT_ID"],
        "client_secret": env["GOOGLE_ADS_CLIENT_SECRET"],
        "refresh_token": env["GOOGLE_ADS_REFRESH_TOKEN"],
        "login_customer_id": env["GOOGLE_ADS_LOGIN_CUSTOMER_ID"],
        "use_proto_plus": True,
    }
    return GoogleAdsClient.load_from_dict(config)


def get_ads_customer_id() -> str:
    """Return the Google Ads customer ID to query (digits only)."""
    env = _require_env("GOOGLE_ADS_CUSTOMER_ID")
    return env["GOOGLE_ADS_CUSTOMER_ID"]


# ============================================================
# User OAuth — Calendar + Gmail (read-only, via refresh token)
# ============================================================
#
# Reading a personal/Workspace mailbox + calendar needs either domain-wide
# delegation (a Workspace-admin grant) or a user OAuth token. We use an OAuth
# refresh token — the same long-lived-token pattern as Google Ads — so the
# headless chief-of-staff routine can pull Calendar/Gmail without the interactive
# claude.ai connector, which does not survive unattended runs. Refresh happens
# server-side against the token endpoint, so there is no browser step at
# runtime. Generate the token once (docs/google-api-setup.md) with these scopes.

CALENDAR_READONLY_SCOPE = "https://www.googleapis.com/auth/calendar.readonly"
GMAIL_READONLY_SCOPE = "https://www.googleapis.com/auth/gmail.readonly"


def _user_credentials(scopes: list):
    """Build OAuth user Credentials from the refresh token in the environment.

    Reads GOOGLE_OAUTH_CLIENT_ID / _CLIENT_SECRET / _REFRESH_TOKEN. The stored
    refresh token must already carry the requested scopes (a superset is fine).
    No network or browser step — google-auth refreshes the access token on first
    API call.
    """
    env = _require_env(
        "GOOGLE_OAUTH_CLIENT_ID",
        "GOOGLE_OAUTH_CLIENT_SECRET",
        "GOOGLE_OAUTH_REFRESH_TOKEN",
    )
    from google.oauth2.credentials import Credentials

    return Credentials(
        None,  # no access token yet; refreshed on first use
        refresh_token=env["GOOGLE_OAUTH_REFRESH_TOKEN"],
        client_id=env["GOOGLE_OAUTH_CLIENT_ID"],
        client_secret=env["GOOGLE_OAUTH_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
        scopes=scopes,
    )


def get_calendar_service():
    """Return an authenticated Google Calendar v3 service (read-only)."""
    from googleapiclient.discovery import build

    creds = _user_credentials([CALENDAR_READONLY_SCOPE])
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def get_gmail_service():
    """Return an authenticated Gmail v1 service (read-only)."""
    from googleapiclient.discovery import build

    creds = _user_credentials([GMAIL_READONLY_SCOPE])
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


# ============================================================
# CLI smoke test
# ============================================================

def _smoke() -> int:
    """Verify each set of credentials loads without contacting the APIs."""
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    checks = {
        "ga4": lambda: (get_ga4_client(), get_ga4_property_id()),
        "gsc": lambda: (get_gsc_service(), get_gsc_site_url()),
        "ads": lambda: (get_ads_client(), get_ads_customer_id()),
        "calendar": lambda: _user_credentials([CALENDAR_READONLY_SCOPE]),
        "gmail": lambda: _user_credentials([GMAIL_READONLY_SCOPE]),
    }

    targets = list(checks) if target == "all" else [target]
    failed = 0
    for name in targets:
        try:
            checks[name]()
            print(f"  ok  {name}")
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            failed += 1
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_smoke())
