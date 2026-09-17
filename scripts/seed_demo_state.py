#!/usr/bin/env python3
"""
seed_demo_state.py — rebuild state/ with synthetic, profile-consistent demo data.

    python3 scripts/seed_demo_state.py [--profile orrery] [--as-of YYYY-MM-DD|today|yesterday] [--seed 42] [--force]

What it writes (everything deterministic for a given --seed/--as-of):
  state/working/fleet.db          rebuilt from state/working/migrations/*.sql, then seeded
  state/working/schema.sql        regenerated from the fresh DB (never hand-edit)
  state/journal/*.md              2-3 entries per agent in the formats the prompts parse
  state/journal/handoffs.md       entries whose ids/timestamps match the `handoffs` rows
  state/journal/ops-incidents.md, state/journal/chief-of-staff-meditations.md
  state/pending/<as-of>/content-researcher-topic-backlog.md, state/working/briefs/brief-0001.md
  state/identity/scribe-pm-cadence.yaml   members/default owner rewritten from the profile
  state/demo-outbox/                      emptied and given a README (DEMO_MODE write target)

The planted story: a SAL→SQL conversion dip over the last three ticks (MED anomaly →
handoff → chief-of-staff brief → Scribe WBR), one HIGH workflow-health flag, one stale content-producer
journal (so chief-of-staff's cross-agent audit has something to report), and a 4-week
keyword-ranking history. No row carries anything real.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts import fleet_paths  # noqa: E402
from scripts.ids import mint  # noqa: E402

PLUGIN_ROOT = fleet_paths.PLUGIN_ROOT
OPERATOR = "Scott McKeighen"


# ----------------------------------------------------------------------------- helpers
def business_days_back(as_of: date, n: int) -> list[date]:
    """n weekdays ending at (and including) as_of if it is a weekday, oldest first."""
    days, d = [], as_of
    while len(days) < n:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    return list(reversed(days))


def ts(d: date, hh: int, mm: int = 0, ss: int = 0) -> str:
    return datetime(d.year, d.month, d.day, hh, mm, ss, tzinfo=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso(d: date) -> str:
    return d.isoformat()


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


class Seeder:
    def __init__(self, root: Path, profile: str, as_of: date, seed: int):
        self.root = root
        self.tokens = self.load_profile(profile)
        self.profile = profile
        self.as_of = as_of
        self.rng = random.Random(seed)
        self._mint_ms = int(datetime(as_of.year, as_of.month, as_of.day, tzinfo=timezone.utc).timestamp() * 1000) - 10 * 86400_000
        self.days = business_days_back(as_of, 22)   # ~1 month of weekday ticks
        self.recent = self.days[-3:]                # the three ticks that carry the story
        self.journal_dir = root / "state" / "journal"
        self.db_path = root / "state" / "working" / fleet_paths.DB_NAME
        self.handoff_log: list[tuple[str, str]] = []  # (timestamp, markdown entry)

    @staticmethod
    def load_profile(profile: str) -> dict:
        pdir = PLUGIN_ROOT / "profiles" / profile
        tokens: dict = {}
        for fn in ("profile.yaml", "connectors.yaml"):
            f = pdir / fn
            if f.exists():
                tokens.update((yaml.safe_load(f.read_text()) or {}).get("tokens") or {})
        if not tokens:
            sys.exit(f"profile {profile!r} not found under {pdir}")
        return {k: str(v) for k, v in tokens.items()}

    def t(self, key: str) -> str:
        return self.tokens[key]

    def mint(self, agent: str, kind: str) -> str:
        self._mint_ms += 1000 + self.rng.randint(0, 900)
        return mint(agent, kind, now_ms=self._mint_ms, rand_bytes=bytes(self.rng.randint(0, 255) for _ in range(4)))

    # ------------------------------------------------------------------ database
    def rebuild_db(self, force: bool):
        if self.db_path.exists():
            if not force:
                sys.exit(f"{self.db_path} exists — pass --force to rebuild")
            self.db_path.unlink()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        sqlite3.connect(self.db_path).close()  # create the empty file the migration runner expects
        from scripts import tick
        tick.DB_PATH = self.db_path
        tick.MIGRATIONS_DIR = fleet_paths.MIGRATIONS_DIR
        applied = tick.run_pending_migrations()
        print(f"[seed] migrations applied: {len(applied)}")

    def seed_db(self):
        con = sqlite3.connect(self.db_path)
        cur = con.cursor()
        rng = self.rng
        days = self.days
        as_of = self.as_of
        t = self.t

        def ins(table: str, rows: list[dict]):
            if not rows:
                return
            cols = list(rows[0].keys())
            cur.executemany(
                f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' for _ in cols)})",
                [tuple(r[c] for c in cols) for r in rows],
            )

        # ---- revops-watchdog: funnel_snapshots (MTD accumulation, planted SAL→SQL dip on the last 3 ticks)
        snaps = []
        mqls = sals = sqls = 0
        month_start = None
        for i, d in enumerate(days):
            if month_start != d.month:
                month_start, mqls, sals, sqls = d.month, 0, 0, 0
            mqls += rng.randint(2, 5)
            sals += rng.randint(1, 3)
            dip = d in self.recent
            sqls += (0 if dip and rng.random() < 0.6 else rng.randint(0, 2))
            sals = min(sals, mqls)
            sqls = min(sqls, sals)
            sal_rate = round(100 * sals / mqls, 1) if mqls else 0
            sql_rate = round(100 * sqls / sals, 1) if sals else 0
            if dip and sql_rate > 31:
                sqls = max(1, int(sals * 0.31))
                sql_rate = round(100 * sqls / sals, 1)
            pipeline = round(900_000 + i * 11_000 + rng.randint(-40_000, 40_000), 2)
            note = f"Day {d.day} MTD. MQL {mqls} / SAL {sals} / SQL {sqls}."
            if dip:
                note += f" SAL→SQL {sql_rate}% below the 35% absolute threshold — MED."
            snaps.append(dict(agent="revops-watchdog", snapshot_date=iso(d), mqls=mqls, sals=sals, sqls=sqls,
                              pipeline_value=pipeline, mql_to_sal_rate=sal_rate, sal_to_sql_rate=sql_rate,
                              notes=note, created_at=ts(d, 13, 40)))
        ins("funnel_snapshots", snaps)
        self.snaps = snaps

        # ---- revops-watchdog: opsos_signals (enrichment coverage; one MED day)
        opsos = []
        for i, d in enumerate(days):
            new = rng.randint(40, 80)
            cov = 0.64 if i == 9 else round(rng.uniform(0.93, 1.0), 3)
            opsos.append(dict(agent="revops-watchdog", check_date=iso(d), new_contacts_7d=new, enriched_count=int(new * cov),
                              coverage_pct=round(cov * 100, 1),
                              field_coverage_json=json.dumps({"person_id": round(cov * 100, 1), "company_id": round(cov * 100, 1)}),
                              flag=("MED" if cov < 0.7 else None), created_at=ts(d, 13, 41)))
        ins("opsos_signals", opsos)

        # ---- revops-watchdog: workflow_health (8 workflows × 5 days; one HIGH)
        wfs = [("900001001", "MQL routing"), ("900001002", "SAL auto-accept"), ("900001003", "Disqualification sweep"),
               ("900001004", "Demo-request alert"), ("900001005", "Lifecycle backfill"), ("900001006", "Nurture — top-of-funnel"),
               ("900001007", "Event registration sync"), ("900001008", "Re-engagement")]
        wh = []
        for d in days[-5:]:
            for wid, name in wfs:
                enr = rng.randint(5, 60)
                rate = round(rng.uniform(0.0, 0.15), 3)
                flag = None
                if wid == "900001007" and d == self.recent[-1]:
                    rate, flag = 1.0, "HIGH"
                wh.append(dict(agent="revops-watchdog", check_date=iso(d), workflow_id=wid, workflow_name=name, enrollments_24h=enr,
                               exits_24h=int(enr * rate), first_step_exit_rate=rate, is_active=1, flag=flag, created_at=ts(d, 13, 42)))
        ins("workflow_health", wh)

        # ---- revops-watchdog: scoring_drift (10 days; median creeping up)
        sd = []
        for i, d in enumerate(days[-10:]):
            med = 42 + i * 1.3
            sd.append(dict(agent="revops-watchdog", snapshot_date=iso(d), median_score=round(med, 1), top_decile_count=rng.randint(18, 26),
                           top_decile_pct=round(rng.uniform(9.5, 11.5), 1),
                           distribution_json=json.dumps({"p25": round(med - 15, 1), "p50": round(med, 1), "p75": round(med + 14, 1)}),
                           drift_flag=int(i >= 8), drift_note=("median +10 pts over 10 days — review scoring inputs" if i >= 8 else None),
                           created_at=ts(d, 13, 43)))
        ins("scoring_drift", sd)

        # ---- performance-marketer: keyword_rankings (20 keywords × 4 weekly snapshots)
        kw_file = PLUGIN_ROOT / "roster" / "performance-marketer" / "references" / "tracked-keywords.txt"

        def kw_render(line: str) -> str:
            # The base keywords file is tokenized ({{company_slug}} …); seeded rows must
            # carry rendered keywords, never raw profile tokens.
            for k, v in self.tokens.items():
                line = line.replace("{{" + k + "}}", v)
            return line

        keywords = [kw_render(l.strip()) for l in kw_file.read_text().splitlines() if l.strip() and not l.startswith("#")][:20] if kw_file.exists() else []
        if len(keywords) < 20:
            keywords += [f"{t('COMPANY').lower()} alternative {i}" for i in range(20 - len(keywords))]
        weeks = [as_of - timedelta(days=7 * k) for k in (3, 2, 1, 0)]
        kr, prior = [], {}
        for wk in weeks:
            for k in keywords:
                pos = max(1, (prior.get(k) or rng.randint(4, 40)) + rng.randint(-3, 3))
                delta = (prior[k] - pos) if k in prior else None
                kr.append(dict(agent="performance-marketer", snapshot_date=iso(wk), keyword=k, position=pos, prior_position=prior.get(k),
                               position_delta=delta, search_volume=rng.choice([90, 210, 480, 1300, 2900]),
                               url=f"https://{t('COMPANY_DOMAIN')}/blog/{k.replace(' ', '-')[:40]}",
                               flag=("WATCH" if delta is not None and delta <= -3 else None), created_at=ts(wk, 15, 30)))
                prior[k] = pos
        ins("keyword_rankings", kr)

        # ---- performance-marketer: paid_creative (12 ads × 7 days), spend_alerts, experiments, proposals, applied_changes
        campaigns = [("Brand — Core", "brand"), ("Nonbrand — Incident Mgmt", "nonbrand"), ("Competitor — Conquest", "competitor")]
        ads = [(c, g, f"ad-{i:03d}") for i, (c, g) in enumerate((c, g) for c, g in campaigns for _ in range(4))]
        pc = []
        # Stable per-campaign bases with a small jitter, so the seeded week reads as a calm
        # paid account (the fixture plants today's spike). The four rng calls per ad-day are
        # kept exactly as before — every downstream seeded value is a positional draw.
        base = {"Brand — Core": (1200, 0.065, 4.2, 0.055), "Nonbrand — Incident Mgmt": (2600, 0.045, 7.4, 0.045),
                "Competitor — Conquest": (1000, 0.030, 9.5, 0.027)}
        # Planted day-level bumps (campaign, days-from-end) → the seeded spend_alerts below and
        # the seeded journal's Spend Check lines describe exactly these.
        bumps = {("Brand — Core", 5): 1.12, ("Nonbrand — Incident Mgmt", 4): 1.12, ("Competitor — Conquest", 3): 1.30,
                 ("Brand — Core", 2): 1.15, ("Nonbrand — Incident Mgmt", 1): 1.32}
        for k, d in enumerate(days[-7:]):
            for camp, grp, cid in ads:
                b_imp, b_ctr, b_cpc, b_cvr = base[camp]
                j1 = (rng.randint(400, 6000) - 400) / 5600          # 0..1 jitter (same call as before)
                j2 = (rng.uniform(0.02, 0.08) - 0.02) / 0.06
                j3 = (rng.uniform(2.5, 9.0) - 2.5) / 6.5
                j4 = (rng.uniform(0.02, 0.09) - 0.02) / 0.07
                bump = bumps.get((camp, 7 - k), 1.0)
                imp = int(b_imp * (0.92 + 0.16 * j1) * bump)
                clicks = int(imp * b_ctr * (0.95 + 0.10 * j2))
                spend = round(clicks * b_cpc * (0.96 + 0.08 * j3), 2)
                conv = int(clicks * b_cvr * (0.90 + 0.20 * j4))
                pc.append(dict(agent="performance-marketer", platform="google_ads", campaign_name=camp, ad_group=grp, creative_id=cid,
                               headline=f"{t('COMPANY')} — on-call without the noise", description="Clear ownership, fast response, learning loops.",
                               impressions=imp, clicks=clicks, ctr=round(clicks / imp, 4), spend=spend, conversions=conv,
                               cpl=(round(spend / conv, 2) if conv else None), status="enabled", snapshot_date=iso(d), created_at=ts(d, 15, 31)))
        ins("paid_creative", pc)
        self.pc, self.campaigns = pc, campaigns
        sa = []
        for i, d in enumerate(days[-5:]):
            sev = ["LOW", "LOW", "MED", "LOW", "MED"][i]
            camp_i = campaigns[i % 3][0]
            value, baseline, dev = self.spend_vs_trailing(camp_i, d)          # from the rows above
            sid = self.mint("performance-marketer", "spendalert")              # same draw order as before: id, then the three value draws
            rng.uniform(300, 700); rng.uniform(280, 520); rng.uniform(-18, 42)  # draws kept in place
            sa.append(dict(id=sid, agent="performance-marketer", detected_at=ts(d, 15, 32), platform="google_ads",
                           campaign_name=camp_i, metric="daily_spend", value=round(value, 2),
                           baseline=round(baseline, 2), deviation_pct=round(dev, 1), severity=sev,
                           description=f"Daily spend vs 7-day average on {campaigns[i % 3][0]}", status=("open" if i >= 3 else "resolved"),
                           resolved_at=(None if i >= 3 else ts(d + timedelta(days=1), 15)), created_at=ts(d, 15, 32)))
        ins("spend_alerts", sa)
        ins("experiments", [
            dict(agent="performance-marketer", name="Nonbrand headline: outcome vs feature", platform="google_ads",
                 hypothesis="Outcome-led headlines lift CTR ≥15% on nonbrand", variant_a="Incident management for platform teams",
                 variant_b="Cut MTTR in half without more alerts", start_date=iso(days[-10]), end_date=None, status="active", outcome=None,
                 notes="Shadow-mode experiment; no live write.", created_at=ts(days[-10], 15, 33)),
            dict(agent="performance-marketer", name="Competitor conquest: tCPA 120 vs 150", platform="google_ads",
                 hypothesis="Lower tCPA holds volume on conquest terms", variant_a="tCPA 150", variant_b="tCPA 120",
                 start_date=iso(days[-20]), end_date=iso(days[-6]), status="completed", outcome="inconclusive — volume fell 22%",
                 notes=None, created_at=ts(days[-20], 15, 33)),
        ])
        props = []
        for i, (bucket, op, camp, summ) in enumerate([
            ("auto_3a", "add_negative", "Nonbrand — Incident Mgmt", "Add negative 'free pager app' on Nonbrand — Incident Mgmt"),
            ("auto_3a", "set_bid", "Nonbrand — Incident Mgmt", "Raise bid +8% on 'incident management platform' (pos 4.2, CVR 6.1%)"),
            ("human_3b", "budget", "Nonbrand — Incident Mgmt", "Shift $40/day from Brand — Core to Nonbrand — Incident Mgmt"),
            ("creative", "creative", "Competitor — Conquest", "Refresh 2 headlines on Competitor — Conquest (CTR below floor)"),
        ]):
            props.append(dict(agent="performance-marketer", dossier_date=iso(days[-2]), platform="google_ads", campaign_name=camp, bucket=bucket,
                              op_type=op, summary=summ, reason="From the weekly position pass", prior_value=json.dumps({"value": "current"}),
                              target_value=json.dumps({"value": "proposed"}), reversal_if="CVR drops >20% over 7 days",
                              linear_ref=("MAR-7076" if bucket == "creative" else None), approval_id=None,
                              status=["applied", "applied", "proposed", "awaiting_creative"][i],
                              decided_at=(ts(days[-1], 16) if i < 2 else None), created_at=ts(days[-2], 15, 35)))
        ins("paid_change_proposals", props)
        ins("applied_changes", [dict(agent="performance-marketer", proposal_id=1, approval_ref="decision:3", platform="google_ads",
                                     entity="campaign:Nonbrand — Incident Mgmt/negative:free pager app", op_type="add_negative", prior_value=json.dumps({"negatives": []}),
                                     new_value=json.dumps({"negatives": ["free pager app"], "match_type": "phrase"}),
                                     mode="shadow", applied_at=ts(days[-1], 16, 4), rolled_back_at=None, created_at=ts(days[-1], 16, 4)),
                                dict(agent="performance-marketer", proposal_id=2, approval_ref="decision:3", platform="google_ads",
                                     entity="keyword:incident management platform", op_type="set_bid", prior_value="3.40", new_value="3.67",
                                     mode="shadow", applied_at=ts(days[-1], 16, 5), rolled_back_at=None, created_at=ts(days[-1], 16, 5))])

        # ---- shared: anomalies, handoffs, decisions, approvals
        anomalies, handoffs = [], []
        sev_cycle = ["LOW", "MED", "HIGH", "LOW", "MED", "MED", "LOW", "MED"]
        status_cycle = ["resolved", "resolved", "acknowledged", "resolved", "open", "open", "resolved", "open"]
        for i in range(8):
            d = days[-8 + i]
            snap = snaps[-8 + i]
            is_funnel = i % 2 == 1 or i >= 5
            metric = "sal_to_sql_cvr" if is_funnel else ["opsos_coverage_pct", "first_step_exit_rate", "median_score", "daily_spend"][i % 4]
            anomalies.append(dict(id=self.mint("revops-watchdog", "anomaly"), agent="revops-watchdog", detected_at=ts(d, 13, 44),
                                  surface=("funnel" if is_funnel else "workflow"), metric=metric,
                                  value=(snap["sal_to_sql_rate"] if is_funnel else round(rng.uniform(0.3, 1.0), 2)),
                                  baseline=(34.9 if is_funnel else 0.1), deviation_pct=round(rng.uniform(-35, -8), 1), severity=sev_cycle[i],
                                  description=(f"SAL→SQL CVR {snap['sal_to_sql_rate']}% on day {d.day} MTD, below the 35% threshold"
                                               if is_funnel else f"{metric} outside its 4-week band"),
                                  status=status_cycle[i], resolved_at=(ts(d + timedelta(days=1), 15) if status_cycle[i] == "resolved" else None),
                                  created_at=ts(d, 13, 44)))
        # The planted workflow HIGH (900001007, last seeded day) must exist as an
        # anomalies row too — the seeded journal claims it was written, and a live
        # revops-watchdog tick audits that claim against the table.
        anomalies.append(dict(id=self.mint("revops-watchdog", "anomaly"), agent="revops-watchdog",
                              detected_at=ts(self.recent[-1], 13, 44), surface="workflow",
                              metric="first_step_exit_rate", value=1.0, baseline=0.1,
                              deviation_pct=900.0, severity="HIGH",
                              description="Event registration sync (900001007) exits every enrollment at step 1",
                              status="open", resolved_at=None, created_at=ts(self.recent[-1], 13, 44)))
        self.anomalies = anomalies

        def handoff(from_a, to_a, sev, subject, body, d, hh, mm, status, ack=None, res=None):
            hid = self.mint(from_a.lower(), "handoff")
            created = ts(d, hh, mm)
            handoffs.append(dict(id=hid, from_agent=from_a, to_agent=to_a, subject=subject, body=body, severity=sev, status=status,
                                 created_at=created, acknowledged_at=ack, resolved_at=res))
            self.handoff_log.append((created, f"## {created} | {from_a} → {to_a} | {sev}: {subject}\n\n**Id:** `{hid}`\n{body}\n"))
            return hid

        for j, d in enumerate(self.recent):
            snap = snaps[-3 + j]
            body = (f"**Severity:** MED\n**Surface:** funnel\n**Metric:** sal_to_sql_cvr\n**Value:** {snap['sal_to_sql_rate']}% "
                    f"({snap['sqls']}/{snap['sals']})\n**Baseline (4-wk avg):** 34.9%\n**Deviation:** "
                    f"{round((snap['sal_to_sql_rate'] - 34.9) / 34.9 * 100, 1)}%\n**Recommended action:** "
                    f"{'Fresh finding — curate for the AM brief.' if j == 0 else f'Day {j + 1} of the same watch item; count, not a fresh ask.'}\n"
                    f"**Tier gate:** 1 (chief-of-staff curates for brief)")
            status = ["resolved", "acknowledged", "pending"][j]
            handoff("revops-watchdog", "chief-of-staff", "MED",
                    f"Funnel anomaly — SAL→SQL CVR {snap['sal_to_sql_rate']}% (Day {d.day} MTD, below 35% threshold)", body, d, 13, 45,
                    status, ack=(ts(d, 14, 25) if status != "pending" else None), res=(ts(d, 16) if status == "resolved" else None))
            if j == 2:
                handoff("revops-watchdog", "chief-of-staff", "HIGH",
                        "Workflow anomaly — 'Event registration sync' exits every enrollment at step 1",
                        "**Severity:** HIGH\n**Surface:** workflow\n**Workflow:** 900001007 (Event registration sync)\n"
                        "**Metric:** first_step_exit_rate 100% — every enrollment exits at step 1\n"
                        "**Recommended action:** pause the workflow's step-1 branch and check the enrollment filter.\n"
                        "**Tier gate:** 1 (chief-of-staff curates for brief)",
                        d, 13, 45, "pending")
            marker_subject = "SAL→SQL MED + workflow HIGH" if j == 2 else "SAL→SQL MED, else clear"
            marker_body = ("Tick-complete marker. Workflow HIGH (Event registration sync) and the funnel MED above; "
                           "scoring drift and enrichment coverage CLEAR." if j == 2 else
                           "Tick-complete marker. Workflow health, scoring drift, enrichment coverage all CLEAR except the funnel item above.")
            handoff("revops-watchdog", "chief-of-staff", "LOW", f"revops-watchdog Daily Tick — {d.strftime('%a')} {iso(d)} | {marker_subject}",
                    marker_body,
                    d, 13, 46, "resolved", ack=ts(d, 14, 25), res=ts(d, 14, 25))
        handoff("performance-marketer", "chief-of-staff", "MED", f"Weekly GTM Scorecard (traffic) — data through {iso(days[-2])}",
                "**Tier gate:** 2 — traffic block ready for the WBR; needs the revops-watchdog funnel block to be complete.\n**Ask:** greenlight the scorecard for Wednesday's WBR.",
                days[-2], 15, 40, "acknowledged", ack=ts(days[-2], 16, 10))
        handoff("performance-marketer", "Scribe", "LOW", "Weekly GTM Scorecard traffic block ready", "Rows written to `gtm_scorecard` for this week.",
                days[-2], 15, 41, "resolved", ack=ts(days[-2], 17), res=ts(days[-2], 17))
        handoff("Scribe", "chief-of-staff", "LOW", f"WBR posted for {iso(days[-1])}",
                f"WBR draft posted to ~~knowledge base (Notion) and section owners pinged in #team-marketing: {t('HEAD_OF_MARKETING')}, "
                f"{t('CONTENT_LEAD')}, {t('DESIGN_LEAD')}, {OPERATOR}. Deadline Thursday 07:00 PT.", days[-1], 17, 5, "pending")
        handoff("Scribe", "content-researcher", "MED", "Topic backlog mirrored to Notion — 2 approved, 1 needs_edit",
                f"{t('HEAD_OF_MARKETING_FIRST')}'s rulings applied via scripts/topic_review.py. Approved topics are now content-producer's queue.",
                days[-1], 17, 18, "acknowledged", ack=ts(days[-1], 17, 30))
        handoff("chief-of-staff", "chief-of-staff", "LOW", "PM carry-forward", "Open decision: SAL→SQL watch — keep watching vs. escalate to sales leadership.",
                days[-1], 1, 10, "resolved", ack=ts(days[-1], 1, 10), res=ts(days[-1], 1, 10))
        handoff("content-researcher", "chief-of-staff", "LOW", "Weekly Tick — 3 topics submitted for review",
                "Research packets: call_mining (6 calls), social_listening (14 threads), competitor_content (5 pages).",
                monday_of(as_of), 16, 55, "resolved", ack=ts(monday_of(as_of), 17), res=ts(monday_of(as_of), 17))
        handoff("brand-designer", "chief-of-staff", "LOW", "dither-pack delivered — webinar hero set (5 channels)",
                f"Packet pending with {t('DESIGN_LEAD_FIRST')}; revision 0/3.", days[-12], 18, 20, "resolved",
                ack=ts(days[-12], 18, 30), res=ts(days[-11], 9))
        handoff("content-producer", "brand-designer", "MED", "dither-pack request — hero channel set for brief-0001",
                "**Source:** `fixtures/brand/orrery-hero-source.png`\n"
                "**Treatment:** `ink` ramp, bayer8, scale 2 (brand defaults)\n"
                "**Channels:** social, display, web, email\n"
                "**Needed for:** `content_drafts` id=1, the draft off `state/working/briefs/brief-0001.md` "
                "(\"Runbooks that engineers actually open\") — featured image plus the LinkedIn derivative "
                "in `derivative_assets` id=1.\n"
                "**Deadline:** with the draft's publish package\n"
                f"**Tier gate:** 2 ({t('DESIGN_LEAD_FIRST')} approves via chief-of-staff)",
                days[-1], 18, 12, "pending")
        handoff("Scott", "fleet", "LOW", f"Handoff resolved: id={handoffs[0]['id']}", "Reviewed in the AM brief thread. Watch continues.",
                self.recent[0], 16, 0, "resolved", ack=ts(self.recent[0], 16), res=ts(self.recent[0], 16))
        ins("anomalies", anomalies)
        ins("handoffs", handoffs)
        self.handoffs = handoffs

        ins("decisions", [
            dict(agent="chief-of-staff", context="SAL→SQL CVR below threshold 3 ticks running", decision="Keep watching; no sales-leadership escalation yet",
                 approved_by=OPERATOR, approved_at=ts(self.recent[0], 16), created_at=ts(self.recent[0], 16)),
            dict(agent="performance-marketer", context="Weekly position pass", decision="Greenlight auto_3a moves (negatives + bid) in shadow mode",
                 approved_by=OPERATOR, approved_at=ts(days[-1], 16), created_at=ts(days[-1], 16)),
            dict(agent="performance-marketer", context="Bid change on 'incident management platform'", decision="Apply +8% (shadow)",
                 approved_by=OPERATOR, approved_at=ts(days[-1], 16, 5), created_at=ts(days[-1], 16, 5)),
            dict(agent="scribe", context="WBR section ownership", decision=f"{t('HEAD_OF_MARKETING')} owns Project Updates; {OPERATOR} owns Summary and GTM Ops",
                 approved_by=OPERATOR, approved_at=ts(days[-15], 18), created_at=ts(days[-15], 18)),
            dict(agent="content-researcher", context="Topic review path", decision="Rulings come from the Notion review database, harvested by Scribe",
                 approved_by=t("HEAD_OF_MARKETING"), approved_at=ts(days[-18], 18), created_at=ts(days[-18], 18)),
        ])
        ins("approvals", [
            dict(agent="performance-marketer", tier=2, draft_type="optimization_dossier", draft_content=None, draft_path=f"state/pending/{iso(days[-2])}/performance-marketer-optimization-dossier.md",
                 slack_channel="#marketing-agent-approvals", slack_thread_ts="1786458135.000100", approver=OPERATOR, approved_at=ts(days[-1], 16),
                 status="approved", edit_notes=None, created_at=ts(days[-2], 15, 45)),
            dict(agent="content-researcher", tier=2, draft_type="topic_backlog", draft_content=None, draft_path=f"state/pending/{iso(monday_of(as_of))}/content-researcher-topic-backlog.md",
                 slack_channel="#marketing-agent-approvals", slack_thread_ts="1786458135.000200", approver=t("HEAD_OF_MARKETING"), approved_at=ts(days[-1], 17, 15),
                 status="approved", edit_notes="Topic 3 needs a sharper angle", created_at=ts(monday_of(as_of), 16, 56)),
            dict(agent="content-producer", tier=2, draft_type="brief", draft_content=None, draft_path="state/working/briefs/brief-0001.md",
                 slack_channel="#marketing-agent-approvals", slack_thread_ts="1786458135.000300", approver=None, approved_at=None,
                 status="pending", edit_notes=None, created_at=ts(days[-1], 18)),
            dict(agent="brand-designer", tier=2, draft_type="dither_pack", draft_content=None, draft_path=f"state/pending/{iso(days[-14])}/brand-designer-dither-pack.md",
                 slack_channel="#marketing-agent-approvals", slack_thread_ts="1786458135.000400", approver=None, approved_at=None,
                 status="expired", edit_notes=None, created_at=ts(days[-14], 18)),
        ])

        # ---- gtm_scorecard (8 metrics × 8 months × 2 agents)
        metrics = {"revops-watchdog": ["mel", "mql", "sal", "sql"], "performance-marketer": ["sessions", "organic_sessions", "paid_sessions", "demo_requests"]}
        sc = []
        for agent, ms in metrics.items():
            for k in range(8):
                period_date = (as_of.replace(day=1) - timedelta(days=1)).replace(day=1)
                for _ in range(k):
                    period_date = (period_date - timedelta(days=1)).replace(day=1)
                period = period_date.strftime("%Y-%m")
                for m in ms:
                    base = {"mel": 420, "mql": 95, "sal": 58, "sql": 21, "sessions": 48_000, "organic_sessions": 31_000, "paid_sessions": 9_000, "demo_requests": 140}[m]
                    val = round(base * (1 + 0.03 * (7 - k)) * rng.uniform(0.92, 1.08))
                    sc.append(dict(agent=agent, snapshot_date=iso(days[-1]), metric=m, period=period, value=val, is_complete=1, projected=None,
                                   flag=None, definition_version="v1.5", created_at=ts(days[-1], 15, 50)))
        ins("gtm_scorecard", sc)

        # ---- Scribe PM
        owners = [t("HEAD_OF_MARKETING"), t("CONTENT_LEAD"), t("DESIGN_LEAD"), OPERATOR]
        slug = t("LINEAR_WORKSPACE_SLUG")
        projects = []
        proj_names = ["Website repositioning", "Q3 webinar series", "Lead scoring model 2.0", "Use-case library", "Brand refresh",
                      "Partner co-marketing", "Event telemetry → CRM", "SEO content sprint", "Customer stories program", "Paid search restructure"]
        for i, name in enumerate(proj_names):
            owner = owners[i % 4]
            health = ["on_track", "on_track", "at_risk", "on_track", "off_track", "on_track", "on_track", "at_risk", "on_track", "on_track"][i]
            projects.append(dict(id=f"p{i + 1}", agent="scribe", name=name, owner=owner, outcome=f"{name} shipped and measured",
                                 quality_bar="Reviewed by the head of marketing", original_due_date=iso(as_of + timedelta(days=20 + i * 7)),
                                 current_target_date=iso(as_of + timedelta(days=20 + i * 7 + (7 if health != "on_track" else 0))), health=health,
                                 health_source="owner", brief_link=None, linear_link=f"https://linear.app/{slug}/project/{name.lower().replace(' ', '-')}-{i + 1}",
                                 short_description=f"{name}: scoped and in flight.", closed_at=None, off_track_acknowledged_at=None, off_track_decision=None,
                                 rca_required=0, rca_link=None, last_synced_at=ts(days[-1], 16), created_at=ts(days[-18], 16),
                                 owner_source="lead", status_type="started", start_date=iso(days[-18]), lead_name=owner))
        ins("pm_projects", projects)
        issues = []
        for i in range(40):
            pid = f"p{(i % 10) + 1}"
            num = 7001 + i
            state = ["active", "active", "stale", "blocked", "closed"][i % 5]
            issues.append(dict(id=f"i{i + 1}", agent="scribe", project_id=pid, title=f"Task {i + 1} for {proj_names[i % 10]}", owner=owners[i % 4],
                               status=("Done" if state == "closed" else "In Progress" if state == "active" else "Todo"), state=state,
                               due_date=iso(as_of + timedelta(days=(i % 14) - 3)), linear_link=f"https://linear.app/{slug}/issue/MAR-{num}",
                               short_description=None, last_activity_at=ts(days[-1 - (i % 12)], 12), closed_at=(ts(days[-2], 12) if state == "closed" else None),
                               last_synced_at=ts(days[-1], 16), created_at=ts(days[-15], 12), status_type=("completed" if state == "closed" else "started")))
        ins("pm_issues", issues)
        ins("pm_blockers", [dict(agent="scribe", project_id="p5", issue_id="i4", opened_at=ts(days[-7], 12), resolved_at=None,
                                 description="Waiting on legal review of new tagline", resolution_notes=None, created_at=ts(days[-7], 12)),
                            dict(agent="scribe", project_id="p3", issue_id=None, opened_at=ts(days[-9], 12), resolved_at=ts(days[-3], 12),
                                 description="Scoring inputs blocked on enrichment coverage", resolution_notes="Coverage recovered", created_at=ts(days[-9], 12)),
                            dict(agent="scribe", project_id="p8", issue_id="i18", opened_at=ts(days[-2], 12), resolved_at=None,
                                 description="Keyword brief awaiting content lead", resolution_notes=None, created_at=ts(days[-2], 12))])
        wk = iso(monday_of(as_of))
        prev_wk = iso(monday_of(as_of) - timedelta(days=7))
        ins("pm_standup_threads", [dict(agent="scribe", week_starting=prev_wk, channel_id="C0DEMO0001", master_ts="1786371471.100000", master_posted_at=ts(monday_of(as_of) - timedelta(days=7), 16),
                                        sweep_done_at=ts(monday_of(as_of) - timedelta(days=6), 7, 45), created_at=ts(monday_of(as_of) - timedelta(days=7), 16)),
                                   dict(agent="scribe", week_starting=wk, channel_id="C0DEMO0001", master_ts="1786976271.100000", master_posted_at=ts(monday_of(as_of), 16),
                                        sweep_done_at=None, created_at=ts(monday_of(as_of), 16))])
        resp = []
        for i, o in enumerate(owners + owners[:2]):
            week = prev_wk if i < 4 else wk
            resp.append(dict(agent="scribe", week_starting=week, owner=o, slack_user_id=f"U0DEMO000{(i % 4) + 1}",
                             last_week=f"Shipped the {proj_names[i % 10].lower()} checkpoint", this_week=f"Drive {proj_names[(i + 1) % 10].lower()} to review",
                             blockers=("Legal review" if i == 2 else None), linear_links_present=int(i % 2 == 0), responded_at=ts(days[-1], 18),
                             created_at=ts(days[-1], 18), raw_text=None, parsed_by="rule"))
        ins("pm_standup_responses", resp)
        comm = []
        for i in range(12):
            comm.append(dict(agent="scribe", week_starting=(prev_wk if i < 6 else wk), owner=owners[i % 4], commitment=f"Finish {proj_names[i % 10].lower()} milestone {i + 1}",
                             linear_link=(f"https://linear.app/{slug}/issue/MAR-{7001 + i}" if i % 3 else None), linear_ref_type=("issue" if i % 3 else None),
                             project_id=f"p{(i % 10) + 1}", issue_id=(f"i{i + 1}" if i % 3 else None), resolution=("by_ref" if i % 3 else "unresolved"),
                             scale="task", acknowledged_untracked=0, nudged_at=None, horizon="this_week", effective_due_date=iso(as_of + timedelta(days=4)),
                             completion_status=(["completed", "partial", "carried", "missed", "completed", "in_flight"][i % 6] if i < 6 else "pending"),
                             evaluated_at=(ts(days[-1], 7, 45) if i < 6 else None), created_at=ts(days[-1], 18), create_requested_at=None))
        ins("pm_commitments", comm)
        ins("pm_external_dependencies", [
            dict(agent="scribe", week_starting=wk, internal_owner=t("CONTENT_LEAD"), external_party=t("CONTRACTOR_FIRST"), description="blog draft",
                 owner_side_action="review on delivery", expected_delivery=iso(as_of + timedelta(days=3)), linear_link=None, status="pending", resolved_at=None,
                 created_at=ts(days[-1], 18), raw_text=f"{t('CONTRACTOR_FIRST')} / blog draft / {iso(as_of + timedelta(days=3))}", parsed_by="rule"),
            dict(agent="scribe", week_starting=wk, internal_owner=t("DESIGN_LEAD"), external_party="Print vendor", description="event banners",
                 owner_side_action="approve proof", expected_delivery=iso(as_of + timedelta(days=6)), linear_link=None, status="pending", resolved_at=None,
                 created_at=ts(days[-1], 18), raw_text=None, parsed_by="model"),
            dict(agent="scribe", week_starting=prev_wk, internal_owner=OPERATOR, external_party="CRM consultant", description="lifecycle workflow spec review",
                 owner_side_action="merge feedback", expected_delivery=iso(days[-3]), linear_link=None, status="delivered", resolved_at=ts(days[-3], 12),
                 created_at=ts(days[-8], 18), raw_text=None, parsed_by="rule"),
        ])
        ins("pm_missed_deadlines", [dict(agent="scribe", project_id="p5", original_due_date=iso(days[-4]), detected_at=ts(days[-3], 16), prompted_at=None,
                                         acknowledged_at=None, explanation=None, linear_comment_link=None, surfaced_in_thursday=0, created_at=ts(days[-3], 16)),
                                    dict(agent="scribe", project_id="p3", original_due_date=iso(days[-12]), detected_at=ts(days[-11], 16), prompted_at=ts(days[-11], 16),
                                         acknowledged_at=ts(days[-10], 9), explanation="Scoring inputs blocked on enrichment", linear_comment_link=None,
                                         surfaced_in_thursday=1, created_at=ts(days[-11], 16))])
        ins("pm_rca_log", [dict(agent="scribe", project_id="p3", rca_trigger="missed original due date by >7 days", rca_link=None,
                                process_changes="Enrichment coverage is now a weekly check before scoring work starts", owner_of_changes=OPERATOR,
                                created_at=ts(days[-9], 16))])

        # ---- content engine
        wk_mon = monday_of(as_of)
        ins("research_packets", [
            dict(agent="content-researcher", packet_type="call_mining", week_starting=iso(wk_mon), source_count=6, quiet_week=0,
                 summary="6 prospect calls mined; recurring theme: alert fatigue and unclear ownership during incidents.",
                 payload_path=f"state/pending/{iso(wk_mon)}/content-researcher-call-mining.md", created_at=ts(wk_mon, 16, 50)),
            dict(agent="content-researcher", packet_type="social_listening", week_starting=iso(wk_mon), source_count=14, quiet_week=0,
                 summary="14 community threads; on-call rotation fairness and paging cost dominate.", payload_path=None, created_at=ts(wk_mon, 16, 51)),
            dict(agent="content-researcher", packet_type="competitor_content", week_starting=iso(wk_mon), source_count=5, quiet_week=0,
                 summary=f"{t('COMPETITOR_A')} and {t('COMPETITOR_B')} both published SLA calculators this week.", payload_path=None, created_at=ts(wk_mon, 16, 52)),
        ])
        personas = ["aaron", "erin", "hannah"]
        themes = ["alert fatigue", "on-call fairness", "MTTR reporting", "postmortem culture", "tool sprawl"]
        vb = []
        for i in range(20):
            vb.append(dict(agent="content-researcher", entry_type=["quote", "question", "pain_point"][i % 3], source=["sales_call", "community", "social"][i % 3],
                           trust_tier=["first_party", "open_ugc", "attributed"][i % 3], persona=personas[i % 3], theme=themes[i % 5],
                           content=[f"We page everyone because nobody knows who owns the service.",
                                    f"How do other teams keep on-call fair without burning people out?",
                                    f"Our MTTR dashboard is hand-built and nobody trusts it."][i % 3] + f" (#{i + 1})",
                           source_ref=(f"meeting:mtg-{i + 1:03d}" if i % 3 == 0 else f"thread:{i + 1:04d}"), funnel_stage=["top", "mid", "bottom"][i % 3],
                           captured_at=ts(days[-1 - (i % 10)], 11), created_at=ts(wk_mon, 16, 53)))
        # topic-0002 ("A fair on-call rotation in five rules") needs publishable on-theme
        # evidence: the round-robin rows above hand it only a T3 community question and an
        # off-theme first-party quote, which (correctly) blocks brief-builder's substance
        # checks. One real quote keeps the demo queue movable without loosening the gate.
        vb.append(dict(agent="content-researcher", entry_type="quote", source="sales_call",
                       trust_tier="first_party", persona="erin", theme="on-call fairness",
                       content="We rebuilt the rotation three times this year; whoever shouts loudest gets the quiet weeks. (#21)",
                       source_ref="meeting:mtg-004", funnel_stage="mid",
                       captured_at=ts(days[-4], 11), created_at=ts(wk_mon, 16, 53)))
        ins("voice_bank", vb)
        mm = []
        for i in range(6):
            mm.append(dict(agent="content-researcher", meeting_id=f"mtg-{i + 1:03d}", title_redacted=f"Discovery call #{i + 1} (prospect)", meeting_date=iso(days[-2 - i]),
                           outcome=["mined", "mined", "mined_empty", "mined", "skipped_offtarget", "mined"][i],
                           skip_reason=("vendor inbound" if i == 4 else None), call_type=("vendor_inbound" if i == 4 else "prospect_sales"),
                           icp_persona=personas[i % 3], funnel_stage=["top", "mid", "bottom"][i % 3], host=t("AE"), company_size="50-200",
                           entries_written=[4, 3, 0, 5, 0, 3][i], packet_id=1, mined_at=ts(wk_mon, 16, 50)))
        ins("mined_meetings", mm)
        topics = []
        topic_titles = ["Why paging everyone is a design failure", "A fair on-call rotation in five rules", "MTTR you can defend to the board",
                        "Postmortems that change behavior", "Consolidating the incident toolchain", "The hidden cost of alert fatigue",
                        "Runbooks that engineers actually open", "SLA calculators: what the vendors leave out"]
        statuses = ["approved", "approved", "needs_edit", "submitted", "submitted", "candidate", "briefed", "rejected"]
        for i, title in enumerate(topic_titles):
            topics.append(dict(agent="content-researcher", topic_uid=f"topic-{i + 1:04d}", topic=title, target_persona=personas[i % 3], funnel_stage=["top", "mid", "bottom"][i % 3],
                               content_type=["blog", "blog", "guide", "blog", "webinar", "blog", "guide", "blog"][i], score_total=88 - i * 4, score_icp=20 - (i % 3),
                               score_search=18 - (i % 4), score_aeo=17, score_evidence=18 - (i % 2), score_education=15, evidence_summary=f"{2 + i % 3} voice-bank entries, {i % 2 + 1} calls",
                               evidence_sources=2 + i % 3, status=statuses[i], review_notes=("Sharpen the angle toward platform engineers" if statuses[i] == "needs_edit" else
                                                                                            "Too close to a vendor comparison" if statuses[i] == "rejected" else None),
                               approved_at=(ts(days[-1], 17, 15) if statuses[i] in ("approved", "briefed") else None),
                               notion_page_id=("00000000000000000000000000000501" if i < 5 else None), notion_synced_at=(ts(days[-1], 17, 18) if i < 5 else None),
                               created_at=ts(wk_mon, 16, 54)))
        ins("topic_backlog", topics)
        ins("topic_evidence", [dict(topic_id=(i % 8) + 1, voice_bank_id=i + 1, created_at=ts(wk_mon, 16, 55)) for i in range(16)]
            + [dict(topic_id=2, voice_bank_id=21, created_at=ts(wk_mon, 16, 55))])
        ci = []
        for i in range(15):
            ci.append(dict(url=f"https://{t('COMPANY_DOMAIN')}/blog/post-{i + 1}", slug=f"post-{i + 1}", title=f"Published post {i + 1}: {themes[i % 5]}",
                           excerpt="An existing article in the content inventory.", headings=json.dumps(["Intro", "The problem", "What to do"]),
                           primary_topic=themes[i % 5], persona=personas[i % 3], top_queries=json.dumps([themes[i % 5]]), query_source="gsc",
                           published_at=iso(as_of - timedelta(days=30 + i * 9)), last_modified=None, source="crawl", status="live",
                           last_seen_at=ts(days[-1], 10), created_at=ts(days[-20], 10)))
        ins("content_inventory", ci)
        ins("content_briefs", [
            dict(agent="content-producer", topic_id=7, working_title="Runbooks that engineers actually open", target_persona="aaron", tone_code="blog A",
                 primary_keyword="incident runbook template", secondary_keywords=json.dumps(["runbook best practices", "on-call runbook"]),
                 aeo_questions=json.dumps(["What should an incident runbook include?"]), word_count_target=1400, brief_path="state/working/briefs/brief-0001.md",
                 status="ready", created_at=ts(days[-1], 18)),
            dict(agent="content-producer", topic_id=1, working_title="Why paging everyone is a design failure", target_persona="erin", tone_code="blog A",
                 primary_keyword="alert fatigue", secondary_keywords=json.dumps(["paging policy", "alert routing"]),
                 aeo_questions=json.dumps(["How do you reduce alert fatigue?"]), word_count_target=1200, brief_path=None, status="draft", created_at=ts(days[-1], 18, 5)),
        ])
        ins("content_drafts", [dict(agent="content-producer", brief_id=1, version=1, stage="drafting", loop_count=0, revision_cycle=0, rubric_brand=None, rubric_education=None,
                                    rubric_evidence=None, rubric_human=None, rubric_factual=None, rubric_seo=None, packet_path=None, gate_decision=None, gate_feedback=None,
                                    published_url=None, created_at=ts(days[-1], 18, 10), updated_at=None)])
        ins("derivative_assets", [dict(agent="content-producer", draft_id=1, channel="linkedin", asset_path=None, status="draft", posted_by=None, posted_at=None, created_at=ts(days[-1], 18, 11))])
        con.commit()
        tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()]
        counts = {tb: cur.execute(f"SELECT COUNT(*) FROM {tb}").fetchone()[0] for tb in tables}
        con.close()
        return counts

    def spend_vs_trailing(self, camp: str, day) -> tuple[float, float, float]:
        """(day spend, trailing-7 mean of the prior seeded days, deviation %) for one campaign."""
        from collections import defaultdict
        by_day = defaultdict(float)
        for r in self.pc:
            if r["campaign_name"] == camp:
                by_day[r["snapshot_date"]] += r["spend"]
        day_s = iso(day)
        today_v = by_day.get(day_s, 0.0)
        prior = [v for d_, v in sorted(by_day.items()) if d_ < day_s][-7:]
        base = sum(prior) / len(prior) if prior else today_v
        dev = (today_v - base) / base * 100 if base else 0.0
        return today_v, base, dev

    def spend_check_line(self, day) -> str:
        """The tick day's spend per campaign against the trailing-7-day mean, from the rows the seeder wrote."""
        parts = []
        for camp, _ in self.campaigns:
            today_v, base, dev = self.spend_vs_trailing(camp, day)
            sev = "**MED**" if abs(dev) > 25 else ("LOW" if abs(dev) > 10 else "CLEAR")
            parts.append(f"{camp} ${today_v:,.0f} ({dev:+.0f}%) {sev}")
        return " · ".join(parts) + "."

    def write_schema(self):
        con = sqlite3.connect(self.db_path)
        rows = con.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' ORDER BY type DESC, name").fetchall()
        con.close()
        header = ("-- state/working/schema.sql — GENERATED by scripts/seed_demo_state.py from\n"
                  "-- state/working/migrations/*.sql. Do not hand-edit; add a migration instead.\n"
                  f"-- Migrations applied: {', '.join(p.stem for p in sorted(fleet_paths.MIGRATIONS_DIR.glob('*.sql')))}\n\n")
        (self.root / "state" / "working" / "schema.sql").write_text(header + ";\n\n".join(r[0] for r in rows) + ";\n")

    # ------------------------------------------------------------------ journals
    def write_journals(self):
        jd = self.journal_dir
        jd.mkdir(parents=True, exist_ok=True)
        for f in jd.glob("*.md"):
            f.unlink()
        t, d3 = self.t, self.recent
        snaps = self.snaps[-3:]
        hdr = lambda title: f"# {title}\n\nAppend-only journal. One `## <ISO-8601Z> | <label>` entry per Tick; the harness reads the last header as its \"since\" marker.\n\n"

        # revops-watchdog
        out = [hdr("revops-watchdog — Journal")]
        for j, (d, s) in enumerate(zip(d3, snaps)):
            h = [x for x in self.handoffs if x["from_agent"] == "revops-watchdog" and x["created_at"].startswith(iso(d))]
            out.append(f"""## {ts(d, 13, 44)} | Daily Tick

### Anchor
{d.strftime('%A %Y-%m-%d')} · Q{(d.month - 1) // 3 + 1} {d.year} · day {d.day} of the month.

### MCP Preflight
~~crm (HubSpot) → bound · ~~knowledge base (Notion) → bound · ~~issue tracker (Linear) → bound · ~~chat (Slack) → bound

### Funnel Snapshot
| Metric | Value | 4-wk baseline | Δ | Severity |
|---|---|---|---|---|
| MQL (MTD) | {s['mqls']} | — | — | — |
| SAL | {s['sals']} | — | — | — |
| SQL | {s['sqls']} | — | — | — |
| MQL→SAL CVR | {s['mql_to_sal_rate']}% | 61.5 | — | CLEAR (>55%) |
| SAL→SQL CVR | {s['sal_to_sql_rate']}% | 34.9 | {round((s['sal_to_sql_rate'] - 34.9) / 34.9 * 100, 1)}% | **MED** |
| Pipeline | ${s['pipeline_value']:,.0f} | — | — | CLEAR |

**SAL→SQL note:** {s['sal_to_sql_rate']}% ({s['sqls']}/{s['sals']}) breaches the <35% absolute threshold — {['first', 'second', 'third'][j]} consecutive MED day.

**DB:** `funnel_snapshots` row for {iso(d)} written and re-read.

### Workflow Health
8 workflows checked. {'Flagged: Event registration sync — first-step exit rate 100% (HIGH).' if j == 2 else 'None flagged.'}

### Scoring Drift
median {42 + (7 + j) * 1.3:.1f} (Δ +{round((7 + j) * 1.3, 1)} pts/10d) · top decile ~10.5% — {'drift flag set' if j >= 1 else 'within band'}.

### {t('ENRICHMENT_VENDOR')} Coverage
new contacts 7d: {self.rng.randint(40, 80)} · both ids populated: 100.0% — CLEAR.

### Anomalies Written
- [MED] funnel / sal_to_sql_cvr: SAL→SQL CVR {s['sal_to_sql_rate']}% below the 35% threshold
{'- [HIGH] workflow / first_step_exit_rate: Event registration sync exits every enrollment at step 1' if j == 2 else ''}

### Handoffs Written
""" + "\n".join(f"- **id={x['id']}** | {x['severity']} | \"{x['subject']}\" → chief-of-staff ({x['status']})" for x in h) + "\n")
        (jd / "revops-watchdog.md").write_text("\n".join(out))

        # chief-of-staff (PM + AM for the last two ticks)
        out = [hdr("chief-of-staff — Journal")]
        for j, d in enumerate(d3[-2:]):
            s = snaps[-2 + j]
            out.append(f"""## {ts(d, 1, 12)} | PM Tick complete
- Date: {iso(d)} ({d.strftime('%A')}) | Quarter: Q{(d.month - 1) // 3 + 1} {d.year}
- Handoffs read since AM: revops-watchdog LOW tick-complete; performance-marketer traffic scorecard ({'acknowledged' if j == 0 else 'still open'}).
- Cross-agent audit: content-producer journal stale (>48h) — covered by the standing M4 grace note; no new incident filed.
- Carry-forward written: SAL→SQL watch decision stays open for the AM brief.
- Meditation written to `state/journal/chief-of-staff-meditations.md`.

## {ts(d, 14, 20)} | AM Tick complete
- Date: {iso(d)} ({d.strftime('%A')}) | Quarter: Q{(d.month - 1) // 3 + 1} {d.year} | day {d.day} of the month
- Connector state: ~~calendar bound (3 events); ~~email bound (30 unread scanned, 1 action item); ~~issue tracker bound (18 open); ~~chat bound.
- Migrations: none pending.
- Cross-agent audit: content-producer stale {9 * 24 + j * 24}h (known, M4 grace); every other journal fresh; {1 if j else 2} handoff(s) pending >72h → nudged in brief.
- Handoffs read since last Tick: revops-watchdog MED — SAL→SQL CVR {s['sal_to_sql_rate']}% (day {j + 2} of the watch), revops-watchdog LOW tick-complete.
- Priorities: (1) SAL→SQL watch — {'decide keep-watching vs escalate' if j == 0 else 'Scott ruled: keep watching'}; (2) GTM scorecard Tier 2 gate for the WBR; (3) topic backlog rulings due from {t('HEAD_OF_MARKETING_FIRST')}.
- Decisions needed: {1 if j == 0 else 0}.
- Brief delivered: ~~chat DM to Scott (demo outbox in DEMO_MODE).
- Voice Standard applied: plain PT calendar framing, no em-dashes in brief prose, Linear links clickable.
""")
        (jd / "chief-of-staff.md").write_text("\n".join(out))
        out = [hdr("chief-of-staff — Evening Meditations")]
        for j, d in enumerate(d3[-2:]):
            out.append(f"""## {ts(d, 1, 15)} | Evening Meditation

Three ticks of the same funnel signal and the question is no longer whether the number is real but what the fleet owes the humans when a watch item stops being news. revops-watchdog did its job by counting; chief-of-staff's job is to keep the count from becoming noise. {'Tomorrow the brief leads with the decision, not the metric.' if j == 0 else 'Scott chose patience; the brief will say so once and then stop repeating it.'}

*— chief-of-staff*
""")
        (jd / "chief-of-staff-meditations.md").write_text("\n".join(out))

        # performance-marketer (daily + the Wednesday scorecard pass)
        out = [hdr("performance-marketer — Journal")]
        for j, d in enumerate(self.days[-2:]):
            label = "Daily Tick (Wed) + Scorecard Pass" if j == 0 else f"Daily Tick ({d.strftime('%a')})"
            out.append(f"""## {ts(d, 15, 30)} | {label}

### Environment
PERFORMANCE_MARKETER_EXECUTE=off (shadow) · DEMO_MODE · ~~ads (Google Ads) data via fixtures/CSV · ~~web analytics (GSC) via CSV.

### Data Pulls
spend-14d.csv → `paid_creative` 84 rows · gsc-7d.csv → `keyword_rankings` 20 keywords (4 weekly snapshots on file).

### Spend Check — {iso(d)} vs 7d avg
{self.spend_check_line(d)}

### Keyword Snapshot
20 tracked · 3 WATCH flags (≥3 positions lost WoW) · best mover: "{t('company_slug')} terraform provider" 4 → 1.

{'### Weekly Analysis — Scorecard Pass (Wednesday)' + chr(10) + 'Traffic block written to `gtm_scorecard` (8 metrics × 8 months, definition v1.5). Funnel block expected from revops-watchdog. Position pass produced 4 proposals: 2 auto_3a (greenlit, shadow), 1 human_3b (change list), 1 creative (awaiting copy review, MAR-7076).' if j == 0 else '### Rollback Watch' + chr(10) + 'Shadow bid change on "incident management platform" — CVR holding (6.0% vs 6.1%), no reversal trigger.'}

### Handoffs Written
{'- performance-marketer → chief-of-staff | MED | Weekly GTM Scorecard (traffic) — Tier 2 greenlight ask' + chr(10) + '- performance-marketer → Scribe | LOW | Weekly GTM Scorecard traffic block ready' if j == 0 else '- none (watch only)'}

### State
`spend_alerts` +1 · `paid_change_proposals` {'+4' if j == 0 else 'unchanged'} · `applied_changes` {'+1 (shadow)' if j == 0 else 'unchanged'}.
""")
        (jd / "performance-marketer.md").write_text("\n".join(out))

        # Scribe
        out = [hdr("Scribe — Journal")]
        for j, d in enumerate([self.days[-6], self.days[-1]]):
            out.append(f"""## {ts(d, 17, 5)} | Weekly Tick — WBR posted

### Anchor
{d.strftime('%A %Y-%m-%d')} · WBR covering the week of {iso(monday_of(d))}.

### WBR
Draft posted to ~~knowledge base (Notion "Updates" database: `{t('NOTION_UPDATES_DB_ID')}`). Summary block auto-populated from revops-watchdog `funnel_snapshots`; traffic block from performance-marketer `gtm_scorecard` (v1.5).
Section owners pinged in #team-marketing: Summary — {OPERATOR}; Project Updates — {t('HEAD_OF_MARKETING')}; Content — {t('CONTENT_LEAD')}; Web & Design — {t('DESIGN_LEAD')}; GTM Ops — {OPERATOR}. Deadline Thursday 07:00 PT.

### Notion topic sync
{'2 approved, 1 needs_edit harvested from the review database and applied via scripts/topic_review.py; 5 rows mirrored.' if j == 1 else '3 candidates mirrored to the review database; no rulings yet.'}

### Handoffs Written
- Scribe → chief-of-staff | LOW | WBR posted for {iso(d)}
{'- Scribe → content-researcher | MED | Topic backlog mirrored to Notion — 2 approved, 1 needs_edit' if j == 1 else ''}
""")
        (jd / "scribe.md").write_text("\n".join(out))
        out = [hdr("Scribe — Project Management Journal")]
        out.append(f"""## {ts(self.days[-1], 16, 35)} | Pulse — 10 projects, 40 issues (8 stale), 1 blocker opened / 0 resolved, 1 missed deadline

- Scope window 90d · brake not tripped (40 issues / 10 projects, ceilings 400 / 60).
- Health: 7 on_track · 2 at_risk ({t('DESIGN_LEAD')}: Brand refresh; {t('CONTENT_LEAD')}: SEO content sprint) · 1 off_track (Lead scoring model 2.0 — RCA logged).
- Orphans: 8 issues with no activity in >10 days, owner hints sent to `default_external_owner` ({t('HEAD_OF_MARKETING')}).
- Missed deadline detected: Brand refresh (original {iso(self.days[-4])}) — not yet prompted (accountability_mode=state_only).

## {ts(monday_of(self.as_of) + timedelta(days=1), 7, 45)} | Monday stand-up sweep (EOD capture) — week of {iso(monday_of(self.as_of))}

- Master thread posted {ts(monday_of(self.as_of), 16)} in C0DEMO0001 · 6 responses captured (4 rule-parsed, 2 model-parsed).
- Commitments captured: 6 this week; prior week evaluated: 2 completed, 1 partial, 1 carried, 1 missed, 1 in_flight.
- External dependencies: {t('CONTRACTOR_FIRST')} / blog draft / {iso(self.as_of + timedelta(days=3))}; Print vendor / event banners.
""")
        (jd / "scribe_project_management.md").write_text("\n".join(out))

        # content-researcher
        out = [hdr("content-researcher — Journal")]
        for j, d in enumerate([monday_of(self.as_of) - timedelta(days=7), monday_of(self.as_of)]):
            out.append(f"""## {ts(d, 16, 55)} | Weekly Tick

### Anchor
{d.strftime('%A %Y-%m-%d')} · week of {iso(d)}.

### MCP Preflight
~~meeting notes (Grain) → bound · WebSearch → available · ~~issue tracker (Linear) → bound (optional).

### Migration
none pending.

### Handoffs Processed
{'Scribe → content-researcher: rulings pre-applied (2 approved, 1 needs_edit) — read, not re-applied.' if j == 1 else 'none addressed to content-researcher.'}

### Research Sweep
call_mining: 6 calls hosted by {t('AE')} or {t('CEO')}, 4 mined, 1 empty, 1 skipped (vendor inbound) · social_listening: 14 threads · competitor_content: 5 pages ({t('COMPETITOR_A')}, {t('COMPETITOR_B')}).
Voice bank +{20 if j == 1 else 12} entries (trust tiers: first_party / attributed / open_ugc). Dedup against `content_inventory` (15 live posts): 1 refresh candidate.

### Backlog Delta
{'8 topics in backlog: 2 approved → content-producer queue, 1 briefed, 1 needs_edit (angle toward platform engineers), 2 submitted, 1 candidate, 1 rejected.' if j == 1 else '5 topics in backlog: 3 submitted for review, 2 candidates.'}

### Handoffs Written
- content-researcher → chief-of-staff | LOW | Weekly Tick — 3 topics submitted for review
""")
        (jd / "content-researcher.md").write_text("\n".join(out))

        # content-producer — deliberately stale (last entry ~9 weekdays ago) so the cross-agent audit has a finding
        d = self.days[-9]
        (jd / "content-producer.md").write_text(hdr("content-producer — Journal") + f"""## {ts(d, 18, 0)} | Skill: brief-builder

### MCP Preflight
~~issue tracker (Linear) → bound (optional) · ~~knowledge base (Notion) → not required.

### Queue
1 approved topic picked up: "Runbooks that engineers actually open" (topic-0007, persona aaron).

### Brief
Written to `state/working/briefs/brief-0001.md` · `content_briefs` id=1 status=ready · evidence: 3 voice-bank entries, 1 call · primary keyword "incident runbook template".

### Handoffs Written
- content-producer → chief-of-staff | LOW | Brief ready for calibration review ({t('HEAD_OF_MARKETING_FIRST')} gate, {t('CONTENT_LEAD_FIRST')} backup)
""")

        # brand-designer
        d = self.days[-12]
        (jd / "brand-designer.md").write_text(hdr("brand-designer — Journal") + f"""## {ts(d, 18, 20)} | Skill: dither-pack

### MCP Preflight
~~issue tracker (Linear) → bound (optional) · ~~design (Figma) → not bound (expected at M1).

### Request
Webinar hero set for "{t('COMPANY')} on-call fairness" (requested by {t('CONTENT_LEAD_FIRST')} via #team-marketing).

### Settings & Outputs
engine: dither-pack, brand palette #0F766E / #F2A900, Inter · 5 channel outputs (social, IAB display, web hero, email, OG) · manifest + alt-text · compliance: pass.

### Review State
packet pending with {t('DESIGN_LEAD_FIRST')} · revision 0/3.
""")

        # handoffs.md — same ids/timestamps as the DB
        body = [hdr("Handoffs — fleet message bus (append-only)")]
        body += [entry for _, entry in sorted(self.handoff_log, key=lambda x: x[0])]
        (jd / "handoffs.md").write_text("\n".join(body))

        # ops-incidents
        (jd / "ops-incidents.md").write_text(hdr("Ops Incidents") + f"""## {ts(self.days[-9], 14, 16)} | MED | chief-of-staff | content-producer journal stale >48h — M4 grace

content-producer's last entry is the brief-builder run on {iso(self.days[-9])}; creation-pod is not built yet, so the daily queue check has nothing to write. Standing grace until M4 lands; re-evaluate weekly.

## {ts(self.recent[-1], 13, 50)} | HIGH | revops-watchdog | Event registration sync exits every enrollment at step 1

`workflow_health` shows first_step_exit_rate 1.0 on workflow 900001007 (24h). Handoff written to chief-of-staff; needs a human to inspect the enrollment trigger in ~~crm.
""")

        # pending packet + brief
        pend = self.root / "state" / "pending" / iso(monday_of(self.as_of))
        pend.mkdir(parents=True, exist_ok=True)
        (pend / "content-researcher-topic-backlog.md").write_text(f"""# content-researcher — topic backlog submission — week of {iso(monday_of(self.as_of))}

Tier 2 review packet. Rulings are made in the ~~knowledge base review database; Scribe harvests them every tick.

| # | Topic | Persona | Stage | Score | Evidence |
|---|---|---|---|---|---|
| 1 | Why paging everyone is a design failure | aaron | top | 88 | 3 voice-bank entries, 2 calls |
| 2 | A fair on-call rotation in five rules | erin | mid | 84 | 2 entries, 1 call |
| 3 | MTTR you can defend to the board | hannah | bottom | 80 | 4 entries, 1 call |
""")
        briefs = self.root / "state" / "working" / "briefs"
        briefs.mkdir(parents=True, exist_ok=True)
        (briefs / "brief-0001.md").write_text(f"""# Content brief — Runbooks that engineers actually open

- **Topic:** topic-0007 · **Persona:** Aaron (platform engineer) · **Stage:** bottom · **Type:** guide
- **Primary keyword:** incident runbook template · **Secondary:** runbook best practices, on-call runbook
- **AEO question:** What should an incident runbook include?
- **Target length:** 1,400 words · **Tone:** clear, authoritative, approachable

## Evidence
- "We page everyone because nobody knows who owns the service." — prospect call
  (first_party · `meeting:mtg-001` · voice-bank #1) — quotable
- On-call engineers skip runbooks that are longer than the incident. — community thread
  (open_ugc · `thread:0002` · voice-bank #2) — direction only, never quote T3 verbatims

## Outline
1. Why most runbooks go unread
2. The five sections an engineer will actually use
3. A template ({t('COMPANY')} link in the CTA)
""")

    def reset_demo_outbox(self):
        """Empty state/demo-outbox/ and (re)write its README.

        DEMO_MODE writes land here instead of Slack and Notion, so a fresh seed has to
        clear the previous run's messages — otherwise a demo opens on yesterday's brief.
        `.gitkeep` survives (the folder is tracked, its contents are not).
        """
        out = self.root / "state" / "demo-outbox"
        out.mkdir(parents=True, exist_ok=True)
        for p in sorted(out.rglob("*"), key=lambda q: len(q.parts), reverse=True):
            if p.name == ".gitkeep":
                continue
            p.unlink() if p.is_file() else p.rmdir()
        (out / ".gitkeep").touch()
        (out / "README.md").write_text(
            "# Demo outbox\n\n"
            "Where the fleet's outbound writes land when `DEMO_MODE=1`. The fixture MCP servers "
            "(`scripts/demo/fixture_mcp.py`) append Slack messages to `slack.md` and save Notion "
            "pages under `notion/`, so a demo can show the rendered surface an agent produced "
            "without a single credential and without touching a live workspace. Everything here is "
            "generated: `scripts/seed_demo_state.py` empties the folder on every seed, and git "
            "ignores its contents.\n"
        )

    def write_cadence(self):
        path = self.root / "state" / "identity" / "scribe-pm-cadence.yaml"
        if not path.exists():
            return
        text = path.read_text()
        head = text.split("members:")[0]
        t = self.t
        members = [(OPERATOR, "U0DEMO0001", OPERATOR, "America/Los_Angeles", "08:00"),
                   (t("HEAD_OF_MARKETING"), "U0DEMO0002", t("HEAD_OF_MARKETING"), "America/Los_Angeles", "08:00"),
                   (t("CONTENT_LEAD"), "U0DEMO0003", t("CONTENT_LEAD"), "America/Chicago", "10:00"),
                   (t("DESIGN_LEAD"), "U0DEMO0004", t("DESIGN_LEAD_FIRST_LOWER"), "Europe/Madrid", "09:00")]
        head = "\n".join(
            (f"default_external_owner: {t('HEAD_OF_MARKETING')}" if line.startswith("default_external_owner:") else line)
            for line in head.split("\n"))
        block = "members:\n" + "".join(
            f"  - name: {n}\n    slack_user_id: \"{sid}\"\n    slack_alias: \"{alias}\"\n    timezone: {tz}\n    standup_tag_local: \"{tag}\"\n"
            for n, sid, alias, tz, tag in members)
        path.write_text(head + block)


def parse_as_of(value: str) -> date:
    """--as-of accepts an ISO date, or the literals 'today' / 'yesterday'.

    `make demo-reset` seeds as of yesterday so the demo day itself is unwritten — the
    agents have a story behind them and today still to do.
    """
    v = value.strip().lower()
    if v == "today":
        return date.today()
    if v == "yesterday":
        return date.today() - timedelta(days=1)
    return date.fromisoformat(value)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--profile", default=fleet_paths.profile() if fleet_paths.profile() != "base" else "orrery")
    ap.add_argument("--as-of", default="today", help="YYYY-MM-DD, 'today', or 'yesterday'")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--root", help="FLEET_ROOT override")
    args = ap.parse_args()
    if args.root:
        os.environ["FLEET_ROOT"] = args.root
    root = fleet_paths.fleet_root(strict=True)
    as_of = parse_as_of(args.as_of)
    s = Seeder(root, args.profile, as_of, args.seed)
    s.rebuild_db(args.force)
    counts = s.seed_db()
    s.write_schema()
    s.write_journals()
    s.write_cadence()
    s.reset_demo_outbox()
    print(f"[seed] profile={args.profile} as_of={as_of} seed={args.seed} root={root}")
    for k, v in counts.items():
        print(f"  {v:5d}  {k}")
    print("[seed] journals:", ", ".join(sorted(p.name for p in s.journal_dir.glob('*.md'))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
