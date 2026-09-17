# Ops Incidents

Append-only journal. One `## <ISO-8601Z> | <label>` entry per Tick; the harness reads the last header as its "since" marker.

## 2026-09-04T14:16:00Z | MED | chief-of-staff | content-producer journal stale >48h — M4 grace

content-producer's last entry is the brief-builder run on 2026-09-04; creation-pod is not built yet, so the daily queue check has nothing to write. Standing grace until M4 lands; re-evaluate weekly.

## 2026-09-16T13:50:00Z | HIGH | revops-watchdog | Event registration sync exits every enrollment at step 1

`workflow_health` shows first_step_exit_rate 1.0 on workflow 900001007 (24h). Handoff written to chief-of-staff; needs a human to inspect the enrollment trigger in ~~crm.

## 2026-09-17T15:44:14Z | HIGH | revops-watchdog | Event registration sync exits every enrollment at step 1 — day 2

`workflow_health` shows first_step_exit_rate 1.0 on workflow 900001007 for the second consecutive day (18/18 exits, 24h). Handoff `revops-watchdog_handoff_01m2r0mdwp_3qv10n` written and re-read in `handoffs`; the day-1 handoff is still pending acknowledgment.

## 2026-09-17T15:44:14Z | MED | revops-watchdog | SAL→SQL CVR 28.6% below 35% threshold — day 4

Contact-only cohort 8/28 on day 17 MTD (MQL 41, low-N gate met). Handoff `revops-watchdog_handoff_01m2r0mdwp_k02v1j` written.

## 2026-09-17T15:47:56Z | MED | chief-of-staff | content-producer journal stale 310h (threshold: 48h)

## 2026-09-17T15:49:53Z | LOW | Scribe | WBR traffic rows incomplete; Notion topic sync skipped

**Id:** `scribe_incident_01m2r0yry6_kfg0v3`
performance-marketer gtm_scorecard (2026-09-16) has no organic_users, channel_users or September MTD rows; WBR Traffic section published partial (organic sessions Apr-Aug). Topic review data source not reachable via notion-search; sync pull/push skipped (pull-before-push rule), retry next tick. wbr/2026-09-17.md audit artifact not saved: file write denied by permission prompt.
