-- 011_content_inventory.sql
-- Published-content inventory for dedup (Step 4 of the content workflow; see
-- roster/content-researcher/skills/content-inventory.md).
-- Single source of truth for what GTM Fleet has shipped, so content-researcher:topic-synthesizer
-- can classify a candidate topic as net-new / refresh / duplicate instead of the
-- former stub. Seeded by scripts/blog_inventory_crawl.py (orrery.example/blog), appended
-- by content-producer's publish-package on publish, and enriched with search-query data from a
-- degradation ladder (GSC API -> GSC CSV export -> Ahrefs proxy -> none). The
-- `framer` source is a scaffolded seam for a future Framer MCP/API connector.
-- Shared table: content-researcher reads (dedup), content-producer writes (on publish).

-- ============================================================
-- CONTENT ENGINE — PUBLISHED CONTENT INVENTORY (migration 011)
-- ============================================================

CREATE TABLE IF NOT EXISTS content_inventory (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    url           TEXT    NOT NULL UNIQUE,          -- canonical published URL (idempotency key)
    slug          TEXT,
    title         TEXT,
    excerpt       TEXT,                             -- meta description / excerpt
    headings      TEXT,                             -- JSON array of H2/H3s (topic surface for matching)
    primary_topic TEXT,                             -- inferred topic label; reuse voice_bank theme vocab where possible
    persona       TEXT    CHECK (persona IN ('aaron','erin','hannah','unknown') OR persona IS NULL),
    top_queries   TEXT,                             -- JSON array of queries this URL ranks for
    query_source  TEXT    CHECK (query_source IN ('gsc','gsc_csv','ahrefs','none') OR query_source IS NULL),
    published_at  TEXT,                             -- ISO 8601
    last_modified TEXT,                             -- ISO 8601
    source        TEXT    NOT NULL                  -- how this row was populated
                          CHECK (source IN ('crawl','framer','gsc','gsc_csv','ahrefs','content-producer')),
    status        TEXT    NOT NULL DEFAULT 'live'
                          CHECK (status IN ('live','stale','removed')),
    last_seen_at  TEXT,                             -- ISO 8601; refreshed each crawl (detect removed posts)
    created_at    TEXT    NOT NULL                  -- ISO 8601
);

-- Self-register so Librarian step 5 does not re-detect this migration as
-- pending (matches 001/003/005/007/008/009/010; tick.py also INSERT OR IGNOREs after apply).
CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('011_content_inventory', datetime('now'));
