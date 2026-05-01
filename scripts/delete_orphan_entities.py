#!/usr/bin/env python3
"""Delete orphan entities with zero references in articles. Keep arcs referenced via arc_id."""

import yaml
from pathlib import Path
from collections import defaultdict
import re

ARCHIVE_DIR = Path("Archive")
ENTITIES_DIR = Path("Entities")


def slugify(text):
    if text is None:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text


def main():
    # Count references from articles
    refs = defaultdict(int)
    arc_refs = defaultdict(int)
    
    for md_file in ARCHIVE_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1])
            for person in fm.get("persons") or []:
                if person:
                    refs[("person", slugify(person))] += 1
            for group in fm.get("groups") or []:
                if group:
                    refs[("faction", slugify(group))] += 1
            for loc in fm.get("locations") or []:
                if loc:
                    refs[("location", slugify(loc))] += 1
            for tech in fm.get("technologies") or []:
                if tech:
                    refs[("technology", slugify(tech))] += 1
            arc_id = fm.get("arc_id")
            if arc_id:
                arc_refs[arc_id] += 1
        except Exception:
            pass
    
    print(f"Total entity references: {sum(refs.values())}")
    print(f"Total arc references: {sum(arc_refs.values())}")
    
    # Check each entity file
    deleted = 0
    kept = 0
    arc_kept = 0
    
    for subdir in ENTITIES_DIR.iterdir():
        if not subdir.is_dir():
            continue
        entity_type = subdir.name
        for md_file in subdir.glob("*.md"):
            entity_id = md_file.stem
            
            if entity_type == "Arcs":
                # Keep arcs referenced by arc_id
                if arc_refs.get(entity_id, 0) > 0:
                    kept += 1
                    arc_kept += 1
                else:
                    # Unreferenced arc - check if it has articles or is meaningful
                    content = md_file.read_text(encoding="utf-8")
                    parts = content.split("---", 2)
                    if len(parts) >= 3:
                        try:
                            fm = yaml.safe_load(parts[1])
                            # Keep arcs with descriptions or related articles
                            if fm.get("description") or fm.get("related_article_uuids"):
                                kept += 1
                                arc_kept += 1
                                continue
                        except Exception:
                            pass
                    md_file.unlink()
                    deleted += 1
            else:
                key = (entity_type, entity_id)
                if refs.get(key, 0) > 0:
                    kept += 1
                else:
                    md_file.unlink()
                    deleted += 1
    
    print(f"\nDeleted {deleted} orphan entities")
    print(f"Kept {kept} referenced entities")
    print(f"  Including {arc_kept} arcs")


if __name__ == "__main__":
    main()
