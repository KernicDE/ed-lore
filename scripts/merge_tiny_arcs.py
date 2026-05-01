#!/usr/bin/env python3
"""Merge tiny arcs (≤3 articles) into parent arcs and delete arc files."""

import yaml
from pathlib import Path

ARCHIVE_DIR = Path("Archive")
ARCS_DIR = Path("Entities/Arcs")

# Mapping: tiny_arc_id -> parent_arc_id
MERGE_MAP = {
    "golconda": "jaques-station",
    "guardian-thargoid-war": "guardian-ancients",
    "banki-liberation": "federal-politics",
    "starship-one-disappearance": "halsey-presidency",
    "corporate-history": "federal-politics",
}


def main():
    # Reassign articles
    reassigned = 0
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

        arc_id = fm.get("arc_id")
        if arc_id in MERGE_MAP:
            fm["arc_id"] = MERGE_MAP[arc_id]
            new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_fm}---\n{parts[2]}"
            md_file.write_text(new_content, encoding="utf-8")
            reassigned += 1

    print(f"Reassigned {reassigned} articles to parent arcs")

    # Delete tiny arc files
    deleted = 0
    for tiny_arc in MERGE_MAP:
        arc_file = ARCS_DIR / f"{tiny_arc}.md"
        if arc_file.exists():
            arc_file.unlink()
            deleted += 1
            print(f"Deleted arc: {tiny_arc}")

    print(f"Deleted {deleted} tiny arc files")


if __name__ == "__main__":
    main()
