# content-producer — Journal

Append-only journal. One `## <ISO-8601Z> | <label>` entry per Tick; the harness reads the last header as its "since" marker.

## 2026-09-04T18:00:00Z | Skill: brief-builder

### MCP Preflight
~~issue tracker (Linear) → bound (optional) · ~~knowledge base (Notion) → not required.

### Queue
1 approved topic picked up: "Runbooks that engineers actually open" (topic-0007, persona aaron).

### Brief
Written to `state/working/briefs/brief-0001.md` · `content_briefs` id=1 status=ready · evidence: 3 voice-bank entries, 1 call · primary keyword "incident runbook template".

### Handoffs Written
- content-producer → chief-of-staff | LOW | Brief ready for calibration review (Maya gate, Priya backup)

## 2026-09-17T16:17:03Z | Daily Tick

Platform `claude` · mode `daily` (harness run; sync, migrations and commit are handled by the harness).
Anchor: Thursday 2026-09-17 · September · Q3 2026.

### MCP Preflight
DEMO_MODE=1: connectors are fixture-backed. No connector was needed this Tick: ~~issue tracker (Linear) → not called (no Linear refs written) · ~~knowledge base (Notion) → not required. All optional; nothing degraded.

### Queue State
1 approved topic unbriefed (topic-0002) · 1 interrupted brief (topic-0001) · 1 draft in flight (draft #1, stage drafting) · 0 at gate · 0 awaiting publish · 1 derivative draft (#1, linkedin).
Handoffs since 2026-09-04T18:00:00Z: none addressed to content-producer. No gate outcomes. Scribe → content-researcher (09-16) confirms topic-0001 and topic-0002 are approved.

### Briefs Built
[brief 3] topic-0002 "A fair on-call rotation in five rules" — refresh of https://orrery.example/blog/post-2
  persona erin · tone blog B · 1200 words
  evidence: 3 entries / 3 distinct sources (2 first_party, 1 open_ugc) · keyword "fair on-call rotation" (rung 4)
  → state/working/briefs/brief-0003.md · content_briefs id=3 status=ready
  → topic_backlog topic-0002 status approved → briefed
  Calibration: brief 2/3, human review before the pod picks it up.
  Verified: row re-read (topic_id=2, erin, path on disk, ready); topic reads briefed; 0 `{{` in the brief; quotes match voice_bank #10/#21/#2 exactly; no hard-fail terms in titles; refresh call re-checked against the final keyword (post-2/7/12 all list "on-call fairness" → refresh stands).

### Skipped
interrupted: topic-0001 has content_briefs id=2 draft/no-path — needs a rebuild decision. The row's target_persona is `erin`, but topic_backlog says `aaron`. If it is rebuilt, the persona has to be corrected, not carried forward.

### Stages Advanced
Gate outcomes: none.
[draft #1] drafting → drafting (loop 0/3). SKIPPED — creation-pod not built (M4). Preconditions: content tables present; topic_backlog reachable; brand/tone YAMLs and context/personas/aaron-platform-engineer.md present.
Publish packages: SKIPPED — publish-package not built (M5). schema-catalog.md readable; no Framer proposal doc found under docs/ (M5 gap).
Derivatives: [derivative #1 linkedin] SKIPPED — derivative-spinner not built (M5); also blocked on a publish confirmation that has not come.
Standing: brand-designer dither-pack request for brief-0001 (handoff content-producer_handoff_01m1t08vvn_5c8ra5) still pending.

### Handoffs Written
- LOW Brief ready — A fair on-call rotation in five rules → chief-of-staff (content-producer_handoff_01m2r2f1bb_v63ym7)
- Harness: session=eed0f700-4e58-49b2-a111-a90d43ea8790 turns=18 cost=$1.36
