# Connector Reauth Runbook — Calendar / Gmail (scheduled runs)

Procedure for restoring the Google MCP connectors (Google Calendar, Gmail) when
chief-of-staff's **scheduled** daily brief reports them offline / unbound, and for
**verifying** the fix so we never again declare it "fixed" on a claim.

## When to use

- A scheduled chief-of-staff AM/PM brief shows `⚠️ Calendar not connected` /
  `⚠️ Gmail not connected`, or (historically) "Calendar/Gmail offline".
- `ops-incidents.md` shows a recurring `MCP_BIND_FAILURE` for chief-of-staff
  Calendar/Gmail.

## Root cause (what this is actually about)

The connectors are **not broken**. In an interactive Claude Code session they
bind and return live data. They are absent only in the **environment where the
scheduled Tick runs**. This is an **authorization gap**, not a code bug, and no
prompt edit can fix it — the fix is reauthorizing the connectors in the
scheduled run context.

Origin: the Google Calendar connector lost auth in a scheduled run
(`state/journal/ops-incidents.md`); the "operator to reauth" remediation was
never closed, and the outage was mislabeled "expected — security rollover" and
copied forward for months. That label is retired (see `docs/mcp-preflight.md` →
"Do not rationalize a chronic outage as expected").

**The trap:** authorizing a connector in the interactive app does **not**
necessarily propagate to the scheduled task's session. Interactive-app
authorization ≠ scheduled-run authorization. The connector must be available in
the context that actually runs `/chief-of-staff am`.

## Fix procedure

1. **Confirm the interactive baseline.** In an interactive session, confirm
   Calendar + Gmail return data (e.g. `list_calendars`, `search_threads`). If
   they fail even here, reconnect them in the Claude Code / claude.ai connector
   settings for the account, re-running the OAuth flow, then retry. (This is the
   only step you may already have done — it is necessary but not sufficient.)

2. **The run context (confirmed).** This is a **headless cloud
   routine** (claude.ai/code/routines) against the repo's default branch, with
   connectors enabled per-routine. Manual runs work; scheduled fires don't —
   a headless routine can't perform the browser re-consent a lapsed Google OAuth
   connector needs, and reconnecting the connector by hand has been tried
   repeatedly and does not hold. So the durable fix is the API path below, not
   another reconnect.

3. **Authorize the connectors for that context.** Ensure Calendar + Gmail are
   connected and enabled for the scheduled session's account/host, not just the
   interactive app. Re-run the OAuth flow from that context if needed.

4. **Do not declare done yet.** Proceed to the verification gate.

## Verification gate (all must pass — this is the anti-"it's-fixed" check)

- **G1 — interactive, on the scheduled task's host.** From the task's working
  directory, run `/chief-of-staff am` manually. PASS = the brief's calendar section
  shows real meetings (or a legitimate "No meetings today"), and the Inbox
  section shows classified mail — **not** the `⚠️ not connected` banner, and no
  `MCP_BIND_FAILURE` for Calendar/Gmail in `ops-incidents.md` for that run.

- **G2 — the next real scheduled fire.** Let the 07:00 PT scheduled task fire
  (or trigger it). Inspect the run's committed journal entry in
  `state/journal/chief-of-staff.md`: PASS = `Meetings today:` shows real data, no
  "offline", and no Calendar/Gmail `MCP_BIND_FAILURE` filed for that run.

**Only G2 passing on a real scheduled fire counts as fixed.** G1 passing while
G2 fails means the scheduled context is not inheriting the connector session —
use the durable fix below.

## The durable fix (BUILT): OAuth-refresh-token API path

Reconnecting the interactive connector has been tried repeatedly and does not
hold on the headless fire. So chief-of-staff no longer depends on it for Calendar/Gmail
in the routine — it pulls them through the Google APIs with an OAuth **refresh
token** carried as an environment variable. Implemented in:

- `scripts/gcal_pull.py`, `scripts/gmail_pull.py` — headless pulls → JSON.
- `scripts/google_auth.py` — `get_calendar_service()` / `get_gmail_service()`.
- chief-of-staff prompt steps 8a/8c — use the MCP connector when bound (interactive),
  else fall back to these scripts; escalate only if the script also fails.

**To turn it on:**
1. Follow `docs/google-api-setup.md` §5B to mint the refresh token
   (`scripts/google_oauth_setup.py`, scopes `calendar.readonly` +
   `gmail.readonly`). Use an **Internal** Workspace OAuth app so the token does
   not expire after 7 days.
2. Set `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`,
   `GOOGLE_OAUTH_REFRESH_TOKEN` as **environment variables on the routine's
   environment** (never in git).
3. Verify with the G1/G2 gate above — the scheduled fire should now show live
   calendar + inbox and file no `MCP_BIND_FAILURE`.

To later move off a personal token, switch to a service account with domain-wide
delegation (needs a Workspace super-admin) — same env-var wiring.

## After a successful fix

Because the AM Tick reads the previous journal entry, write the first restored
entry so it explicitly notes "Calendar/Gmail restored; prior 'security rollover'
label retired" — so no stale offline explanation gets carried forward. Then mark
the root-cause incident RESOLVED in `ops-incidents.md`.
