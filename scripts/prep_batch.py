#!/usr/bin/env python3
"""
prep_batch.py — Prepare a batch of GalNet articles for AI analysis.

Reads raw articles, cleans GitHub artifacts, and outputs a compact format
suitable for batch review. The AI can then analyse all articles at once
and decide which need deep enrichment vs light tagging.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
GALNET_DIR = BASE_DIR / "GalNet"


def clean_body(body: str) -> str:
    """Remove GitHub artifact lines (* prefix, /date/ lines)."""
    lines = body.splitlines()
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("* ") and len(stripped) > 2:
            cleaned.append(stripped[2:])
        elif stripped.startswith("/") and stripped.endswith("/") and any(c.isdigit() for c in stripped):
            continue
        else:
            cleaned.append(line)
    return "\n".join(cleaned).strip()


def parse_article(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        fm = yaml.safe_load(parts[1].strip()) or {}
    except yaml.YAMLError:
        return None
    body = clean_body(parts[2].strip())
    return {
        "uuid": fm.get("uuid"),
        "title": fm.get("title"),
        "date": fm.get("ed_date"),
        "source": fm.get("source"),
        "slug": fm.get("slug"),
        "body": body,
        "path": str(path.relative_to(BASE_DIR)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", required=True, help="Elite year to process (e.g. 3301)")
    parser.add_argument("--offset", type=int, default=0, help="Skip N articles")
    parser.add_argument("--limit", type=int, default=50, help="Process N articles")
    args = parser.parse_args()

    real_year = int(args.year) - 1286
    pattern = f"{real_year}-{args.year}"
    source_dir = GALNET_DIR / pattern
    if not source_dir.exists():
        print(f"Directory not found: {source_dir}", file=sys.stderr)
        return 1

    all_files = sorted(source_dir.glob("*.md"))
    batch = all_files[args.offset : args.offset + args.limit]

    print(f"# BATCH: {args.year} | offset={args.offset} limit={args.limit} | {len(batch)} articles\n")

    for i, path in enumerate(batch, 1):
        art = parse_article(path)
        if not art:
            continue
        print(f"--- ARTICLE {i} ---")
        print(f"DATE: {art['date']}")
        print(f"TITLE: {art['title']}")
        print(f"SLUG: {art['slug']}")
        print(f"SOURCE: {art['source']}")
        print(f"BODY:\n{art['body']}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
