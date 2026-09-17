#!/usr/bin/env python3
"""Seed/refresh the content_inventory table from GTM Fleet's published blog.

Step 4 of the content engine. Crawls
orrery.example/blog via sitemap.xml, extracts each post's title/excerpt/headings/dates
(preferring the Article JSON-LD the Framer template emits), enriches with search
queries via a degradation ladder, and upserts content_inventory. content-researcher's
topic-synthesizer reads the table to classify candidate topics net-new / refresh
/ duplicate. Owned by the content-researcher:content-inventory skill.

Stdlib only (urllib + xml.etree + json) to match the repo's script conventions.

Source adapters (content_inventory.source):
  crawl  — this script (the seed path)
  framer — scaffolded seam for a future Framer MCP/API connector (stub below)
  content-producer   — appended by content-producer's publish-package on publish

Query enrichment ladder (content_inventory.query_source), best available wins:
  gsc      — Search Console API via scripts/gsc_pull.py   (not permissioned yet)
  gsc_csv  — manual GSC export passed with --gsc-csv       (works today)
  ahrefs   — Ahrefs/SimilarWeb MCP proxy                   (needs auth; stub)
  none     — no query data; matcher falls back to title/topic overlap

Usage:
  python scripts/blog_inventory_crawl.py [--db PATH] [--base-url https://orrery.example]
      [--sitemap URL] [--gsc-csv PATH] [--limit N] [--dry-run]
"""

import argparse
import html
import json
import re
import sqlite3
import sys
import time
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

import sys as _sys
_sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import fleet_paths  # noqa: E402

DEFAULT_DB = fleet_paths.DB_PATH
USER_AGENT = "GTM FleetContentInventory/1.0 (+marketing agent; respects robots)"
ARTICLE_TYPES = {"Article", "BlogPosting", "NewsArticle", "TechArticle"}
# Nav/CTA headings the Framer template repeats on every post — not content structure.
_BOILERPLATE_HEADINGS = {"table of contents", "want product news & updates?",
                         "continue reading", "related articles"}


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def discover_blog_urls(base_url, sitemap_url):
    """Return blog post URLs from the sitemap (follows one level of sitemap index)."""
    sitemap_url = sitemap_url or base_url.rstrip("/") + "/sitemap.xml"
    seen, queue, out = set(), [sitemap_url], []
    while queue:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(fetch(sm))
        except Exception as e:  # network / parse — skip this sitemap, keep going
            print(f"  ! sitemap {sm}: {e}", file=sys.stderr)
            continue
        ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
        # Nested sitemap index → enqueue children.
        for loc in root.iterfind(f".//{ns}sitemap/{ns}loc"):
            if loc.text:
                queue.append(loc.text.strip())
        for loc in root.iterfind(f".//{ns}url/{ns}loc"):
            u = (loc.text or "").strip()
            if "/blog/" in u and not u.rstrip("/").endswith("/blog"):
                out.append(u)
    return sorted(set(out))


class _Headings(HTMLParser):
    def __init__(self):
        super().__init__()
        self._tag = None
        self._buf = []
        self.headings = []

    def handle_starttag(self, tag, attrs):
        if tag in ("h2", "h3"):
            self._tag = tag
            self._buf = []

    def handle_endtag(self, tag):
        if tag == self._tag:
            text = " ".join("".join(self._buf).split())
            if text:
                self.headings.append(text)
            self._tag = None

    def handle_data(self, data):
        if self._tag:
            self._buf.append(data)


def _jsonld_blocks(markup):
    blocks = []
    for m in re.finditer(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        markup, re.DOTALL | re.IGNORECASE):
        try:
            blocks.append(json.loads(m.group(1).strip()))
        except Exception:
            continue
    return blocks


def _find_article(blocks):
    """Locate an Article-type node across plain objects, lists, and @graph."""
    stack = list(blocks)
    while stack:
        node = stack.pop()
        if isinstance(node, list):
            stack.extend(node)
        elif isinstance(node, dict):
            if "@graph" in node:
                stack.extend(node["@graph"] if isinstance(node["@graph"], list) else [node["@graph"]])
            t = node.get("@type")
            types = set(t) if isinstance(t, list) else {t}
            if types & ARTICLE_TYPES:
                return node
    return None


def _meta(markup, *names):
    for name in names:
        # Backreference \1 anchors the closing quote to the opening one, so an
        # apostrophe inside a single-quoted content value doesn't end the match.
        m = re.search(
            r'<meta[^>]+(?:name|property)=["\']' + re.escape(name) + r'["\'][^>]+content=(["\'])(.*?)\1',
            markup, re.IGNORECASE)
        if m:
            return html.unescape(m.group(2)).strip()
    return None


def _clean_title(t):
    """Unescape entities and strip the site-suffix (' - GTM Fleet | ...')."""
    if not t:
        return None
    t = html.unescape(t).strip()
    t = re.sub(r'\s*[-|]\s*GTM Fleet\s*\|.*$', '', t).strip()
    return t or None


def extract_post(url, markup):
    article = _find_article(_jsonld_blocks(markup)) or {}
    raw_title = article.get("headline") or article.get("name")
    if not raw_title:
        m = re.search(r"<title>(.*?)</title>", markup, re.DOTALL | re.IGNORECASE)
        raw_title = m.group(1) if m else None
    title = _clean_title(raw_title)
    excerpt = article.get("description") or _meta(markup, "description", "og:description")
    if excerpt:
        excerpt = html.unescape(excerpt).strip()
    published = article.get("datePublished") or _meta(markup, "article:published_time")
    modified = article.get("dateModified") or _meta(markup, "article:modified_time")
    parser = _Headings()
    try:
        parser.feed(markup)
    except Exception:
        pass
    tl = (title or "").strip().lower()
    headings = [h for h in parser.headings
                if h.strip().lower() not in _BOILERPLATE_HEADINGS and h.strip().lower() != tl]
    section = article.get("articleSection")
    return {
        "url": url,
        "slug": url.rstrip("/").rsplit("/", 1)[-1],
        "title": title,
        "excerpt": excerpt,
        "headings": json.dumps(headings[:25]),
        "primary_topic": html.unescape(section).strip() if section else None,
        "published_at": published,
        "last_modified": modified,
    }


def load_gsc_csv(path):
    """Map page URL -> [queries] from a manual GSC export (fallback A).

    Tolerant of column naming: any header containing 'page'/'url' is the page,
    'quer' is the query. A pages-only export still marks URLs as indexed.
    """
    import csv
    mapping = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        cols = {c.lower(): c for c in (reader.fieldnames or [])}
        page_col = next((cols[c] for c in cols if "page" in c or "url" in c or "landing" in c), None)
        query_col = next((cols[c] for c in cols if "quer" in c), None)
        for row in reader:
            page = (row.get(page_col) or "").strip() if page_col else ""
            if not page:
                continue
            q = (row.get(query_col) or "").strip() if query_col else ""
            mapping.setdefault(page, [])
            if q:
                mapping[page].append(q)
    return mapping


def framer_adapter(base_url):
    """Scaffolded seam for a future Framer MCP/API connector. No-op until wired."""
    print("  · framer adapter: no connector configured — skipping (seam only)")
    return []


def enrich(rows, gsc_csv):
    if gsc_csv:
        gsc = load_gsc_csv(gsc_csv)
        for r in rows:
            queries = gsc.get(r["url"], [])
            r["top_queries"] = json.dumps(queries[:20])
            r["query_source"] = "gsc_csv" if r["url"] in gsc else "none"
    else:
        for r in rows:
            r["top_queries"] = json.dumps([])
            r["query_source"] = "none"
    return rows


UPSERT = """
INSERT INTO content_inventory
  (url, slug, title, excerpt, headings, primary_topic, top_queries, query_source,
   published_at, last_modified, source, status, last_seen_at, created_at)
VALUES
  (:url, :slug, :title, :excerpt, :headings, :primary_topic, :top_queries, :query_source,
   :published_at, :last_modified, 'crawl', 'live', :now, :now)
ON CONFLICT(url) DO UPDATE SET
  slug=excluded.slug, title=excluded.title, excerpt=excluded.excerpt,
  headings=excluded.headings, primary_topic=excluded.primary_topic,
  top_queries=CASE WHEN excluded.query_source != 'none' THEN excluded.top_queries
                   ELSE content_inventory.top_queries END,
  query_source=CASE WHEN excluded.query_source != 'none' THEN excluded.query_source
                    ELSE content_inventory.query_source END,
  published_at=excluded.published_at, last_modified=excluded.last_modified,
  status='live', last_seen_at=excluded.last_seen_at;
"""


def upsert(db_path, rows, run_ts):
    conn = sqlite3.connect(db_path)
    try:
        for r in rows:
            conn.execute(UPSERT, {**r, "now": run_ts})
        # Crawl-sourced rows not seen this run → stale (post likely unpublished/moved).
        stale = conn.execute(
            "UPDATE content_inventory SET status='stale' "
            "WHERE source='crawl' AND status='live' AND last_seen_at < ?",
            (run_ts,)).rowcount
        conn.commit()
        return stale
    finally:
        conn.close()


def main():
    ap = argparse.ArgumentParser(description="Crawl orrery.example/blog into content_inventory.")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--base-url", default="https://orrery.example")
    ap.add_argument("--sitemap", default=None, help="Override sitemap URL")
    ap.add_argument("--gsc-csv", default=None, help="Manual GSC export for query enrichment")
    ap.add_argument("--limit", type=int, default=0, help="Cap posts fetched (0 = all)")
    ap.add_argument("--dry-run", action="store_true", help="Print, do not write the DB")
    args = ap.parse_args()

    run_ts = _now()
    print(f"Discovering blog URLs from {args.base_url} ...")
    urls = discover_blog_urls(args.base_url, args.sitemap)
    if args.limit:
        urls = urls[:args.limit]
    print(f"Found {len(urls)} blog post URLs.")

    rows = []
    for i, url in enumerate(urls, 1):
        try:
            rows.append(extract_post(url, fetch(url)))
            print(f"  [{i}/{len(urls)}] {url}")
        except Exception as e:
            print(f"  ! [{i}/{len(urls)}] {url}: {e}", file=sys.stderr)
        time.sleep(0.5)  # be polite

    framer_adapter(args.base_url)  # seam; currently a no-op
    rows = enrich(rows, args.gsc_csv)

    if args.dry_run:
        print(f"\n--dry-run: {len(rows)} rows extracted (not written):")
        print(json.dumps(rows[:3], indent=2))
        return

    stale = upsert(args.db, rows, run_ts)
    print(f"\nUpserted {len(rows)} rows into content_inventory. Flagged {stale} stale.")


if __name__ == "__main__":
    main()
