<!--
Use Case Library article template, filled by content-producer:use-case-builder, published (by a
human) to Notion under Marketing → Use Cases.
Mirrors the canonical Notion "Template" page (Use Cases library). Replace every
{{placeholder}} and delete guidance comments before publishing.

HARD RULE (content-producer:use-case-builder): every capability described in sections 1 and 3 must
trace to a PASS in the run's smoke-test evidence log. Do not describe a step, tool, or
outcome that was not exercised against the live {{COMPANY}} MCP (or an equivalent validated
source). Reframe or drop anything unvalidated. Never write it as if it works.

EXTENSIBILITY: this is the single "use case article" template (decision 2a). Additional
document templates can be added later as templates/use-cases/<name>.md and selected by
the skill; do not fork this file for one-off use cases.
-->

# {{Title}}
<!-- Plain-language outcome. Format: "[Do X] with {{COMPANY}}." No product jargon.
     Example: "Model next quarter's on-call load before you change the rotation with {{COMPANY}}." -->

**One-liner:** {{≤100 characters. Expands on the title. No jargon. Lead with the relief/outcome.}}

**Filter tags**

| Tag type | Value |
|----------|-------|
| Category | {{On-Call · Routing · Escalation · Alert Hygiene · Postmortems · Ownership · Reporting · Integrations; pick the closest}} |
| Persona / Ideal for | {{Aaron the Platform Engineer · Hannah the VP Engineering · Erin the Technical Founder · Anna (Finance) · Jake (IT & SecOps); pick all that genuinely apply}} |

**Recommended for:** {{CLI · API · MCP · {{COMPANY}} Agent; list ONLY the surfaces validated in this run's evidence log}}

---

## 1. What It Does

<!-- 2–3 sentences. LEAD WITH THE BENEFIT FOR THE TARGET READER (e.g. the engineering leader
     and/or the platform engineer): what they can now do or no longer have to do, then the outcome
     detail. No product names or technical terms. No fear-based reliability framing. -->
{{benefit-led paragraph; name the reader and the payoff first}}

{{Optional: a single screenshot or short GIF of the real result. "Image coming soon." if none.}}

---

## 2. Demo

*Video coming soon.*
<!-- If no video yet, keep this placeholder. Guidance for the eventual video:
     - Show the trigger (what the reader asks / what event fires)
     - Show {{COMPANY}} responding (pulling the live records)
     - Show the output (the finished result)
     - No narration required; captions preferred -->

---

## 3. How to Set It Up

<!-- Step-by-step. Each step = one action. For {{COMPANY}} Agent / MCP, a step can be a suggested
     copy-paste prompt. Every prompt here must have been exercised in the smoke test. -->

### Option A — Use your AI app and {{COMPANY}} MCP

#### Setting up your MCP connection
Before you start, you'll connect your AI app to {{COMPANY}}. In an MCP-compatible client, add {{COMPANY}} as a remote connector using the link below. For more detailed instructions, check out our MCP guide.
```plain text
https://{{API_DOMAIN}}/mcp
```

#### Step 1: {{Action title}}
{{One sentence.}}
```plain text
{{tested copy-paste prompt}}
```

#### Step {{N}}: {{Send / apply}}
{{Closing action.}}
> 💡 **Tip:** {{optional}}

### Option B — Ask {{COMPANY}} Agent (in Slack)

#### Setting up {{COMPANY}} Agent
To turn on {{COMPANY}} Agent in Slack, sign into your {{COMPANY}} account and go to the Features catalog (https://{{APP_DOMAIN}}/features). Note that {{COMPANY}} Agent is currently in beta.

#### Step 1: {{Action title}}
{{One sentence on what this step does and why.}}
```plain text
{{tested copy-paste prompt}}
```
> 💡 **Tip:** {{optional clarifying note for a non-technical reader, or where to find a value in the UI}}

#### Step {{N}}: Review and send / apply
{{What the reader gets back and how they act on it. Nothing changes until the reader confirms.}}

---

## 4. What You'll Need

<!-- Bulleted prereqs. Maximum 5 items. -->
- A {{COMPANY}} workspace with the relevant records
- {{permission / access level needed}}
- **For {{COMPANY}} Agent:** {{COMPANY}} Agent enabled in your Slack workspace (currently in beta)
- **For MCP:** an MCP-compatible AI client (e.g., Claude or ChatGPT) connected to {{COMPANY}}
- {{any other hard requirement}}

---

## 5. Related Use Cases

<!-- 2–3 cards linking to related library pages: title, one-liner, available-on chips.
     "TBD" if none identified yet. -->
{{TBD}}

<!--
------------------------------------------------------------------------------------------
SMOKE-TEST EVIDENCE (kept with the draft, NOT published)
Every row is one claim in this article validated against the live {{COMPANY}} MCP.
| Claim / step | Tool(s) exercised | Result | Notes |
Populated by the skill run; lives at state/pending/<date>/use-case-<slug>-evidence.md.
------------------------------------------------------------------------------------------
-->
