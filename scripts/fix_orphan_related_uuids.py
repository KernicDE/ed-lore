#!/usr/bin/env python3
"""Remove related_uuids that point to non-existent articles."""

import yaml
from pathlib import Path

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
    # Collect all valid UUIDs
    valid_uuids = set()
    for md_file in ARCHIVE_DIR.rglob("*.md"):
        fm, _ = parse_frontmatter(md_file)
        if fm:
            u = fm.get("uuid")
            if u:
                valid_uuids.add(u)

    fixed = 0
    for md_file in ARCHIVE_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1])
        except Exception:
            continue

        related = fm.get("related_uuids") or []
        if not related:
            continue

        new_related = [r for r in related if r in valid_uuids]
        if len(new_related) != len(related):
            fm["related_uuids"] = new_related if new_related else []
            new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_fm}---\n{parts[2]}"
            md_file.write_text(new_content, encoding="utf-8")
            fixed += 1

    print(f"Fixed {fixed} articles by removing invalid related_uuids")


if __name__ == "__main__":
    main()
