-- 007_content_engine_tables.sql
-- Content engine scaffold (M1): content-researcher (research/intelligence) and content-producer
-- (creation/distribution) claim their tables.

-- ============================================================
-- content-researcher — Content Research & Intelligence
-- ============================================================

-- One row per research packet produced by a research skill run.
-- The packet body lives in the journal / state/pending; this row is the index.
CREATE TABLE IF NOT EXISTS research_packets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    agent         TEXT    NOT NULL DEFAULT 'content-researcher',
    packet_type   TEXT    NOT NULL CHECK (packet_type IN
                          ('social_listening','call_mining','competitor_content')),
    week_starting TEXT    NOT NULL,                -- YYYY-MM-DD (Monday of the run week)
    source_count  INTEGER NOT NULL DEFAULT 0,      -- threads / calls / pages mined
    quiet_week    INTEGER NOT NULL DEFAULT 0,      -- 0/1; explicit "quiet week" flag
    summary       TEXT,                            -- one-paragraph packet summary
    payload_path  TEXT,                            -- file path of the full packet
    created_at    TEXT    NOT NULL                 -- ISO 8601
);

-- Verbatim voice-of-market entries: quotes, questions, pain points.
-- Quotes are verbatim, never paraphrased; every external entry has a source.
CREATE TABLE IF NOT EXISTS voice_bank (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    agent       TEXT    NOT NULL DEFAULT 'content-researcher',
    entry_type  TEXT    NOT NULL CHECK (entry_type IN ('quote','question','pain_point')),
    source      TEXT    NOT NULL CHECK (source IN ('social','sales_call','community')),
    persona     TEXT    CHECK (persona IN ('aaron','erin','hannah','unknown')),
    theme       TEXT,                              -- cluster label
    content     TEXT    NOT NULL,                  -- verbatim text (anonymized for calls)
    source_ref  TEXT,                              -- URL or Grain call reference
    funnel_stage TEXT   CHECK (funnel_stage IN ('top','mid','bottom') OR funnel_stage IS NULL),
    captured_at TEXT,                              -- when the source said it (if known)
    created_at  TEXT    NOT NULL                   -- ISO 8601
);

-- Ranked topic backlog — the output of content-researcher:topic-synthesizer.
-- Scoring: Aaron-fit weighted highest.
CREATE TABLE IF NOT EXISTS topic_backlog (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    agent            TEXT    NOT NULL DEFAULT 'content-researcher',
    topic            TEXT    NOT NULL,
    target_persona   TEXT    NOT NULL DEFAULT 'aaron'
                             CHECK (target_persona IN ('aaron','erin','hannah')),
    funnel_stage     TEXT    CHECK (funnel_stage IN ('top','mid','bottom')),
    content_type     TEXT,                         -- educational guide / tutorial / report / FAQ ...
    score_total      INTEGER,                      -- 0-100
    score_icp        INTEGER,                      -- /25 Aaron-fit weighted highest
    score_search     INTEGER,                      -- /15
    score_aeo        INTEGER,                      -- /20
    score_evidence   INTEGER,                      -- /20
    score_education  INTEGER,                      -- /20 category-creation value
    evidence_summary TEXT,                         -- one-line, e.g. "7 sales calls; 2.4k vol; absent from Perplexity"
    evidence_sources INTEGER NOT NULL DEFAULT 0,   -- count; >=2 required for Tier 2 submission
    status           TEXT    NOT NULL DEFAULT 'candidate'
                             CHECK (status IN ('candidate','submitted','approved','rejected',
                                               'briefed','published','refresh')),
    approved_at      TEXT,                         -- ISO 8601; set on Maya's batch approval
    created_at       TEXT    NOT NULL              -- ISO 8601
);

-- ============================================================
-- content-producer — Content Creation & Distribution
-- ============================================================

-- One row per content brief built from an approved topic.
CREATE TABLE IF NOT EXISTS content_briefs (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    agent              TEXT    NOT NULL DEFAULT 'content-producer',
    topic_id           INTEGER,                    -- -> topic_backlog.id (not enforced)
    working_title      TEXT    NOT NULL,
    target_persona     TEXT    NOT NULL DEFAULT 'aaron'
                               CHECK (target_persona IN ('aaron','erin','hannah')),
    tone_code          TEXT,                       -- humor scale A/B/C per channel-tone YAML
    primary_keyword    TEXT,
    secondary_keywords TEXT,                       -- JSON array of strings
    aeo_questions      TEXT,                       -- JSON array of question strings
    word_count_target  INTEGER,
    brief_path         TEXT,                       -- full brief file (state/pending or briefs dir)
    status             TEXT    NOT NULL DEFAULT 'draft'
                               CHECK (status IN ('draft','ready','in_creation','gated',
                                                 'published','killed')),
    created_at         TEXT    NOT NULL            -- ISO 8601
);

-- Pipeline state per draft as it moves through the creation pod and the gate.
CREATE TABLE IF NOT EXISTS content_drafts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    agent           TEXT    NOT NULL DEFAULT 'content-producer',
    brief_id        INTEGER NOT NULL,              -- -> content_briefs.id (not enforced)
    version         INTEGER NOT NULL DEFAULT 1,
    stage           TEXT    NOT NULL DEFAULT 'drafting'
                            CHECK (stage IN ('drafting','voice_edit','humanize','fact_check',
                                             'optimize','scored','gate','passed','no_pass',
                                             'escalated','killed')),
    loop_count      INTEGER NOT NULL DEFAULT 0,    -- pod loops; max 3 then escalate
    revision_cycle  INTEGER NOT NULL DEFAULT 0,    -- gate No Pass cycles; max 2 then back to brief
    rubric_brand    INTEGER,                       -- /10; gate threshold 8 per dimension
    rubric_education INTEGER,                      -- /10
    rubric_evidence INTEGER,                       -- /10
    rubric_human    INTEGER,                       -- /10
    rubric_factual  INTEGER,                       -- /10
    rubric_seo      INTEGER,                       -- /10
    packet_path     TEXT,                          -- review packet in state/pending/
    gate_decision   TEXT    CHECK (gate_decision IN ('pass','no_pass') OR gate_decision IS NULL),
    gate_feedback   TEXT,                          -- structured No Pass feedback (voice/facts/angle/structure)
    published_url   TEXT,                          -- live URL once a human publishes
    created_at      TEXT    NOT NULL,              -- ISO 8601
    updated_at      TEXT                           -- ISO 8601
);

-- Derivative assets spun from gate-passed posts. Draft-only: humans post.
CREATE TABLE IF NOT EXISTS derivative_assets (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    agent      TEXT    NOT NULL DEFAULT 'content-producer',
    draft_id   INTEGER NOT NULL,                   -- -> content_drafts.id (not enforced)
    channel    TEXT    NOT NULL CHECK (channel IN ('linkedin','x','newsletter','sales_snippet')),
    asset_path TEXT,                               -- draft file in state/pending/
    status     TEXT    NOT NULL DEFAULT 'draft'
                       CHECK (status IN ('draft','pending_approval','approved','posted','rejected')),
    posted_by  TEXT,                               -- human who posted (never an agent)
    posted_at  TEXT,                               -- ISO 8601
    created_at TEXT    NOT NULL                    -- ISO 8601
);

-- Self-register so Librarian step 5 does not re-detect this migration as
-- pending (matches 001/003/005; tick.py also INSERT OR IGNOREs after apply).
CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
INSERT OR IGNORE INTO schema_migrations (version, applied_at)
VALUES ('007_content_engine_tables', datetime('now'));
