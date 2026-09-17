# revops-watchdog — Journal

Append-only journal. One `## <ISO-8601Z> | <label>` entry per Tick; the harness reads the last header as its "since" marker.


## 2026-09-14T13:44:00Z | Daily Tick

### Anchor
Monday 2026-09-14 · Q3 2026 · day 14 of the month.

### MCP Preflight
~~crm (HubSpot) → bound · ~~knowledge base (Notion) → bound · ~~issue tracker (Linear) → bound · ~~chat (Slack) → bound

### Funnel Snapshot
| Metric | Value | 4-wk baseline | Δ | Severity |
|---|---|---|---|---|
| MQL (MTD) | 31 | — | — | — |
| SAL | 22 | — | — | — |
| SQL | 6 | — | — | — |
| MQL→SAL CVR | 71.0% | 61.5 | — | CLEAR (>55%) |
| SAL→SQL CVR | 27.3% | 34.9 | -21.8% | **MED** |
| Pipeline | $1,142,000 | — | — | CLEAR |

**SAL→SQL note:** 27.3% (6/22) breaches the <35% absolute threshold — first consecutive MED day.

**DB:** `funnel_snapshots` row for 2026-09-14 written and re-read.

### Workflow Health
8 workflows checked. None flagged.

### Scoring Drift
median 51.1 (Δ +9.1 pts/10d) · top decile ~10.5% — within band.

### Kestrel Coverage
new contacts 7d: 68 · both ids populated: 100.0% — CLEAR.

### Anomalies Written
- [MED] funnel / sal_to_sql_cvr: SAL→SQL CVR 27.3% below the 35% threshold


### Handoffs Written
- **id=revops-watchdog_handoff_01m1t0878e_h8wq6z** | MED | "Funnel anomaly — SAL→SQL CVR 27.3% (Day 14 MTD, below 35% threshold)" → chief-of-staff (resolved)
- **id=revops-watchdog_handoff_01m1t088w0_xjxw5j** | LOW | "revops-watchdog Daily Tick — Mon 2026-09-14 | SAL→SQL MED, else clear" → chief-of-staff (resolved)

## 2026-09-15T13:44:00Z | Daily Tick

### Anchor
Tuesday 2026-09-15 · Q3 2026 · day 15 of the month.

### MCP Preflight
~~crm (HubSpot) → bound · ~~knowledge base (Notion) → bound · ~~issue tracker (Linear) → bound · ~~chat (Slack) → bound

### Funnel Snapshot
| Metric | Value | 4-wk baseline | Δ | Severity |
|---|---|---|---|---|
| MQL (MTD) | 34 | — | — | — |
| SAL | 25 | — | — | — |
| SQL | 6 | — | — | — |
| MQL→SAL CVR | 73.5% | 61.5 | — | CLEAR (>55%) |
| SAL→SQL CVR | 24.0% | 34.9 | -31.2% | **MED** |
| Pipeline | $1,087,331 | — | — | CLEAR |

**SAL→SQL note:** 24.0% (6/25) breaches the <35% absolute threshold — second consecutive MED day.

**DB:** `funnel_snapshots` row for 2026-09-15 written and re-read.

### Workflow Health
8 workflows checked. None flagged.

### Scoring Drift
median 52.4 (Δ +10.4 pts/10d) · top decile ~10.5% — drift flag set.

### Kestrel Coverage
new contacts 7d: 50 · both ids populated: 100.0% — CLEAR.

### Anomalies Written
- [MED] funnel / sal_to_sql_cvr: SAL→SQL CVR 24.0% below the 35% threshold


### Handoffs Written
- **id=revops-watchdog_handoff_01m1t08a8a_na8daj** | MED | "Funnel anomaly — SAL→SQL CVR 24.0% (Day 15 MTD, below 35% threshold)" → chief-of-staff (acknowledged)
- **id=revops-watchdog_handoff_01m1t08bj3_9fv4yd** | LOW | "revops-watchdog Daily Tick — Tue 2026-09-15 | SAL→SQL MED, else clear" → chief-of-staff (resolved)

## 2026-09-16T13:44:00Z | Daily Tick

### Anchor
Wednesday 2026-09-16 · Q3 2026 · day 16 of the month.

### MCP Preflight
~~crm (HubSpot) → bound · ~~knowledge base (Notion) → bound · ~~issue tracker (Linear) → bound · ~~chat (Slack) → bound

### Funnel Snapshot
| Metric | Value | 4-wk baseline | Δ | Severity |
|---|---|---|---|---|
| MQL (MTD) | 37 | — | — | — |
| SAL | 26 | — | — | — |
| SQL | 7 | — | — | — |
| MQL→SAL CVR | 70.3% | 61.5 | — | CLEAR (>55%) |
| SAL→SQL CVR | 26.9% | 34.9 | -22.9% | **MED** |
| Pipeline | $1,126,093 | — | — | CLEAR |

**SAL→SQL note:** 26.9% (7/26) breaches the <35% absolute threshold — third consecutive MED day.

**DB:** `funnel_snapshots` row for 2026-09-16 written and re-read.

### Workflow Health
8 workflows checked. Flagged: Event registration sync — first-step exit rate 100% (HIGH).

### Scoring Drift
median 53.7 (Δ +11.7 pts/10d) · top decile ~10.5% — drift flag set.

### Kestrel Coverage
new contacts 7d: 59 · both ids populated: 100.0% — CLEAR.

### Anomalies Written
- [MED] funnel / sal_to_sql_cvr: SAL→SQL CVR 26.9% below the 35% threshold
- [HIGH] workflow / first_step_exit_rate: Event registration sync exits every enrollment at step 1

### Handoffs Written
- **id=revops-watchdog_handoff_01m1t08dbc_9egbd1** | MED | "Funnel anomaly — SAL→SQL CVR 26.9% (Day 16 MTD, below 35% threshold)" → chief-of-staff (pending)
- **id=revops-watchdog_handoff_01m1t08ejp_jkqkg0** | HIGH | "Workflow anomaly — 'Event registration sync' exits every enrollment at step 1" → chief-of-staff (pending)
- **id=revops-watchdog_handoff_01m1t08g6z_pd66v0** | LOW | "revops-watchdog Daily Tick — Wed 2026-09-16 | SAL→SQL MED + workflow HIGH" → chief-of-staff (resolved)

## 2026-09-17T15:45:21Z | Daily Tick

### Anchor
Thursday 2026-09-17 · September · Q3 2026 · day 17 of the month. Harness run (sync, migrations, commit handled by `scripts/tick.py`).

### MCP Preflight
DEMO_MODE=1, one probe each. ~~crm (HubSpot) → bound · ~~knowledge base (Notion) → bound · ~~issue tracker (Linear) → bound · ~~chat (Slack) → bound

### Handoffs Read
No entries addressed to revops-watchdog since 2026-09-16T13:44:00Z. Status of my open items: SAL→SQL MED `revops-watchdog_handoff_01m1t08dbc_9egbd1` pending; workflow HIGH `revops-watchdog_handoff_01m1t08ejp_jkqkg0` pending (not acknowledged).

### Funnel Snapshot
| Metric | Value | 4-wk baseline | Δ | Severity |
|---|---|---|---|---|
| MEL (MTD) | 238 | — | — | — |
| MQL (MTD) | 41 (P1 9 · P2 23 · Outbound 9) | — | — (cumulative MTD; not compared to its own average) | — |
| SAL | 28 | — | — | — |
| SQL | 8 | — | — | — |
| MQL→SAL CVR | 68.3% | 62.9% | +8.6% | CLEAR (>55%; no 3-day downtrend: 71.0 → 73.5 → 70.3) |
| SAL→SQL CVR | 28.6% | 34.3% | -16.6% | **MED** |
| Pipeline | $1,137,093 (89 open deals) | $1,030,261 | 7-day avg $1,106,494, +7.4% | CLEAR |

**SAL→SQL note:** 28.6% (8/28) breaches the <35% absolute threshold; low-N gate met (MQL 41 ≥ 20). Day 4 of the same watch item.
**Pipeline note:** total is the fixture-declared sum of the 89 deal amounts; an independent re-sum via `scripts/demo/connector.py` failed (system python lacks the `mcp` module).
**DB:** `funnel_snapshots` row for 2026-09-17 written and re-read. Baseline n=20 snapshots (≥14).

### Workflow Health
8 workflows checked. Flagged: Event registration sync (900001007) — first-step exit 100% (18/18), HIGH, day 2; last_updated 2026-09-15. No workflow-spec artifact available.
Noted, not flagged: Lifecycle backfill action_failures_24h = 1 (no threshold defined). Workflow 900001006 name now reads "Nurture - top-of-funnel" (was "Nurture — top-of-funnel"); same id, not a new workflow. No zero-enrollment workflows.

### Scoring Drift
median 55.9 (Δ +7.4 pts/7d vs 48.5 on 2026-09-10; rule window is 7 days) — under threshold. Top decile 231 contacts / 10.6% (prior week 9.6% on 2026-09-11) — no shrink. Compared on share: the scored base is 2,184 against stored prior counts near 20, so the count is not comparable. drift_flag=0.
The 2026-09-15 and 2026-09-16 drift flags used a 10-day window; on the rule's own 7-day window neither crossed.

### Kestrel Coverage
quick mode, 0 excluded. new contacts 7d: 20 · person_id 100.0% (Δ +6.2 pp) · company_id 95.0% (Δ +1.2 pp) · both populated 95.0% (19) · neither 0.0% — CLEAR.

### Anomalies Written
- [MED] funnel / sal_to_sql_cvr: SAL→SQL CVR 28.6% below the 35% threshold (day 4) — `revops-watchdog_anomaly_01m2r0mdvs_rewkb3`
- [HIGH] workflow / first_step_exit_rate: Event registration sync exits every enrollment at step 1 (day 2) — `revops-watchdog_anomaly_01m2r0mdvs_fjzwx7`

### Handoffs Written
- **id=revops-watchdog_handoff_01m2r0mdwp_k02v1j** | MED | "Funnel anomaly — SAL→SQL CVR 28.6% (Day 17 MTD, below 35% threshold) — day 4" → chief-of-staff (pending)
- **id=revops-watchdog_handoff_01m2r0mdwp_3qv10n** | HIGH | "Workflow anomaly — 'Event registration sync' exits every enrollment at step 1 — day 2" → chief-of-staff (pending)
- **id=revops-watchdog_handoff_01m2r0mdwp_wv4nvf** | LOW | "revops-watchdog Daily Tick — Thu 2026-09-17 | SAL→SQL MED (day 4) + workflow HIGH (day 2)" → chief-of-staff (resolved)

Verified: both MED/HIGH have `anomalies` and `handoffs` rows (re-read). Entries also appended to `state/journal/handoffs.md` and `state/journal/ops-incidents.md`.
- Harness: session=87e1539d-e9c0-4569-8e18-cfb39e85a745 turns=36 cost=$2.43
