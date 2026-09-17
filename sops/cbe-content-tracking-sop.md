# Content Hub Behavioral Event Tracking — Maintenance & Registry SOP

**Version:** 2.1
**Owner:** Marketing / GTM Ops
**Applies to:** Anyone adding or maintaining tracked content elements on the {{COMPANY}} content hub
**Tools:** `~~web analytics` tag manager (Google Tag Manager), `~~crm` (HubSpot Marketing Hub Enterprise), `~~cms` (Framer), `~~knowledge base` (Notion)

---

## What This Is

The content hub uses HubSpot Custom Behavioral Events (CBEs) to capture engagement signals — link clicks, PDF downloads, and CTA interactions — without requiring a form gate. When a visitor clicks a tracked element, a GTM tag fires and posts the event to the visitor's HubSpot contact record along with content metadata and UTM attribution data.

These events feed three downstream systems:

1. **Lifecycle scoring** — CBE occurrences contribute to lead score calculations that drive MQL and SAL thresholds.
2. **Workflow enrollment** — HubSpot workflows can enroll contacts based on specific CBE property combinations (e.g., anyone who clicked a case study and visited the pricing page).
3. **Content attribution** — CBE data enables reporting on which content assets drive pipeline, by source and segment.

The tracking system is live. This SOP covers how to maintain it: adding new tracked elements, updating the metadata registry, running quarterly audits, and troubleshooting.

**Time to complete:** ~15 minutes per new tracked element | ~30 minutes for a quarterly audit

---

## Section 1: Prerequisites

Before making any changes to the tracking system, confirm the following:

- **GTM publish access** for the {{COMPANY_DOMAIN}} container (`GTM-0000000`). If the Submit button is grayed out, you need elevated permissions — contact {{CEO_FIRST}}.
- **HubSpot admin access** (Marketing Hub Enterprise). Required to view CBE schemas and event occurrence data.
- **Framer editor access** to the content hub project. Required to add HTML attributes to tracked elements.
- **Notion access** to the [Content Tracking Registry](https://www.notion.example/{{NOTION_PAGE_ID}}) — the live database inside the Knowledge Hub > Marketing > Formless Click-Event Metadata Table page (see Section 3).
- **GTM Preview mode familiarity.** You will use Preview mode to validate every change before publishing. If you have not used Preview mode before, run through Google's Tag Manager Preview documentation first.
- **HubSpot tracking script** must be installed on all content hub pages. This is already in place. If a new subdomain or page template is created outside Framer, verify the tracking script is present before adding tracked elements.

---

## Section 2: System Architecture

This section describes what exists. It is a reference, not a setup guide.

### HubSpot Custom Behavioral Events

Two CBEs are configured, both associated with the Contact object:

**Content Link Clicked** (`pe{portalID}_content_link_clicked`)

| Property | Type | Description |
|----------|------|-------------|
| `content_title` | String | Human-readable asset name |
| `content_type` | String | guide, case_study, datasheet, pdf, template, webinar |
| `element_id` | String | HTML ID of the clicked element |
| `destination_url` | URL | Where the link points |
| `page_url` | URL | Page where the click occurred |
| `utm_source` | String | UTM source from the session |
| `utm_medium` | String | UTM medium from the session |
| `utm_campaign` | String | UTM campaign from the session |
| `utm_content` | String | UTM content from the session |
| `utm_term` | String | UTM term from the session |
| `gclid` | String | Google Click ID from the session |

**Content CTA Clicked** (`pe{portalID}_content_cta_clicked`)

| Property | Type | Description |
|----------|------|-------------|
| `cta_label` | String | Visible text or data-cta-label value of the CTA |
| `cta_destination` | URL | URL the CTA points to |
| `element_id` | String | HTML ID of the CTA element |
| `page_url` | URL | Page where the click occurred |
| `utm_source` | String | UTM source from the session |
| `utm_medium` | String | UTM medium from the session |
| `utm_campaign` | String | UTM campaign from the session |
| `utm_content` | String | UTM content from the session |
| `utm_term` | String | UTM term from the session |
| `gclid` | String | Google Click ID from the session |

### GTM Tag and Trigger Structure

| Component | Name | Type | Purpose |
|-----------|------|------|---------|
| Tag | `HS - Content Link Click` | Custom HTML | Fires `content_link_clicked` CBE via `_hsq.push` |
| Tag | `HS - Content CTA Click` | Custom HTML | Fires `content_cta_clicked` CBE via `_hsq.push` |
| Tag | `UTM + GCLID Capture` | Custom HTML | Fires on all pages; writes UTM params and GCLID to sessionStorage with `hs_` prefix |
| Trigger | `HS - Tracked Content Link` | Click — All Elements | Fires when click class contains `hs-track-content` AND does not contain `hs-track-cta` |
| Trigger | `HS - Tracked CTA Click` | Click — All Elements | Fires when click class contains `hs-track-cta` |
| Variable | `Attribution Params` | Custom JavaScript | Returns UTM/GCLID object; checks current URL first, then sessionStorage fallback |
| Variable | `Content Metadata Lookup` | Custom JavaScript | Maps element IDs to content titles and types (see Section 3) |
| Variable | `CTA Label` | DOM Element | Reads `data-cta-label` attribute from `.hs-track-cta` elements |

The mutual exclusion between triggers is intentional. A CTA element carries both classes (`hs-track-content hs-track-cta`). The content link trigger's exclusion condition prevents double-firing. Only the CTA tag fires on CTA elements.

### UTM and Attribution Persistence

The `UTM + GCLID Capture` tag fires on every page load and writes URL parameters to sessionStorage as `hs_utm_source`, `hs_utm_medium`, etc. The `Attribution Params` variable reads from the current URL first and falls back to sessionStorage, ensuring UTM data persists across page navigation within the same browser tab.

sessionStorage is tab-scoped. A visitor who manually opens a new tab starts a fresh session. This is expected and negligible for CBE purposes since click events fire in the originating tab.

### Identity Resolution

CBE tracking relies on the HubSpot `hutk` cookie. Contacts who have clicked a tracked HubSpot email or submitted a HubSpot form have a hutk-to-record linkage. Their CBE data appears on the contact timeline immediately.

Anonymous visitors (no hutk linkage) still generate CBE data. It is captured and retroactively associated when the visitor later identifies themselves via email click or form submission. This is expected behavior, not a bug.

---

## Section 3: The Content Metadata Lookup Variable

This is the core maintenance item. Every tracked element on the content hub must have a corresponding entry in this GTM variable. When a tracked element is clicked, the variable resolves the element's HTML `id` attribute to a human-readable title and content type. If no match is found, it returns the raw element ID as the title and `unknown` as the type.

### Entry Format

Each entry in the variable is a key-value pair inside a JavaScript object:

```javascript
'oncall-rotation-guide': { title: 'On-Call Rotation Design Guide', type: 'guide' },
```

- The **key** is the exact HTML `id` attribute on the tracked element in Framer. It is case-sensitive.
- `title` is the human-readable name that appears on the HubSpot contact timeline.
- `type` is one of the valid content type values (see below).

### Naming Convention

Element IDs must be lowercase, hyphen-separated, and descriptive. They should describe the content, not internal strategy or audience segments.

**Format:** `{category}-{asset-slug}`

**Good examples:**

| Element ID | Title | Type |
|------------|-------|------|
| `oncall-rotation-guide` | On-Call Rotation Design Guide | guide |
| `alert-hygiene-checklist` | Alert Hygiene Audit Checklist | template |
| `incident-runbook-pdf` | Incident Commander Runbook | pdf |
| `reliability-roundtable-ep4` | Reliability Roundtable — Episode 4 | webinar |
| `cta-hero-start-free` | Start Free (Hero CTA) | — |
| `form-demo-request` | Request a Demo (Footer CTA) | — |

**Do not** encode competitive intelligence, pricing strategy, or audience segmentation labels into element IDs. These IDs are visible in the page source and DOM to anyone who inspects the page.

### Valid content_type Values

| Value | Use For |
|-------|---------|
| `guide` | Long-form written content (ebooks, playbooks, how-to guides) |
| `case_study` | Customer stories, implementation examples |
| `datasheet` | Comparison tables, feature breakdowns, spec sheets |
| `pdf` | Downloadable PDF assets that do not fit other categories |
| `template` | Reusable frameworks, checklists, calculators |
| `webinar` | Recorded or on-demand webinar content |

If a new content type is needed, add it to this table, update the HubSpot CBE property description, and use it consistently going forward. Do not create one-off types.

### Fallback Mechanism

If a clicked element's `id` does not match any key in the registry, the variable returns:

```javascript
{ title: clickedId || 'unknown', type: 'unknown' }
```

This means unregistered elements still generate CBE data — they just appear with the raw element ID (or `unknown`) as the content title. Use HubSpot's Event Management Analyze tab to spot unregistered elements: filter for events where `content_type` = `unknown`.

### How to Add, Update, Rename, and Deprecate Entries

**Adding a new entry:**
Add a new line to the registry object in the GTM variable. Place it in the correct section (organized by content type) with a comment if helpful.

```javascript
// --- GUIDES ---
'oncall-rotation-guide': { title: 'On-Call Rotation Design Guide', type: 'guide' },
'escalation-policy-guide': { title: 'Escalation Policy Design Patterns', type: 'guide' },
```

**Updating an existing entry:**
If a content asset is renamed or its type changes, update the existing entry in place. Do not add a second entry with the same key.

**Renaming an element ID:**
If the HTML `id` changes in Framer (e.g., due to a slug update), you must update both sides simultaneously:
1. Change the `id` attribute in Framer.
2. Change the key in the GTM registry to match.
3. Publish both Framer and GTM.

If you update Framer first without updating GTM, clicks on the renamed element will fall through to the fallback and appear as `unknown` until the GTM variable is synced.

**Deprecating an entry:**
Comment out the entry in the GTM variable. Do not delete it outright — the comment serves as a record of what was previously tracked. If the entry has been deprecated for two or more quarters with no reactivation, it can be removed entirely.

```javascript
// DEPRECATED Q{N} {YEAR} — page removed
// 'old-asset-slug': { title: 'Deprecated Asset Name', type: 'guide' },
```

### The Notion Content Tracking Registry

**Registry:** [Formless Click-Event Metadata Table](https://www.notion.example/{{NOTION_PAGE_ID}}) — Knowledge Hub > Marketing

The Notion registry is the source-of-truth database for all tracked elements. It mirrors the GTM variable but adds status tracking, dates, and notes that do not belong in the GTM codebase. The database is live with three views: **All Entries**, **Live** (filtered), and **Deprecated** (filtered).

**Schema:**

| Column | Type | Description |
|--------|------|-------------|
| Element ID | Title | The exact HTML `id` attribute — must match the GTM registry key. Case-sensitive. |
| Content Title | Text | Human-readable asset name shown on the HubSpot contact timeline |
| Content Type | Select | guide, case_study, datasheet, pdf, template, webinar |
| Status | Select | Staged, Live, Inactive, Deprecated |
| Date Added | Date | When the entry was first created |
| Last Verified | Date | Last date the entry was confirmed active — updated during each quarterly audit |
| Notes | Text | Context: e.g., "PDF opens in new tab," "CMS-driven element," "replaced by v2" |

**Status definitions:**

| Status | Meaning |
|--------|---------|
| Staged | Entry added to Notion and GTM variable, not yet QA'd or published |
| Live | Entry is published in GTM and actively tracking |
| Inactive | Zero occurrences in the last 90 days, but the Framer page is still live |
| Deprecated | Framer page or element removed — entry commented out in GTM |

**Bootstrap (one-time, not yet complete):**
The registry currently contains three illustrative example rows. To bootstrap: open the GTM Content Metadata Lookup variable, add each existing key-value pair as a row in the Notion registry, set Status = Live and Date Added = today, then delete the example rows. After bootstrap, Notion is the source of truth.

**Steady-state workflow:**
The direction of updates is **Notion first, then GTM.** Add or modify entries in Notion, then sync the change to the GTM variable. This ensures Notion always reflects the current state and GTM never drifts ahead.

**Until the bootstrap is complete, the GTM variable is the de facto source of truth.** All procedures that reference the Notion registry can be performed directly in GTM in the interim.

### Common Mistakes

**Case sensitivity.** Element IDs are case-sensitive. `OnCall-Rotation-Guide` does not match `oncall-rotation-guide`. Use lowercase-with-hyphens consistently in both Framer and GTM.

**Duplicate keys.** If two entries share the same key, the last one in the object wins. This is a silent override — no error is thrown. Always search the existing registry before adding a new entry.

**Stale entries.** An element removed from Framer but still in the GTM registry wastes space but causes no harm. The reverse (element in Framer but not in GTM) means clicks register as `unknown`. The quarterly audit catches both cases.

**Strategic information in element IDs.** Element IDs appear in the page source. Do not use them to encode internal campaign names, competitive positioning, or audience segment labels. Use descriptive but neutral slugs.

---

## Section 4: Adding a New Tracked Element

Run this process each time a new content link or CTA is added to the content hub and needs tracking.

### Step 1: Add HTML Attributes in Framer

On the element to be tracked:

1. Add a unique `id` attribute following the naming convention in Section 3: `{category}-{asset-slug}`, all lowercase with hyphens.
2. Add the appropriate class:
   - `hs-track-content` for content engagement links (guides, PDFs, case studies, templates).
   - `hs-track-cta` for high-intent CTAs (Book Demo, Start Trial, Talk to Sales).
3. For icon or image CTAs with no visible text: add `data-cta-label="Your CTA Label"` so the CTA tag can resolve a human-readable label.
4. For PDF links: set `target="_blank"` so the PDF opens in a new tab. This prevents a race condition where the browser navigates away before the GTM click event fires.

**Decision tree — which class to use:**

- If the element is a high-intent conversion CTA → `hs-track-cta`
- If the element is a content engagement link → `hs-track-content`
- If it is genuinely both → use `hs-track-cta` only. The CTA event carries sufficient signal, and the mutual exclusion on the content link trigger prevents double-firing.

Publish the Framer page after adding attributes.

### Step 2: Add Entry to Notion Content Tracking Registry

Open the [Content Tracking Registry](https://www.notion.example/{{NOTION_PAGE_ID}}) and add a row:

| Column | Value |
|--------|-------|
| Element ID | The exact `id` set in Step 1 |
| Content Title | Human-readable asset name |
| Content Type | guide / case_study / datasheet / pdf / template / webinar |
| Status | Staged |
| Date Added | Today |
| Notes | Any relevant context |

### Step 3: Update the GTM Content Metadata Lookup Variable

Open the `Content Metadata Lookup` variable in GTM. Add a new line to the registry object:

```javascript
'your-element-id': { title: 'Your Content Title', type: 'guide' },
```

Ensure the key exactly matches the HTML `id` attribute set in Framer.

If an entry with the same element ID already exists with different metadata, this is a renamed or replaced asset. Update the existing entry rather than adding a duplicate. Note the change in the Notion registry.

Save the variable. Do not publish yet.

### Step 4: QA and Publish

1. Open GTM Preview on the content hub page where the new element lives.
2. Click the new element.
3. In the GTM debug panel: confirm the correct tag fired (`HS - Content Link Click` or `HS - Content CTA Click`).
4. In the Variables tab for that click event: confirm `{{Content Metadata Lookup}}` resolves to the expected title and type.
5. Confirm `{{Attribution Params}}` returns UTM values (if you arrived with UTM parameters).
6. If everything resolves correctly: publish the GTM container with version note `Content registry update — added {element-id}`.
7. Update the Notion registry row Status from **Staged** to **Live**.

If `{{Content Metadata Lookup}}` returns `{ title: 'unknown', type: 'unknown' }`, the element ID in Framer does not match the key in the GTM registry. Check for typos, case mismatches, or a missing `id` attribute on the element.

---

## Section 5: Quarterly Registry Audit

Run this every quarter to validate active entries, flag stale ones, and keep the GTM variable clean.

### Step 1: Pull Event Occurrence Data

In HubSpot: navigate to **Data Management > Event Management**. For each event (`content_link_clicked` and `content_cta_clicked`), open the **Analyze** tab. Set the date range to the last 90 days. Note which element IDs have occurrences and which have zero.

### Step 2: Cross-Reference Against the Registry

Compare the HubSpot event data against the [Content Tracking Registry](https://www.notion.example/{{NOTION_PAGE_ID}}) in Notion (or the GTM variable directly, if the bootstrap has not been completed yet).

For each entry, classify it:

- **Active**: Has occurrences in the last 90 days. Leave as-is. Update the Last Verified date in Notion.
- **Inactive**: Zero occurrences, but the corresponding Framer page is still live. Leave the entry in place. Flag for content team review — the content may be low-traffic, not broken. Update status to Inactive in Notion.
- **Deprecated**: Zero occurrences AND the Framer page has been unpublished or the element removed. Mark as Deprecated in Notion and proceed to Step 3.

Also check for the reverse: events firing with `content_type` = `unknown` indicate elements that exist in Framer but are missing from the registry. Add these to the registry.

### Step 3: Prune the GTM Variable

Comment out deprecated entries in the GTM Content Metadata Lookup variable. Do not remove entries that are Inactive but not Deprecated — they may become active again.

Publish the GTM container with version note: `Quarterly registry audit — Q{N} {YEAR}`.

Update the Notion registry to reflect the final state.

### Step 4: Reconcile Notion and GTM

After the audit, confirm that every Live and Inactive entry in Notion has a corresponding uncommented entry in the GTM variable, and vice versa. There should be no entries in GTM that are not in Notion, and no Live entries in Notion that are missing from GTM.

---

## Section 6: QA Procedures

Run these checks after any change to the tracking system.

### UTM Persistence Test

1. Open GTM Preview. Enter the content hub URL with test parameters: `?utm_source=test&utm_medium=email&utm_campaign=qa-check`.
2. Open DevTools > Application > Session Storage > {{COMPANY_DOMAIN}}.
3. Confirm `hs_utm_source`, `hs_utm_medium`, `hs_utm_campaign` are present.
4. Navigate to a second content hub page. Confirm the values persist in sessionStorage.

### Content Link Click Test

If no live tracked elements are available for testing, simulate one:

1. In the GTM Preview tab, open DevTools > Elements.
2. Find any `<a>` tag and edit it to add `class="hs-track-content"` and `id="{an-id-in-your-registry}"`.
3. Click the element on the page.
4. In the GTM debug panel: confirm `HS - Content Link Click` fired.
5. In the Variables tab: confirm `{{Content Metadata Lookup}}` resolves to the expected title and type.
6. Confirm `{{Attribution Params}}` shows UTM values from Step 1.

### HubSpot End-to-End Confirmation

1. Arrive at the content hub by clicking a link in a tracked HubSpot marketing email. This establishes hutk cookie linkage to a known contact.
2. Click a tracked element.
3. In HubSpot: open the contact's record > Activity feed. The CBE should appear within 1-2 minutes with all properties populated.
4. If the event does not appear on the contact record but does appear in the Event Management Analyze tab: the hutk is not linked to the contact. Re-arrive via a tracked email link and retest.
5. If the event does not appear in the Analyze tab at all: the tag is not firing or the portal ID in the tag is wrong. Check the tag's `name` property string.

### Post-Change Verification Checklist

After any Part B deploy or quarterly audit, confirm:

- [ ] UTM parameters persist in sessionStorage across page navigation
- [ ] `{{Content Metadata Lookup}}` returns the correct title and type for all active element IDs
- [ ] `{{Attribution Params}}` returns UTM values on pages navigated to after landing with UTM params
- [ ] CBE appears on a known contact's HubSpot activity timeline within 2 minutes of a test click
- [ ] Content link tag does **not** fire on `hs-track-cta` elements
- [ ] CTA tag does **not** fire on plain `hs-track-content` elements
- [ ] PDF links have `target="_blank"`
- [ ] Notion registry and GTM variable are in sync

---

## Section 7: Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| CBE fires in GTM Preview but does not appear on the HubSpot contact record | Visitor is not a known contact (no hutk linkage). | Arrive via a tracked HubSpot email link to establish identity, then retest. Check the Analyze tab to confirm the event is reaching HubSpot at all. |
| CBE appears in Analyze tab but properties are null or `unknown` | Property schema mismatch between the GTM tag and HubSpot CBE definition. Or the element is missing an `id` attribute. | Confirm the property internal names in HubSpot exactly match those in the GTM tag. Confirm the element has an `id` attribute that matches a registry key. |
| Both content link and CTA tags fire on the same click | The element is missing the `hs-track-cta` class, or the content link trigger's exclusion condition was removed. | Add `hs-track-cta` to the element's class list. Verify that the `HS - Tracked Content Link` trigger excludes clicks where class contains `hs-track-cta`. |
| `{{Attribution Params}}` returns all null despite UTMs in the original URL | The UTM Capture tag and Attribution Params variable are using different sessionStorage prefixes, or the Capture tag fires after the click tag. | Confirm both use the `hs_` prefix. Check tag firing order in GTM Preview — the UTM Capture tag must fire on page load before any click tags. |
| New tab opens before the GTM click event fires (PDF race condition) | The PDF link is missing `target="_blank"`, causing the browser to navigate away before the event fires. | Add `target="_blank"` to the PDF link in Framer so it opens in a new tab. |
| Element ID contains uppercase letters and lookup returns `unknown` | Registry keys are case-sensitive. An uppercase ID does not match a lowercase key. | Convert all element IDs and registry keys to lowercase-with-hyphens. Update both Framer and the GTM variable. |
| GTM container publish blocked pending approval | Infrastructure gating on production tool changes. | Escalate to {{CEO_FIRST}} for approval before publishing. |
| Events firing with `content_type` = `unknown` for a known element | The element exists in Framer with the correct class and ID, but the ID is not in the GTM registry. | Add the missing entry to the Content Metadata Lookup variable following the process in Section 4. |
| HubSpot event property limit concern | The current schema uses 11 properties per event, well within HubSpot's 50-property limit. | No action needed unless future additions approach 50. If so, audit for low-signal properties to remove. |

---

## Quick Reference

| Item | Detail |
|------|--------|
| **Process** | Content Hub CBE Tracking — Maintenance & Registry |
| **Tools** | `~~web analytics` tag manager, `~~crm`, `~~cms`, `~~knowledge base` |
| **Add new element** | ~15 min: Framer attributes > Notion registry > GTM variable > QA > publish |
| **Quarterly audit** | ~30 min: HubSpot event data > cross-reference registry > prune GTM > reconcile |
| **Notion registry** | [Content Tracking Registry](https://www.notion.example/{{NOTION_PAGE_ID}}) — source of truth once bootstrapped |
| **GTM variable** | `Content Metadata Lookup` (deployed copy of the registry) |
| **Naming convention** | Lowercase, hyphen-separated: `{category}-{asset-slug}` |
| **Valid content types** | guide, case_study, datasheet, pdf, template, webinar |
| **Publish approval** | Confirm with {{CEO_FIRST}} before first container publish in a sprint cycle |
| **Related SOPs** | Lead Scoring Update SOP, GTM Container Governance SOP |

---

*Questions? Ping Scott or drop a note in #team-marketing or #revops.*
