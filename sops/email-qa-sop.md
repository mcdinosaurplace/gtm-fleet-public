# Email QA — Team SOP

**Version:** 1.0
**Owner:** Marketing / GTM Ops
**Applies to:** Anyone sending HubSpot marketing emails
**Tool:** {{COMPANY}} Marketing Plugin v1.5.0 → `/email-qa`

---

## What This Is

The `/email-qa` skill is a pre-send quality check for HubSpot marketing emails. It runs automated checks against subject line, preview text, body copy, links, image alt text, brand voice, and sender configuration, then returns a verdict with a list of any issues found. It works on both workflow emails and batch campaigns.

**Time to complete:** ~2-3 minutes per email

---

## Section 1: When to Run Email QA

Run `/email-qa` before every send. No exceptions.

This applies to:

- Batch campaign emails before scheduling
- Workflow emails before activating the workflow
- Re-engagement emails
- Nurture sequence emails
- Any one-off send from HubSpot

Build `/email-qa` into your send checklist as the last step before scheduling or activating. If you make edits after running QA, re-run before sending.

---

## Section 2: How to Submit an Email for QA

Three submission methods are supported:

**Option 1 — Paste HTML directly**
Copy the email HTML from HubSpot (via the source editor or export) and paste it into Co-Work. This works for any email regardless of publish state.

**Option 2 — HubSpot email ID**
Provide the numeric email asset ID from HubSpot. Find it in the URL when editing the email: `app.hubspot.com/email/{portal-id}/edit/{email-id}/...`. Submit as: `email ID: 12345678`.

**Option 3 — Preview link**
Generate a preview link in HubSpot (Actions > Preview > Copy link) and paste the `hs-sites.com` URL into Co-Work.

When submitting, include context alongside the email:

- Campaign name
- Intended audience (list or segment name)
- Scheduled send date

This context helps the skill assess brand voice and audience fit in addition to technical checks.

---

## Section 3: Reading the QA Report

The report returns results in the following sections:

**Subject Line Check**
Flags spelling and grammar errors, reports character count against the 50-character recommended limit, notes tone issues, and identifies common spam trigger words.

**Preview Text Check**
Confirms preview text is present, checks that it is not a repeat of the subject line, and flags awkward truncation based on typical inbox character limits (85-100 characters).

**Body Copy Check**
Flags spelling and grammar errors, identifies any competitor names in the copy, flags fear-based language, and checks that product names are correctly cased per brand guidelines.

**Link Check Table**
Lists every link in the email with its destination URL, HTTP status code from a live check, and UTM parameter status. A link is flagged if it returns a non-200 status or is missing `utm_source`, `utm_medium`, or `utm_campaign`.

**Image Alt Text Check**
Lists every image and reports whether descriptive alt text is present. Empty or generic alt text (e.g., `image`, `photo`) is flagged.

**Brand Voice Check**
Assesses the copy against {{COMPANY}} brand guidelines: tone, clarity, avoidance of filler phrases, and messaging consistency.

**From Name and Reply-To Check**
Confirms the from name matches approved sender profiles and that the reply-to address is a monitored inbox.

**Verdict**

| Verdict | Meaning |
|---------|---------|
| Ready to Send | All checks pass. Schedule in HubSpot. |
| Ready to Send with Fixes | Minor issues found. Address the listed items, then schedule. |
| Do Not Send | Blocking issues found. Resolve before scheduling. |

---

## Section 4: Common Failures and Fixes

| Failure | Fix |
|---------|-----|
| Broken link (non-200 HTTP status) | Update or remove the link in HubSpot. Re-run QA after saving. |
| Missing UTM parameters | Add `utm_source`, `utm_medium`, and `utm_campaign` to all links. Use HubSpot's URL builder or update the link directly in the email editor. |
| Missing preview text | Add preview text in HubSpot email settings (the dedicated preview text field, not the email body). Avoid adding it as hidden text at the top of the body. |
| Fear-based language | Rewrite the flagged copy per brand guidelines. Fear-based language includes urgency framing around negative outcomes (e.g., "Don't miss out or you'll fall behind"). |
| Wrong product name casing | Correct the casing and re-run. Check `context/brand-voice.yaml` if you are unsure of the correct form. |
| Subject line over 50 characters | Tighten the subject line. The check is advisory, not blocking, but subjects over 60 characters risk truncation in most clients. |
| Missing image alt text | Add descriptive alt text to each image in HubSpot's image editor. Alt text should describe the image content, not the file name. |
| Unrecognized from name | Confirm the sender profile exists in HubSpot Settings > Marketing > Email > Sending Domains. Use only approved from names. |

---

## Section 5: After QA

**Ready to Send**
Schedule the email in HubSpot. No further action needed.

**Ready to Send with Fixes**
Make the listed changes in HubSpot. Re-run `/email-qa` after saving changes. Do not schedule until you receive a clean verdict.

**Do Not Send**
Do not schedule. Resolve all blocking issues. If the issue is ambiguous or requires a judgment call (e.g., whether a phrase qualifies as fear-based language), get a second opinion from a teammate before re-running. Once blocking issues are resolved, re-run QA and confirm you receive "Ready to Send" or "Ready to Send with Fixes" before scheduling.

---

## Section 6: Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Skill cannot access a link | The destination URL is behind a VPN, requires authentication, or is geo-restricted. The live HTTP check cannot reach it. | Test the link manually in a browser. If it loads correctly, note it in chat and the skill will mark it as manually verified. |
| HubSpot email ID not found | The ID provided is a campaign ID or folder ID, not the email asset ID. | Open the email in HubSpot's email editor. The email asset ID is the numeric segment in the URL at `edit/{email-id}`. |
| Preview link expired or returns an error | HubSpot preview links expire after a short window. | Generate a fresh preview link in HubSpot (Actions > Preview > Copy link) and resubmit. |
| Link check table is incomplete | The HTML contains dynamically inserted links (e.g., personalization tokens in href attributes) that cannot be resolved statically. | Submit the rendered preview HTML rather than the raw template source. Alternatively, list the dynamic link destinations in chat for manual verification. |
| Brand voice check flags copy that is approved | The skill flagged a phrase that was intentionally approved for this campaign. | Note the exception in chat. The skill will log it and exclude it from the verdict. Keep a record in the campaign brief. |

---

## Quick Reference

| Item | Detail |
|------|--------|
| **Command** | `/email-qa` |
| **Plugin version** | {{COMPANY}} Marketing Plugin v1.5.0 |
| **Where to run** | Claude Co-Work (Path A) |
| **Submission methods** | Paste HTML, HubSpot email ID, or hs-sites.com preview link |
| **Applies to** | Batch campaigns, workflow emails, re-engagement, nurture sequences |
| **Verdict types** | Ready to Send / Ready to Send with Fixes / Do Not Send |
| **What gets checked** | Subject line, preview text, body copy, links (live HTTP), image alt text, brand voice, from name and reply-to |
| **Send gate rule** | Do not schedule any email without a passing QA verdict |

---

*Questions? Ping Scott or drop a note in #marketing-ops.*
