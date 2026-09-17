<!--
Content brief template — filled by content-producer:brief-builder, consumed by content-producer:creation-pod.
One file per approved topic at state/working/briefs/brief-<content_briefs.id, zero-padded to 4>.md (e.g. brief-0001.md).
Replace every {{placeholder}}. Delete the "Refresh delta" section for net-new pieces.
Every section must trace to a source — no generic outlines.
-->

# Brief: {{working_title}}

| | |
|---|---|
| **Topic ID** | {{topic_id}} (topic_backlog) |
| **Type** | {{net-new | refresh}} |
| **Content type** | {{guide | tutorial | report | faq | comparison}} |
| **Target persona** | {{aaron | erin | hannah}} |
| **Tone code** | {{e.g. blog A–B}} |
| **Funnel stage** | {{top | mid | bottom}} |
| **Word-count target** | {{range}} |
| **Topic score** | {{N}}/100 · evidence quotes: {{E}} |

## Working titles
1. **{{recommended title}}** ← recommended
2. {{alternative}}
3. {{alternative}}
<!-- No Aaron hard-fail terms: "easy-to-use", "all-in-one", "streamline", "simplify",
     feature checklists, "AI will replace your team". No blocked competitor names. -->

## The educational job
{{One sentence: what the reader can DO after reading — a config, checklist, working
example, or mental model. This is the spine of the outline.}}

## Keywords
- **Primary:** {{keyword}} ({{intent}}) — source: {{keyword_rankings | candidate-handoff | content_inventory | theme}}
- **Secondary:** {{2–5 comma-separated}}

## AEO question set
<!-- From docs/aeo-tracked-prompts.md where tracked; else candidate question targets. -->
- {{question the piece must answer}}
- {{…}}

## Outline (H2 / H3)
<!-- Each H2 maps to the educational job and/or an AEO question + the evidence it uses. -->
1. **{{H2}}** — answers: {{AEO question / job}} · evidence: {{quote ref / stat / code example}}
   - {{H3}}
2. **{{H2}}** — …
<!-- SERP features to target: {{featured snippet | PAA | none}} — earned by section {{n}}. -->

## Evidence bundle (verbatim — from topic_evidence → voice_bank)
<!-- Anonymized quotes with source_ref. These are the market's actual words; use them. -->
- [{{entry_type}} · {{persona}} · {{funnel_stage}}] "{{verbatim quote}}" ({{source_ref}})
- {{…}}

### Additional evidence the pod must source + fact-check
<!-- 100% of claims verified with a source or removed. -->
- {{stat needed + acceptable source type}}
- {{code / API / MCP example to include}}
- {{claim requiring a primary source}}

## Internal links (from content_inventory)
- **Link to:** {{url}} — {{why relevant}}
- **Link from:** {{existing url that should link to this piece}}
- **Cannibalization:** {{none | warns: {{url}} already targets the primary keyword → consolidate / make this a refresh}}

## Refresh delta (refresh pieces only)
<!-- Delete for net-new. -->
- **Existing piece:** {{url}}
- **What this adds:** {{new angle / persona / AEO format / freshness the existing piece lacks}}

## CTA
{{persona + funnel-appropriate call to action}}

---
*Built by content-producer:brief-builder from topic_backlog #{{topic_id}}. Status set per the
calibration gate. Creation-pod: draft strictly from this brief and its evidence.*
