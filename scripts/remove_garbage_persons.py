#!/usr/bin/env python3
"""Bulk-remove garbage words from persons lists across all articles."""

import yaml
from pathlib import Path

ARCHIVE_DIR = Path("Archive")
ENTITIES_DIR = Path("Entities/person")

GARBAGE_WORDS = {"Its", "Located", "This"}


def main():
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

        persons = fm.get("persons") or []
        new_persons = [p for p in persons if p not in GARBAGE_WORDS]
        if len(new_persons) != len(persons):
            fm["persons"] = new_persons
            new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_fm}---\n{parts[2]}"
            md_file.write_text(new_content, encoding="utf-8")
            fixed += 1

    print(f"Fixed {fixed} articles by removing garbage persons")

    # Delete garbage entity files
    for word in GARBAGE_WORDS:
        slug = word.lower()
        f = ENTITIES_DIR / f"{slug}.md"
        if f.exists():
            f.unlink()
            print(f"Deleted entity: {f}")


if __name__ == "__main__":
    main()
