#!/usr/bin/env python3
"""Audit arcs and UUIDs: find gaps, orphans, bad links."""

import yaml
from pathlib import Path
from collections import defaultdict
import re

ARCHIVE_DIR = Path("Archive")
ENTITIES_DIR = Path("Entities")


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    try:
        return yaml.safe_load(parts[1]), parts[2]
    except Exception:
        return None, text


def slugify(text):
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text


def audit_arcs():
    """Find arc issues: tiny arcs, gaps in multi-year arcs."""
    print("=" * 60)
    print("ARC AUDIT")
    print("=" * 60)

    arc_articles = defaultdict(list)
    for md_file in sorted(ARCHIVE_DIR.rglob("*.md")):
        fm, _ = parse_frontmatter(md_file)
        if not fm:
            continue
        arc_id = fm.get("arc_id")
        if arc_id:
            date = fm.get("date", "")
            if hasattr(date, 'strftime'):
                date = date.strftime("%Y-%m-%d")
            arc_articles[arc_id].append({
                "file": md_file,
                "date": date or "",
                "title": fm.get("title", ""),
                "uuid": fm.get("uuid", ""),
            })

    # Tiny arcs (<= 3 articles) — candidates for merging
    print("\n--- TINY ARCS (≤3 articles) — candidates for merging ---")
    for arc_id, articles in sorted(arc_articles.items(), key=lambda x: len(x[1])):
        if len(articles) <= 3:
            dates = [a["date"] for a in articles]
            print(f"  {arc_id}: {len(articles)} articles ({', '.join(dates)})")

    # Multi-year arcs with gaps > 6 months
    print("\n--- MULTI-YEAR ARCS WITH GAPS > 6 MONTHS ---")
    for arc_id, articles in sorted(arc_articles.items()):
        if len(articles) < 2:
            continue
        sorted_arts = sorted(articles, key=lambda a: a["date"])
        for i in range(1, len(sorted_arts)):
            d1 = sorted_arts[i-1]["date"]
            d2 = sorted_arts[i]["date"]
            if not d1 or not d2:
                continue
            from datetime import datetime
            try:
                dt1 = datetime.strptime(d1, "%Y-%m-%d")
                dt2 = datetime.strptime(d2, "%Y-%m-%d")
                gap_days = (dt2 - dt1).days
                if gap_days > 180:
                    print(f"  {arc_id}: {gap_days}d gap between {d1} and {d2}")
                    break
            except Exception:
                pass

    # Arcs spanning < 30 days (probably not real arcs)
    print("\n--- VERY SHORT ARCS (<30 days) ---")
    for arc_id, articles in arc_articles.items():
        if len(articles) < 2:
            continue
        from datetime import datetime
        try:
            dates = sorted([datetime.strptime(a["date"], "%Y-%m-%d") for a in articles if a["date"]])
            span = (dates[-1] - dates[0]).days
            if span < 30:
                print(f"  {arc_id}: {span} days span ({len(articles)} articles)")
        except Exception:
            pass


def audit_uuids():
    """Check UUID consistency and related_uuids bidirectional links."""
    print("\n" + "=" * 60)
    print("UUID AUDIT")
    print("=" * 60)

    articles = []
    for md_file in sorted(ARCHIVE_DIR.rglob("*.md")):
        fm, _ = parse_frontmatter(md_file)
        if not fm:
            continue
        date = fm.get("date", "")
        if hasattr(date, 'strftime'):
            date = date.strftime("%Y-%m-%d")
        articles.append({
            "file": md_file,
            "date": date or "",
            "title": fm.get("title", ""),
            "uuid": fm.get("uuid", ""),
            "related_uuids": fm.get("related_uuids") or [],
        })

    uuid_to_article = {a["uuid"]: a for a in articles if a["uuid"]}

    # Check UUIDv5 consistency: uuid should be derived from date + title
    print("\n--- UUID CONSISTENCY (sample) ---")
    import uuid as uuid_module
    mismatches = 0
    for a in articles[:100]:  # Sample first 100
        expected = str(uuid_module.uuid5(uuid_module.NAMESPACE_DNS, f"{a['date']}-{a['title'].lower()}"))
        if a["uuid"] != expected:
            mismatches += 1
    print(f"  {mismatches}/100 sampled articles have non-v5 UUIDs (may be intentional)")

    # Check bidirectional related_uuids
    print("\n--- MISSING BIDIRECTIONAL RELATED_UUIDS ---")
    missing_backlinks = 0
    for a in articles:
        for related_uuid in a["related_uuids"]:
            target = uuid_to_article.get(related_uuid)
            if not target:
                print(f"  {a['file']}: related_uuid {related_uuid} not found")
                continue
            if a["uuid"] not in (target["related_uuids"] or []):
                missing_backlinks += 1
    print(f"  Total missing bidirectional links: {missing_backlinks}")

    # Articles with no related_uuids at all
    print("\n--- ARTICLES WITH EMPTY RELATED_UUIDS ---")
    empty_count = sum(1 for a in articles if not a["related_uuids"])
    print(f"  {empty_count}/{len(articles)} articles have no related_uuids")


def audit_article_paths():
    """Check article file paths match their dates."""
    print("\n" + "=" * 60)
    print("ARTICLE PATH AUDIT")
    print("=" * 60)

    mismatches = 0
    for md_file in ARCHIVE_DIR.rglob("*.md"):
        fm, _ = parse_frontmatter(md_file)
        if not fm:
            continue
        date = fm.get("date", "")
        if hasattr(date, 'strftime'):
            date = date.strftime("%Y-%m-%d")
        expected_path = date.replace("-", "/") + "_" if date else None
        if expected_path and not str(md_file).replace(str(ARCHIVE_DIR) + "/", "").startswith(expected_path):
            mismatches += 1
            if mismatches <= 10:
                print(f"  {md_file}: date={date} but path doesn't match")

    print(f"  Total path/date mismatches: {mismatches}")


if __name__ == "__main__":
    audit_arcs()
    audit_uuids()
    audit_article_paths()
