"""One-time Google Ads OAuth refresh-token generator.

Reads GOOGLE_ADS_CLIENT_ID / GOOGLE_ADS_CLIENT_SECRET from the repo .env,
runs the browser consent flow, and writes the refresh token to
localwork/ads-refresh-token.env (chmod 600). Never prints the token.
"""
import os
import sys
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import fleet_paths  # noqa: E402

REPO = fleet_paths.FLEET_ROOT
ENV_PATH = REPO / ".env"
OUT_PATH = Path.home() / ".config" / "gtm-fleet" / "ads-refresh-token.env"  # outside the repo


def read_env(path):
    vals = {}
    for line in path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            vals[k.strip()] = v.strip()
    return vals


env = read_env(ENV_PATH)
client_id = env.get("GOOGLE_ADS_CLIENT_ID", "")
client_secret = env.get("GOOGLE_ADS_CLIENT_SECRET", "")
if not client_id or not client_secret:
    sys.exit("FAIL: GOOGLE_ADS_CLIENT_ID / GOOGLE_ADS_CLIENT_SECRET not set in .env")

from google_auth_oauthlib.flow import InstalledAppFlow

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
    scopes=["https://www.googleapis.com/auth/adwords"],
)
creds = flow.run_local_server(port=0)

if not creds.refresh_token:
    sys.exit("FAIL: no refresh token returned (re-run; ensure you approve access)")

OUT_PATH.write_text(f"GOOGLE_ADS_REFRESH_TOKEN={creds.refresh_token}\n")
os.chmod(OUT_PATH, 0o600)
print(f"OK: refresh token written to {OUT_PATH} ({len(creds.refresh_token)} chars)")
