-- 019_voice_bank_trust_tier.sql
-- Adds a provenance trust tier to every voice_bank entry, so that how much a
-- signal is allowed to influence downstream work is a property of *where it came
-- from*, enforced in code, rather than a judgement call made per run.
--
-- Motivation. content-researcher's research skills are about to gain egress to LinkedIn,
-- Reddit, Hacker News, Product Hunt and competitor blogs (see
-- docs/agent-content-trust-policy.md). Those are surfaces where anyone can author
-- text. That text flows voice_bank -> topic_evidence -> content-producer:brief-builder ->
-- published content, so absent a control, a stranger's forum post can become a
-- quote GTM Fleet publishes as market evidence. The tier makes that path refusable.
--
-- Tiers (fleet vocabulary; see the policy doc for the full definitions):
--   first_party  Authenticated, internally recorded, and attributable to a real
--                conversation we were part of. Grain sales calls, HubSpot records.
--   attributed   Published by an identifiable organisation under its own name and
--                accountable for it. Competitor blogs, trade publications.
--   open_ugc     Anyone can author it. Forum posts, issue bodies, social posts,
--                comments, search terms. Treated as quarantine-grade evidence.
--
-- Enforcement this migration enables (applied in topic-synthesizer): a topic may
-- not clear the Tier 2 submission floor on open_ugc alone, regardless of how many
-- distinct sources it has. Eight forum posts can be eight sock puppets; two
-- independent sales calls cannot. Corroboration must include at least one
-- first_party or attributed source.
--
-- NOT NULL with no DEFAULT is deliberate — fail closed. An INSERT that forgets to
-- declare provenance errors loudly instead of silently defaulting to a tier its
-- author did not think about. This intentionally breaks any writer not updated in
-- the same change; call-miner, social-listening and competitor-content-scan are
-- updated alongside it.
--
-- Backfill is by observed source, verified row by row before writing (2026-08-04):
--   209 sales_call rows          -> first_party (Grain, all of them)
--     2 community rows           -> attributed  (competitor-a.example and competitor-b.example posts)
--     5 social rows              -> open_ugc    (GitHub issue bodies, all of them)
-- Note that `source='social'` is NOT uniformly open_ugc going forward — the
-- publications cluster (HR Brew, People Managing People, Lattice) is attributed.
-- The mapping below is correct for the rows that exist today, not a general rule;
-- the skills assign the tier per source cluster from here on.
--
-- Owned by content-researcher (voice_bank is content-researcher's table).
-- Run: applied by scripts/tick.py::run_pending_migrations (Librarian step), or
--   manually: sqlite3 state/working/fleet.db < state/working/migrations/019_voice_bank_trust_tier.sql

-- Mirrors the existing table exactly (migration 007), adding only trust_tier.
-- The entry_type / source / persona / funnel_stage CHECKs are reproduced verbatim
-- from the live schema — do not "tidy" them here, a silent widening or narrowing
-- of an unrelated constraint is exactly the drift 016 had to clean up.
CREATE TABLE voice_bank_new (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent       TEXT    NOT NULL DEFAULT 'content-researcher',
    entry_type  TEXT    NOT NULL CHECK (entry_type IN ('quote','question','pain_point')),
    source      TEXT    NOT NULL CHECK (source IN ('social','sales_call','community')),
    trust_tier  TEXT    NOT NULL CHECK (trust_tier IN ('first_party','attributed','open_ugc')),
    persona     TEXT    CHECK (persona IN ('aaron','erin','hannah','unknown')),
    theme       TEXT,                              -- cluster label
    content     TEXT    NOT NULL,                  -- verbatim text (anonymized for calls)
    source_ref  TEXT,                              -- URL or Grain call reference
    funnel_stage TEXT   CHECK (funnel_stage IN ('top','mid','bottom') OR funnel_stage IS NULL),
    captured_at TEXT,                              -- when the source said it (if known)
    created_at  TEXT    NOT NULL                   -- ISO 8601
);

INSERT INTO voice_bank_new (
    id, agent, entry_type, source, trust_tier, persona, theme, content,
    source_ref, funnel_stage, captured_at, created_at
)
SELECT
    id, agent, entry_type, source,
    CASE source
        WHEN 'sales_call' THEN 'first_party'
        WHEN 'community'  THEN 'attributed'
        WHEN 'social'     THEN 'open_ugc'
        ELSE 'open_ugc'                     -- fail closed on anything unforeseen
    END,
    persona, theme, content, source_ref, funnel_stage, captured_at, created_at
FROM voice_bank;

DROP TABLE voice_bank;

ALTER TABLE voice_bank_new RENAME TO voice_bank;

CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('019_voice_bank_trust_tier', datetime('now'));
