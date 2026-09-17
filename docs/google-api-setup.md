# Google API Setup — One-Time Runbook

This runbook bootstraps Claude's programmatic access to **Google Analytics 4**, **Google Search Console**, and **Google Ads** for the {{COMPANY}} Marketing workspace. After completing it once, the `scripts/ga4_pull.py`, `scripts/gsc_pull.py`, and `scripts/google_ads_pull.py` CLIs will work end-to-end.

> Estimated wall-clock time: 30–45 minutes. Most of it is Google Cloud Console clicks; the Ads OAuth grant is the only step that needs a browser hand-off.

---

## 0. Prerequisites

- **GA4:** Admin (or Editor) on the property.
- **Search Console:** **Owner** on the property — specifically Owner, not Full
  or Restricted. Only Owners can add users (step 4). If you're not an Owner,
  identify one under Settings → Users and permissions and plan the handoff
  ask before starting.
- **Google Ads:** access to a **manager account (MCC)**. Developer tokens
  (step 5a) only exist at the MCC level — the API Center is invisible from
  client accounts. If {{COMPANY}} has no MCC, you'll create a free one in step 5a.
- A Google Cloud Platform project you control. New project is fine.
- Python 3.10+ with the deps installed:
  ```
  python3 -m pip install -r scripts/requirements.txt
  ```

---

## 1. Create the GCP project and enable APIs

1. Go to <https://console.cloud.google.com/projectcreate>. Name it something like `{{GCP_PROJECT_ID}}`.
2. With that project selected, enable these APIs (Console → APIs & Services → Enable APIs):
   - **Google Analytics Data API**
   - **Google Search Console API**
   - **Google Ads API**
   - **Google Calendar API** (chief-of-staff AM brief — headless)
   - **Gmail API** (chief-of-staff AM brief — headless)

---

## 2. Create the service account (for GA4 + Search Console)

1. Console → IAM & Admin → Service Accounts → **Create service account**.
2. Name: `gtm-fleet-reader`. Description: `Read-only access for Claude pulls`.
3. Skip the "Grant access" step at the project level — we'll grant per-product access in GA4 / Search Console UIs instead.
4. Open the new service account → **Keys** → **Add key** → **Create new key** → **JSON**. Save the file.
5. **Move the JSON file outside the repo.** Recommended path: `~/.config/gtm-fleet/google-sa.json`.
   ```
   mkdir -p ~/.config/gtm-fleet
   mv ~/Downloads/{{GCP_PROJECT_ID}}-*.json ~/.config/gtm-fleet/google-sa.json
   chmod 600 ~/.config/gtm-fleet/google-sa.json
   ```
6. Note the service account email (e.g. `{{GCP_SERVICE_ACCOUNT_EMAIL}}`). You'll paste it in the next two steps.

---

## 3. Grant GA4 access to the service account

1. GA4 → **Admin** → (left column, under Account or Property) **Property Access Management**.
2. Click **+** → Add users → paste the service account email.
3. Role: **Viewer**. Uncheck "Notify by email" (the SA can't read mail). Save.
4. Note the GA4 **Property ID** (Admin → Property Settings → Property ID, e.g. `123456789`). You'll put this in `.env` as `GA4_PROPERTY_ID`.

---

## 4. Grant Search Console access to the service account

> **Owner required.** Only property Owners can add users. If the Add user
> button is missing or fails, you're a Full/Restricted user — find an Owner
> in the Users and permissions list (owners are badged) and ask them to do
> step 2 for you; have them delegate ownership to you at the same time so
> future changes are self-serve. If no Owner is reachable, independent
> verification via DNS TXT record (whoever controls {{COMPANY_DOMAIN}} DNS) makes
> you an Owner automatically.

1. Search Console → **Settings** (gear icon, bottom left) → **Users and permissions**.
2. **Add user** → paste the service account email. Permission: **Restricted** (read-only).
3. Note the exact site URL as it appears in Search Console (e.g. `https://{{COMPANY_DOMAIN}}/` with trailing slash, or `sc-domain:{{COMPANY_DOMAIN}}` for domain properties). You'll put this in `.env` as `GSC_SITE_URL`.

---

## 5. Set up Google Ads access

Google Ads doesn't accept service accounts for most managed-account configurations. We use OAuth 2.0 with a refresh token instead — generated once, then long-lived.

### 5a. Apply for a developer token

> **"The API Center is only available to manager accounts"** means you're
> signed into the client account. Developer tokens only exist at the MCC
> level. If {{COMPANY}} has no MCC (check the client account → Access and
> security → Managers tab), create a free one — it's an empty container
> and changes nothing about how the ads run:
>
> 1. Create a manager account at
>    <https://ads.google.com/home/tools/manager-accounts/>
>    (e.g. "{{COMPANY}} Marketing API").
> 2. Link it to the production account: from the MCC, send a link request
>    to the client account ID; accept the invite inside the client account
>    under Access and security → Managers.
> 3. The new MCC's ID becomes `GOOGLE_ADS_LOGIN_CUSTOMER_ID` in step 5d.

1. Sign into the Google Ads MCC (manager) account at <https://ads.google.com/>.
2. Tools & Settings → Setup → **API Center**.
3. Apply for a developer token. **Basic Access** is sufficient (15k operations/day, plenty for read-only pulls).
   - The token is issued immediately but starts in **test** status — test
     tokens can only query test accounts, not production data. Real pulls
     work once the Basic Access application is approved (typically a few
     business days). Use case for the application: internal read-only
     reporting / ETL.
4. Note the token. Put it in `.env` as `GOOGLE_ADS_DEVELOPER_TOKEN`.

### 5b. Create OAuth 2.0 credentials

1. GCP Console → APIs & Services → **Credentials** → Create Credentials → **OAuth client ID**.
2. If prompted, configure the consent screen first. **Use User type:
   Internal** (available since {{COMPANY_DOMAIN}} is on Google Workspace) — External
   apps left in "Testing" mode expire refresh tokens after **7 days**, which
   silently breaks scheduled pulls. Only fall back to External + Testing
   (+ your email as test user) if Internal is unavailable, and publish the
   app to production before relying on it.
3. Application type: **Desktop app**. Name: `gtm-fleet-ads`.
4. Download the credentials JSON. From it, grab `client_id` and `client_secret` and put them in `.env` as `GOOGLE_ADS_CLIENT_ID` and `GOOGLE_ADS_CLIENT_SECRET`.

### 5c. Generate the refresh token (one-time browser dance)

The `google-ads-python` package ships a helper script. Run:

```
python3 -m google.ads.googleads.oauth2 \
    --client_id "$GOOGLE_ADS_CLIENT_ID" \
    --client_secret "$GOOGLE_ADS_CLIENT_SECRET" \
    --additional_scopes https://www.googleapis.com/auth/adwords
```

Or, if that helper isn't available in your install, use this short snippet:

```python
# scripts/_one_time_ads_oauth.py — run once, then delete or .gitignore
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_config(
    {
        "installed": {
            "client_id": "YOUR_CLIENT_ID",
            "client_secret": "YOUR_CLIENT_SECRET",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    },
    scopes=["https://www.googleapis.com/auth/adwords"],
)
creds = flow.run_local_server(port=0)
print("REFRESH_TOKEN:", creds.refresh_token)
```

1. The helper opens a browser. Sign in with the Google account that has
   access to the **manager account** (the one that created the MCC) — the
   API authenticates "as" the MCC via `login_customer_id`, so MCC access on
   the OAuth user is what's required, not just client-account access.
2. Copy the printed refresh token and put it in `.env` as `GOOGLE_ADS_REFRESH_TOKEN`.

### 5d. Set the customer IDs

1. `GOOGLE_ADS_LOGIN_CUSTOMER_ID` — the MCC ID (digits only, no dashes).
2. `GOOGLE_ADS_CUSTOMER_ID` — the specific account to query (digits only, no dashes).

---

## 5B. Calendar + Gmail read access (headless chief-of-staff brief)

chief-of-staff's daily brief runs as a **headless cloud routine**. The interactive
claude.ai Calendar/Gmail connectors do not survive unattended runs, so the brief
reads them through the Google APIs with an OAuth **refresh token** instead — the
same long-lived-token pattern as Google Ads (§5). Read-only.

1. **Enable the APIs** (if not already done in §1): Google Calendar API + Gmail API.
2. **OAuth client.** Reuse the Desktop OAuth client from §5b, or create another
   (Credentials → Create → OAuth client ID → Desktop app). Put its id/secret in
   `.env` as `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET`.
   - **Consent screen must be User type: Internal** (available since {{COMPANY_DOMAIN}} is
     Google Workspace). External + "Testing" apps expire refresh tokens after
     **7 days**, which silently breaks the scheduled pull. If you must use
     External, publish the app to production before relying on it.
3. **Generate the refresh token (one-time browser step):**
   ```
   export GOOGLE_OAUTH_CLIENT_ID=...
   export GOOGLE_OAUTH_CLIENT_SECRET=...
   python3 -m pip install google-auth-oauthlib   # one-time, local only
   python3 scripts/google_oauth_setup.py
   ```
   Sign in as the mailbox owner (`{{OPERATOR_EMAIL}}`). The script requests
   `calendar.readonly` + `gmail.readonly` and prints
   `GOOGLE_OAUTH_REFRESH_TOKEN=...`. Put that in `.env` (and in the cloud
   routine's environment variables — see §8).
4. **Verify:**
   ```
   python3 scripts/google_auth.py calendar   # ok  calendar
   python3 scripts/google_auth.py gmail      # ok  gmail
   python3 scripts/gcal_pull.py | head        # today's events as JSON
   python3 scripts/gmail_pull.py | head       # unread + starred as JSON
   ```

---

## 6. Verify

Run the smoke test in `google_auth.py`:

```
python3 scripts/google_auth.py        # checks all five
python3 scripts/google_auth.py ga4    # individual checks
python3 scripts/google_auth.py gsc
python3 scripts/google_auth.py ads
python3 scripts/google_auth.py calendar
python3 scripts/google_auth.py gmail
```

Expected output:
```
  ok  ga4
  ok  gsc
  ok  ads
  ok  calendar
  ok  gmail
```

If any line is `FAIL`, the error message names the missing or broken credential. Fix that and rerun. **The smoke test only verifies credential loading**, not API access — the per-script smoke tests in the [implementation plan verification section](../../.claude/plans/claude-i-want-you-scalable-fog.md) confirm live API calls.

---

## 7. Lock down what you committed

After this runbook completes, these files / paths exist:

| Path | Where | Committed? |
|---|---|---|
| `~/.config/gtm-fleet/google-sa.json` | Outside repo | No (outside repo) |
| `.env` | Repo root | No (gitignored) |
| `.env.example` | Repo root | Yes (no secrets) |
| `docs/google-api-setup.md` | Repo | Yes (this file) |

Verify with:
```
git status
git check-ignore -v .env google-sa.json
```

`git check-ignore` should confirm both files are ignored. If `.env` shows up under `git status`, stop and fix `.gitignore` before committing.

---

## 8. Cloud / headless routine secrets (performance-marketer + chief-of-staff)

The local `.env` exists only for your machine. A server-side cloud routine (e.g.
performance-marketer's daily Tick, or chief-of-staff's AM brief, running via a claude.ai routine) has
no `.env` and must never get one in git. `scripts/google_auth.py` reads every credential from `os.environ`,
so the cloud routine just needs these set as **environment secrets** in the cloud
environment's settings UI — nothing is committed.

Set as plain environment secrets (string values, copy from your local `.env`):

| Secret | Notes |
|---|---|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | string |
| `GOOGLE_ADS_CLIENT_ID` | string |
| `GOOGLE_ADS_CLIENT_SECRET` | string |
| `GOOGLE_ADS_REFRESH_TOKEN` | string |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | digits only |
| `GOOGLE_ADS_CUSTOMER_ID` | digits only |
| `GA4_PROPERTY_ID` | numeric |
| `GSC_SITE_URL` | e.g. `https://{{COMPANY_DOMAIN}}/` |
| `GOOGLE_OAUTH_CLIENT_ID` | string (Calendar/Gmail — chief-of-staff AM brief) |
| `GOOGLE_OAUTH_CLIENT_SECRET` | string |
| `GOOGLE_OAUTH_REFRESH_TOKEN` | string; granted calendar.readonly + gmail.readonly |

The service-account key (GA4 + GSC) is a *file* locally, so for the cloud set its
**content** instead of a path — `_service_account_info()` prefers it and writes no
file:

| Secret | How to produce it |
|---|---|
| `GOOGLE_SERVICE_ACCOUNT_JSON_CONTENT` | raw JSON: paste the key file's contents; or base64: `base64 -i ~/.config/gtm-fleet/google-sa.json \| pbcopy` |

Do **not** set `GOOGLE_SERVICE_ACCOUNT_JSON` (the path) in the cloud — leave it
unset so the content var is used.

After setting the secrets, confirm from inside the cloud environment with the same
smoke test: `python3 scripts/google_auth.py` should print `ok ga4 / ok gsc / ok ads`.
(GSC live queries currently 403 until the service account is authorized on the
{{COMPANY_DOMAIN}} Search Console property — credential loading still passes.)

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| GA4: `403 PERMISSION_DENIED` | SA email isn't on the property | Re-do step 3 |
| GSC: `403` or empty results | SA email not added in Search Console settings, OR `GSC_SITE_URL` doesn't match the verified property exactly | Re-do step 4; check trailing slash and `sc-domain:` prefix |
| GSC: can't add users (no button / denied) | You're a Full/Restricted user, not an Owner | See the Owner-required note in step 4 |
| Ads: "API Center is only available to manager accounts" | Signed into the client account; no MCC exists or you're not in it | See the MCC note in step 5a — create a free manager account and link it |
| Ads: `developer-token-not-approved` | Developer token still pending review (test status) | Wait for Basic Access approval; test tokens can't query production accounts |
| Ads: `GRPC target method can't be resolved` | Installed `google-ads` package targets a sunset Ads API version (versions sunset ~12 months after release) | `python3 -m pip install --upgrade google-ads` (requirements.txt intentionally has no upper bound) |
| Ads: `invalid_grant` on refresh | Refresh token revoked (account password change, 6 months idle, etc.) | Re-run step 5c |
| `Missing required env vars: ...` | `.env` not loaded | Confirm `python-dotenv` is installed and `.env` exists at repo root |
