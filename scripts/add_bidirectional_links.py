#!/usr/bin/env python3
"""Add bidirectional related_uuids for articles in same arc or adjacent dates."""

import yaml
from pathlib import Path
from collections import defaultdict

ARCHIVE_DIR = Path("Archive")


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


def main():
    # Load all articles
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
            "uuid": fm.get("uuid", ""),
            "date": date,
            "arc_id": fm.get("arc_id"),
            "related_uuids": set(fm.get("related_uuids") or []),
        })

    # Index by UUID
    uuid_to_article = {a["uuid"]: a for a in articles if a["uuid"]}

    # Group by arc
    arc_groups = defaultdict(list)
    for a in articles:
        if a["arc_id"]:
            arc_groups[a["arc_id"]].append(a)

    added = 0
    for arc_id, group in arc_groups.items():
        # Sort by date
        group.sort(key=lambda a: a["date"])
        for i, a in enumerate(group):
            # Link to adjacent articles in same arc (prev/next)
            neighbors = []
            if i > 0:
                neighbors.append(group[i-1]["uuid"])
            if i < len(group) - 1:
                neighbors.append(group[i+1]["uuid"])

            for neighbor_uuid in neighbors:
                if neighbor_uuid not in a["related_uuids"]:
                    a["related_uuids"].add(neighbor_uuid)
                    added += 1
                # Also add backlink
                neighbor = uuid_to_article.get(neighbor_uuid)
                if neighbor and a["uuid"] not in neighbor["related_uuids"]:
                    neighbor["related_uuids"].add(a["uuid"])
                    added += 1

    # Write back changes
    written = 0
    for a in articles:
        if not a["related_uuids"]:
            continue
        content = a["file"].read_text(encoding="utf-8")
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1])
        except Exception:
            continue

        existing = set(fm.get("related_uuids") or [])
        new_related = sorted(a["related_uuids"])
        if set(new_related) != existing:
            fm["related_uuids"] = new_related
            new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_fm}---\n{parts[2]}"
            a["file"].write_text(new_content, encoding="utf-8")
            written += 1

    print(f"Added {added} bidirectional links")
    print(f"Wrote changes to {written} articles")


if __name__ == "__main__":
    main()
