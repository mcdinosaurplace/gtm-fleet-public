-- Migration: 015_textual_ids
-- Created: 2026-07-14
-- Description: Move the id column of the three agent-minted tables (handoffs,
--   anomalies, spend_alerts) from INTEGER PRIMARY KEY AUTOINCREMENT to TEXT
--   PRIMARY KEY. Sequential integer ids assigned as MAX(id)+1 by uncoordinated
--   concurrent writers (multiple agents, and the same agent on divergent
--   branches during a scheduled-tick divergence) collide on merge and have to be
--   renumbered by hand (e.g. performance-marketer and chief-of-staff both minting id=193 on 2026-07-14;
--   id=184 before that). Going forward ids are minted via scripts/ids.py as
--   `{agent}_{kind}_{time}_{rand}` (e.g. revops-watchdog_handoff_01j9x8k2p7_a3f2z9), which
--   is unique without coordination and never needs shuffling.
--   No foreign keys reference these ids (verified); all cross-references live in
--   free text (journals, decision bodies, briefs), so existing references stay
--   valid. Existing integer ids are preserved verbatim as their text form
--   ('177', '191', ...) via CAST — new-style ids only apply to rows minted from
--   here on. Owner: chief-of-staff (fleet-wide; Scott directive 2026-07-14).
-- Run: applied by scripts/tick.py::run_pending_migrations (Librarian step), or
--   manually: sqlite3 state/working/fleet.db < state/working/migrations/015_textual_ids.sql

-- handoffs
CREATE TABLE handoffs_new (
    id              TEXT    PRIMARY KEY,
    from_agent      TEXT    NOT NULL,
    to_agent        TEXT    NOT NULL,
    subject         TEXT    NOT NULL,
    body            TEXT,
    severity        TEXT    CHECK (severity IN ('LOW', 'MED', 'HIGH')),
    status          TEXT    NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'acknowledged', 'resolved')),
    created_at      TEXT    NOT NULL,
    acknowledged_at TEXT,
    resolved_at     TEXT
);
INSERT INTO handoffs_new (id, from_agent, to_agent, subject, body, severity, status, created_at, acknowledged_at, resolved_at)
SELECT CAST(id AS TEXT), from_agent, to_agent, subject, body, severity, status, created_at, acknowledged_at, resolved_at FROM handoffs;
DROP TABLE handoffs;
ALTER TABLE handoffs_new RENAME TO handoffs;

-- anomalies
CREATE TABLE anomalies_new (
    id          TEXT    PRIMARY KEY,
    agent       TEXT    NOT NULL,
    detected_at TEXT    NOT NULL,
    surface     TEXT    NOT NULL,
    metric      TEXT    NOT NULL,
    value       REAL,
    baseline    REAL,
    deviation_pct REAL,
    severity    TEXT    NOT NULL CHECK (severity IN ('LOW', 'MED', 'HIGH')),
    description TEXT,
    status      TEXT    NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'resolved')),
    resolved_at TEXT,
    created_at  TEXT    NOT NULL
);
INSERT INTO anomalies_new (id, agent, detected_at, surface, metric, value, baseline, deviation_pct, severity, description, status, resolved_at, created_at)
SELECT CAST(id AS TEXT), agent, detected_at, surface, metric, value, baseline, deviation_pct, severity, description, status, resolved_at, created_at FROM anomalies;
DROP TABLE anomalies;
ALTER TABLE anomalies_new RENAME TO anomalies;

-- spend_alerts
CREATE TABLE spend_alerts_new (
    id              TEXT    PRIMARY KEY,
    agent           TEXT    NOT NULL DEFAULT 'performance-marketer',
    detected_at     TEXT    NOT NULL,
    platform        TEXT    NOT NULL,
    campaign_name   TEXT,
    metric          TEXT    NOT NULL,
    value           REAL,
    baseline        REAL,
    deviation_pct   REAL,
    severity        TEXT    NOT NULL CHECK (severity IN ('LOW', 'MED', 'HIGH')),
    description     TEXT,
    status          TEXT    NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'acknowledged', 'resolved')),
    resolved_at     TEXT,
    created_at      TEXT    NOT NULL
);
INSERT INTO spend_alerts_new (id, agent, detected_at, platform, campaign_name, metric, value, baseline, deviation_pct, severity, description, status, resolved_at, created_at)
SELECT CAST(id AS TEXT), agent, detected_at, platform, campaign_name, metric, value, baseline, deviation_pct, severity, description, status, resolved_at, created_at FROM spend_alerts;
DROP TABLE spend_alerts;
ALTER TABLE spend_alerts_new RENAME TO spend_alerts;

INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('015_textual_ids', datetime('now'));
