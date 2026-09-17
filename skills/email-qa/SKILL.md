---
name: email-qa
description: >
  Pre-send QA for HubSpot marketing emails — workflows and batch campaigns. Trigger ANY TIME the user wants
  an email reviewed before sending: "QA this email", "check this before it goes out", "proof this",
  "pre-send check", "can you review this email", "check for broken links", "check the copy", "run a QA pass",
  "is this ready to send", "does this pass brand voice", "I need sign-off on this email", or any variation of
  wanting an email checked before launch. Also trigger when the user pastes HTML or provides a HubSpot email ID
  or hs-sites.com preview link. Checks: subject line (spelling, grammar, length, tone), preview text, body copy
  (spelling, grammar, competitor names, fear-based language, product name casing), all links (live HTTP
  verification + UTM check), image alt text, and {{COMPANY}} brand voice. Returns a pass/fail report with verdict:
  Ready to Send, Ready to Send with Fixes, or Do Not Send.
---

## {{COMPANY}} Email QA Configuration

This skill is configured for **{{COMPANY}}** — an incident management and on-call platform for engineering teams. Before performing any brand voice assessment, read `${CLAUDE_PLUGIN_ROOT}/context/brand-pack/brand.md` for {{COMPANY}}'s complete brand reference: voice pillars, persona lenses, tone scale, competitor terminology rules, and tone transformation examples.

**Product name rule**: The product name is always **{{COMPANY}}** — sentence case with a capital O only. Any instance of "{{company_slug}}" in a brand context — in body copy, sign-offs, headlines, or CTAs — is a spelling/capitalization error and must be flagged.

---

# Email QA Skill

A structured pre-send quality assurance workflow for HubSpot marketing emails. Works for both automated workflow emails and batch campaigns.

## What Gets Checked

1. **Subject line** — spelling, grammar, length, tone alignment
2. **Preview text** — spelling, grammar, non-duplication of subject
3. **Body copy** — spelling, grammar, product name casing, competitor names, fear-based framing
4. **Links** — live URL verification + format/UTM check for every link
5. **Image alt text** — presence and quality on all images
6. **Brand voice** — high-level alignment with {{COMPANY}}'s Clear/Authoritative/Approachable pillars

---

## Step 1: Retrieve the Email

Determine what the user has provided and retrieve the email content. **If the user says "run QA", "check the latest email", or gives no specific source, default to Option D.**

### Option D: Drive Folder — Latest File (Default / On-Demand)

This is the default pathway when QA is invoked from the chat or command line without a specific email provided.

**Folder details (from the profile — set these per company, never hardcode an id here):**
- Watch folder ID: `{{DRIVE_QA_WATCH_FOLDER_ID}}`
- Watch folder URL: `https://drive.google.com/drive/folders/{{DRIVE_QA_WATCH_FOLDER_ID}}`
- Reports subfolder ID: `{{DRIVE_QA_REPORTS_FOLDER_ID}}`
- Reports subfolder URL: `https://drive.google.com/drive/folders/{{DRIVE_QA_REPORTS_FOLDER_ID}}`

**Step D1 — Find the latest file:**

Use `google_drive_search` to list files in the watch folder. Sort by `modifiedTime desc` and take the first result. Note its file ID, file name, and modified timestamp.

**Step D2 — Extract the HTML source:**

Navigate Chrome to `https://drive.google.com/open?id={FILE_ID}` and wait for the Drive viewer to load (the page title should change to the file name). Then use this JavaScript to extract the full HTML source — Drive renders the file as a raw text node in the viewer:

```javascript
let found = null;
const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
let node;
let maxLen = 0;
while (node = walker.nextNode()) {
  if (node.textContent.length > maxLen && node.textContent.includes('DOCTYPE')) {
    maxLen = node.textContent.length;
    found = node;
  }
}
found ? found.textContent.substring(0, 80000) : 'NOT_FOUND'
```

If the result is `NOT_FOUND` or the page is still loading (`status "Loading"` visible in `read_page`), wait a few seconds and retry once.

**Step D3 — Save locally and parse:**

Write the extracted HTML to `/tmp/email-qa-input.html` using the Write tool. Then run this Python script to extract all QA-relevant components:

```python
from html.parser import HTMLParser
import re

with open('/tmp/email-qa-input.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Subject / title
title = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
print('TITLE:', title.group(1).strip() if title else 'NOT FOUND')

# Preview text — hidden span near top of body
preview = re.search(
    r'(?:display\s*:\s*none|max-height\s*:\s*0)[^>]*>([^<]{20,})<',
    html, re.IGNORECASE
)
print('PREVIEW:', preview.group(1).strip() if preview else 'NOT FOUND')

# All HTTP links
links = re.findall(r'href=["\']([^"\']+)["\']', html)
http_links = [l for l in links if l.startswith('http')]
print('LINKS:', http_links)

# All images + alt text
imgs = re.findall(r'<img[^>]*>', html, re.IGNORECASE)
for img in imgs:
    alt = re.search(r'alt=["\']([^"\']*)["\']', img)
    src = re.search(r'src=["\']([^"\']+)["\']', img)
    src_short = src.group(1).split('/')[-1][:50] if src else 'unknown'
    print(f'IMG: {src_short} | ALT: {alt.group(1) if alt else "MISSING"}')

# Lowercase "{{company_slug}}" brand violations
violations = re.findall(r'(?<![A-Za-z]){{company_slug}}(?![A-Za-z])', html)
print('LOWERCASE {{company_slug}} COUNT:', len(violations))

# Competitor names
competitors = ['{{COMPETITOR_A}}', '{{COMPETITOR_C}}', '{{COMPETITOR_D}}', '{{COMPETITOR_G}}', '{{COMPETITOR_B}}', '{{COMPETITOR_F}}',
               '{{COMPETITOR_H}}', '{{COMPETITOR_E}}', '{{COMPETITOR_I}}', '{{COMPETITOR_M}}']
for c in competitors:
    if re.search(re.escape(c), html, re.IGNORECASE):
        print(f'COMPETITOR FOUND: {c}')
```

Use this output as the basis for all QA checks below. Proceed to Step 2.

**Step D4 — Upload the report after Step 3:**

After completing the QA report:
1. Save the report to `/tmp/{email-subject}-QA-report.md`
2. Navigate Chrome to the reports subfolder: `https://drive.google.com/drive/folders/{{DRIVE_QA_REPORTS_FOLDER_ID}}`
3. Use `file_upload` to upload the report file to that folder
4. Resolve the scan log path at runtime — run this command to find the current workspace:
   ```bash
   # ${WORKSPACE_MOUNT} is the marketing workspace directory for this run — export it in
   # the environment; never hardcode a host mount path in a skill.
   echo "${WORKSPACE_MOUNT:?set WORKSPACE_MOUNT to the marketing workspace path}"
   ```
   Append `/email-qa-scan-log.json` to the result to get the full path. If the file doesn't exist yet, create it with `{ "scanned_files": {} }` before updating. Then add an entry under `scanned_files` keyed by file ID:

```json
"FILE_ID": {
  "title": "filename.html",
  "last_modified": "ISO timestamp from Drive",
  "last_scanned": "ISO timestamp now",
  "verdict": "READY TO SEND | READY TO SEND WITH FIXES | DO NOT SEND",
  "report_file": "report filename uploaded to Drive"
}
```

---

### Option A: HubSpot Preview URL

If the user provides a preview URL (e.g., `https://hs-XXXXX.hs-sites.com/...` or any `hubspot.com/email/preview/...` link):

Use `WebFetch` to retrieve the rendered HTML. If the page requires authentication or WebFetch cannot render it fully, use Claude in Chrome to navigate to the URL and extract the HTML source via JavaScript.

### Option B: HubSpot Email ID

If the user provides a numeric HubSpot email ID (e.g., `12345678`):

Try fetching via HubSpot CRM tools using `objectType: "marketing_email"` and the provided ID. If the API returns the email's subject, preview text, and HTML body, proceed. If the marketing email object type is unsupported or the HTML body is unavailable, ask the user to:
- Provide the HubSpot preview URL instead, or
- Paste the raw HTML (in HubSpot: Email > Actions > Export HTML)

### Option C: Pasted HTML

If raw HTML is pasted directly into the chat, use it as-is.

### Parsing Email Components

Once you have the HTML source, extract these components. Write a short Python script if the HTML is long or complex:

- **Subject line**: Often not in the HTML body — ask the user to confirm it if not found in `<title>` tags or HubSpot API metadata
- **Preview text**: Typically a hidden `<span>` near the top of `<body>` with styles like `display:none; max-height:0; overflow:hidden`
- **Body copy**: Visible text in `<td>`, `<p>`, `<span>` tags — skip unsubscribe/footer boilerplate
- **Links**: All `<a href="...">` values
- **Images**: All `<img>` tags — check `alt` attribute presence and value

### HubSpot Tokens — How to Treat Them

**Footer tokens** (`{{unsubscribe_link}}`, `{{manage_preferences_link}}`): These are always HubSpot-managed and always correct. Mark them PASS in the links table and don't comment on them further.

**Personalization tokens** (e.g., `{{contact.firstname}}`, `{{company.name}}`): These are intentional and correct. Do not flag as errors. A soft ⚠️ WARN is acceptable only if a token is used in a prominent position where a blank value would look obviously broken (e.g., "Hi ," in the greeting of a cold email). Never block sending over a personalization token.

---

## Step 2: Run the QA Checks

Work through each section. Record **PASS**, **FAIL**, or **WARN** (warn = worth noting, not a blocker) for each item.

### 2.1 Subject Line

| Check | Pass Criteria |
|-------|---------------|
| Spelling | No misspellings |
| Grammar | Correct per {{COMPANY}} brand standards |
| Length | ≤ 50 characters is ideal; flag as WARN if > 60 |
| Tone | No fear-based framing; no corporate announcement language |
| Product name | "{{COMPANY}}" is title case — flag any lowercase "{{company_slug}}" |

### 2.2 Preview Text

| Check | Pass Criteria |
|-------|---------------|
| Spelling | No misspellings |
| Grammar | Correct per {{COMPANY}} brand standards |
| Present | Preview text exists (empty preview causes email clients to pull body text as fallback) |
| Adds value | Complements the subject line; does not repeat it verbatim |

### 2.3 Body Copy

Run these checks on the visible body copy, excluding the footer/unsubscribe section:

| Check | Pass Criteria |
|-------|---------------|
| Spelling | No misspellings |
| Grammar | No unintentional errors (see brand grammar note below) |
| Product name | "{{COMPANY}}" is always title case — flag every instance of lowercase "{{company_slug}}" used as a brand reference |
| No competitor names | {{COMPETITOR_A}}, {{COMPETITOR_C}}, {{COMPETITOR_D}}, {{COMPETITOR_G}}, {{COMPETITOR_B}}, {{COMPETITOR_F}}, {{COMPETITOR_H}}, {{COMPETITOR_E}}, {{COMPETITOR_I}}, {{COMPETITOR_M}} — none should appear by name |
| No fear-based language | Does not lead with risk, fines, penalties, or worst-case scenarios |

**Brand grammar note**: Before flagging a grammar issue, check `${CLAUDE_PLUGIN_ROOT}/context/brand-pack/brand.md`. {{COMPANY}} allows intentional fragments in headlines and CTAs if they read cleanly (e.g., "Ship faster." or "No compliance headaches."). These are deliberate — do not flag them.

### 2.4 Links

For every link in the email (skip HubSpot footer tokens as noted above):

**Format check** (no request needed):
- URL is well-formed and uses HTTPS
- UTM parameters are present and properly encoded on campaign emails
- No obviously broken patterns (double slashes, malformed query strings)

**Live check** — use `WebFetch` for each non-token URL:
- Returns HTTP 200 (not 404, 5xx, or a redirect loop)
- Final destination makes contextual sense given the CTA or surrounding link text
- Does not redirect more than 2 hops to an unexpected page

Flag if: error status, destination mismatch, or UTM parameters are absent on a campaign email that should be tracked.

### 2.5 Image Alt Text

For every `<img>` tag in the email body:

| Check | Pass Criteria |
|-------|---------------|
| Alt attribute exists | `alt` attribute is present on the tag |
| Alt text is not empty | `alt=""` only acceptable for decorative spacer/pixel images (typically 1×1px) |
| Alt text is descriptive | Not a filename, not generic ("image", "banner", "photo") |
| Alt text is purposeful | Describes what the image shows or contributes in context |

### 2.6 Brand Voice

Read `${CLAUDE_PLUGIN_ROOT}/context/brand-pack/brand.md` before this section.

Assess against {{COMPANY}}'s three core voice pillars:

- **Clear**: Direct and reader-first. Jargon explained or avoided. Sentences reasonably concise.
- **Authoritative**: Confident without arrogance. Claims are supportable. No defensive or legalistic hedging.
- **Approachable**: Reads like a smart, warm colleague — not a corporate entity. Inclusive, human, not robotic.

Also verify:
- **Removal over capability**: Email leads with what gets easier or disappears — not with a feature list or capability announcement
- **No announcement tone**: Phrases like "We are thrilled to announce", "revolutionary", "comprehensive solution" violate {{COMPANY}}'s voice
- **Persona alignment**: Erin (technical founder) = energetic clarity, conversational and pragmatic / B; Hannah (VP Engineering) = reassuring authority, precise and evidence-led / A (dry wit only)
- **No prevention claims**: {{COMPANY}} shortens, routes, and reviews incidents — it never prevents them. "Never miss an alert again" and "zero downtime" are hard fails
- **No fear-based reliability**: no outage-shaming, no downtime-cost math, no screenshots of angry customers (the cardinal sin)
- **No competitor names by name**: Already checked in body copy, but flag here if missed

Flag major deviations only. Do not nitpick minor tone variation unless it actively contradicts a pillar.

---

## Step 3: Produce the QA Report

Use this exact structure:

---

## ✉️ Email QA Report

**Email**: [subject line or HubSpot ID]
**Date**: [today's date]
**Type**: [Automation / Batch Campaign]

---

### QA Summary

| Section | Status | Issues |
|---------|--------|--------|
| Subject Line | ✅ PASS / ❌ FAIL / ⚠️ WARN | [count or "None"] |
| Preview Text | ✅ / ❌ / ⚠️ | |
| Body Copy | ✅ / ❌ / ⚠️ | |
| Links | ✅ / ❌ / ⚠️ | |
| Image Alt Text | ✅ / ❌ / ⚠️ | |
| Brand Voice | ✅ / ❌ / ⚠️ | |

---

### Verdict

Use one of these three verdicts — nothing else:

- **🟢 READY TO SEND** — No fails. May have minor warnings that don't need fixing before launch.
- **🟡 READY TO SEND WITH FIXES** — Has issues that should be resolved, but nothing that would cause real harm or embarrassment if sent. Fix before next send or use judgment on urgency.
- **🔴 DO NOT SEND** — Has one or more hard blockers: spelling errors in subject/body, broken links, missing required elements, competitor names named directly, or serious brand violations.

---

### Detailed Findings

*(Only include sections with FAIL or WARN status — skip clean sections to keep the report scannable)*

**[Section Name]**
- ❌ [Issue description] — *exact text or element*
  > Fix: [concrete recommendation]

- ⚠️ [Warning description] — *exact text or element*
  > Note: [brief explanation]

---

### Links Verified

| URL | HTTP Status | Destination | UTMs | Result |
|-----|-------------|-------------|------|--------|
| `[url]` | 200 / 404 / etc. | [landing page description] | ✅ / ❌ / N/A | ✅ / ❌ |
| `{{unsubscribe_link}}` | HubSpot managed | Unsubscribe | N/A | ✅ |
| `{{manage_preferences_link}}` | HubSpot managed | Preference center | N/A | ✅ |

---

### Images

| Image | Alt Text | Status |
|-------|----------|--------|
| [src or context] | [alt text value or "missing"] | ✅ / ❌ Missing / ⚠️ Generic |

---

## Output Standards

- If the email passes cleanly, say so clearly: "This email passed all QA checks. Ready to send."
- Every FAIL should include a specific recommended fix — hand the copywriter an actionable to-do, not just a problem description
- Do not flag intentional {{COMPANY}} brand fragments (punchy CTAs, short headers) as grammar errors
- HubSpot footer tokens are always PASS — do not comment on them
- Only soft-warn on personalization tokens if a blank value would be genuinely awkward in context
- Surface genuine issues only — false positives erode trust in the QA process over time
