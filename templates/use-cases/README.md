# templates/use-cases/

Working copies of generated Use Case Library articles, held here **before** review.

`content-producer:use-case-builder` writes each article twice: the reviewable draft goes to
`state/pending/YYYY-MM-DD/content-producer-use-case-<slug>.md` (that is the copy chief-of-staff routes
for the editorial gate), and a working copy lands here as `use-case-<slug>.md` so the
article stays findable next to the template it was built from, without digging through
dated pending folders.

## What lives here

- `use-case-<slug>.md` — one per generated article, matching the slug in the pending
  draft's filename.
- Nothing else. No published articles, no evidence logs (those stay with the draft in
  `state/pending/`), no source material.

## Rules

- **These are drafts, not publications.** A human publishes to Notion from the
  approved pending draft. content-producer holds no Notion credentials and never posts.
- **The reviewed copy is the pending one.** If the two ever diverge, the copy in
  `state/pending/` is authoritative — it is the one the gate saw.
- **Unverified capability claims stay marked.** A working copy carries the same
  `[unverified]` / `[unverified — demo]` markers as the draft. Never strip them here
  to make the file read better.
- **Overwrite by slug.** Rebuilding the same use case replaces `use-case-<slug>.md`
  rather than accumulating suffixed variants.

## Naming note

`templates/use-case-article.md` reserves `templates/use-cases/<name>.md` as the path
for *additional article templates* if the library ever needs more than the single
canonical one. The `use-case-` filename prefix used here keeps generated articles from
colliding with that: anything named `use-case-<slug>.md` is a generated draft; a future
template would be named for its document type. Resolve the convention properly if and
when a second template is actually added.

Structure and the smoke-test hard rule: `templates/use-case-article.md`.
Procedure: `roster/content-producer/skills/use-case-builder.md`.
