#!/usr/bin/env python3
"""Convert a Google Search Console "Performance on Search" xlsx export into a
page,query CSV for scripts/blog_inventory_crawl.py --gsc-csv.

GSC's standard export puts Queries and Pages on SEPARATE sheets with NO join — it
does not record which queries each page ranks for. This tool reconstructs an
approximate per-page query list by assigning each top query to the single blog
page whose URL slug best overlaps the query's tokens (default: >=2 shared
non-stopword tokens). It is a TOPICAL HEURISTIC, not true per-page GSC
attribution — interim dedup signal until the GSC API (scripts/gsc_pull.py) is
permissioned, at which point real per-page queries replace this.

Usage:
  python scripts/gsc_xlsx_to_pagequeries.py --xlsx <export.xlsx> --out <csv>
      [--all-pages] [--min-overlap 2]
"""

import argparse
import csv
import re

import openpyxl

# Common words that shouldn't drive a query->page match on their own.
STOP = {"the", "a", "an", "to", "of", "for", "and", "or", "in", "on", "is", "vs",
        "how", "what", "your", "you", "with", "do", "does", "can", "are", "be",
        "at", "from", "by", "this", "it", "as", "when", "vs.", "&"}


def tokens(s):
    # GSC cells may arrive as float/int (e.g. a numeric query like 1099) — coerce.
    return {t for t in re.split(r"[^a-z0-9]+", str(s if s is not None else "").lower())
            if t and t not in STOP and len(t) > 1}


def slug_tokens(url):
    slug = url.rstrip("/").rsplit("/", 1)[-1]
    return tokens(slug.replace("-", " "))


def read_sheet(wb, name):
    rows = list(wb[name].iter_rows(values_only=True))
    return rows[1:]  # drop header row


def main():
    ap = argparse.ArgumentParser(description="GSC xlsx -> page,query CSV (heuristic join).")
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--all-pages", action="store_true", help="Include non-/blog/ pages too")
    ap.add_argument("--min-overlap", type=int, default=2, help="Min shared tokens to assign")
    args = ap.parse_args()

    wb = openpyxl.load_workbook(args.xlsx, read_only=True, data_only=True)
    pages = [(r[0], r[2]) for r in read_sheet(wb, "Pages") if r and r[0]]      # (url, impressions)
    queries = [(r[0], r[2] or 0) for r in read_sheet(wb, "Queries") if r and r[0]]  # (query, impressions)

    page_tok = {url: slug_tokens(url) for url, _ in pages
                if args.all_pages or "/blog/" in url}

    # Assign each query to its single best-matching page (argmax token overlap).
    assigned = {}
    for q, imp in queries:
        qt = tokens(q)
        best, best_ov = None, 0
        for url, pt in page_tok.items():
            ov = len(qt & pt)
            if ov > best_ov:
                best, best_ov = url, ov
        if best and best_ov >= args.min_overlap:
            assigned.setdefault(best, []).append((imp, q))

    with open(args.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["page", "query"])
        for url in sorted(assigned):
            for imp, q in sorted(assigned[url], reverse=True):
                w.writerow([url, q])

    pairs = sum(len(v) for v in assigned.values())
    print(f"Blog pages in export: {len(page_tok)} | "
          f"queries assigned: {pairs} across {len(assigned)} pages "
          f"(min-overlap={args.min_overlap})")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
