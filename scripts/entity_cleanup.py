#!/usr/bin/env python3
"""Entity cleanup: find duplicates, orphans, and near-name variants."""

import yaml
from pathlib import Path
from collections import defaultdict
import re

ARCHIVE_DIR = Path("Archive")
ENTITIES_DIR = Path("Entities")


def scan_entities():
    """Scan all entity files and return {type: {id: info}}."""
    entities = defaultdict(dict)
    for subdir in ENTITIES_DIR.iterdir():
        if not subdir.is_dir():
            continue
        entity_type = subdir.name
        for md_file in subdir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue
            try:
                fm = yaml.safe_load(parts[1])
                entity_id = md_file.stem
                entities[entity_type][entity_id] = {
                    "name": fm.get("name", entity_id),
                    "path": str(md_file),
                    "file": md_file,
                }
            except Exception:
                pass
    return entities


def scan_article_references():
    """Scan all articles and count entity references by type."""
    refs = defaultdict(lambda: defaultdict(int))
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
                    refs["person"][slugify(person)] += 1
            for group in fm.get("groups") or []:
                if group:
                    refs["faction"][slugify(group)] += 1
            for loc in fm.get("locations") or []:
                if loc:
                    refs["location"][slugify(loc)] += 1
            for tech in fm.get("technologies") or []:
                if tech:
                    refs["technology"][slugify(tech)] += 1
        except Exception:
            pass
    return refs


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text).strip('_')
    return text


def find_duplicates(entities):
    """Find near-name duplicates within each entity type."""
    duplicates = defaultdict(list)
    for entity_type, items in entities.items():
        names = {}
        for entity_id, info in items.items():
            name = info["name"].lower().strip()
            # Check exact name match
            if name in names:
                duplicates[entity_type].append((entity_id, names[name], name))
            else:
                names[name] = entity_id
            # Check near-match (e.g., "sirius corp" vs "sirius corporation")
            for existing_name, existing_id in list(names.items())[:-1]:
                if name != existing_name:
                    # Check if one is a substring of the other
                    if name in existing_name or existing_name in name:
                        if abs(len(name) - len(existing_name)) <= 5:
                            duplicates[entity_type].append((entity_id, existing_id, f"{name} ~ {existing_name}"))
                    # Check common suffix/prefix removal
                    name_clean = name.replace(" corporation", "").replace(" corp", "").replace(" inc", "").replace(" ltd", "")
                    existing_clean = existing_name.replace(" corporation", "").replace(" corp", "").replace(" inc", "").replace(" ltd", "")
                    if name_clean == existing_clean and name_clean != name and existing_clean != existing_name:
                        duplicates[entity_type].append((entity_id, existing_id, f"{name} ~ {existing_name} (clean: {name_clean})"))
    return duplicates


def find_orphans(entities, refs):
    """Find entities with zero references in articles."""
    orphans = defaultdict(list)
    for entity_type, items in entities.items():
        for entity_id, info in items.items():
            if refs[entity_type].get(entity_id, 0) == 0:
                orphans[entity_type].append((entity_id, info["name"]))
    return orphans


def main():
    print("Scanning entities...")
    entities = scan_entities()
    total = sum(len(v) for v in entities.values())
    print(f"Total entities: {total}")
    for t, items in sorted(entities.items()):
        print(f"  {t}: {len(items)}")

    print("\nScanning article references...")
    refs = scan_article_references()
    total_refs = sum(sum(v.values()) for v in refs.values())
    print(f"Total references: {total_refs}")

    print("\n--- FINDING DUPLICATES ---")
    duplicates = find_duplicates(entities)
    for entity_type, dups in sorted(duplicates.items()):
        if dups:
            print(f"\n{entity_type}: {len(dups)} potential duplicates")
            for dup in dups[:10]:
                print(f"  {dup[0]} <-> {dup[1]} ({dup[2]})")
            if len(dups) > 10:
                print(f"  ... and {len(dups) - 10} more")

    print("\n--- FINDING ORPHANS ---")
    orphans = find_orphans(entities, refs)
    total_orphans = sum(len(v) for v in orphans.values())
    print(f"Total orphans: {total_orphans}")
    for entity_type, items in sorted(orphans.items()):
        if items:
            print(f"\n{entity_type}: {len(items)} orphans")
            for oid, oname in items[:10]:
                print(f"  {oid} ({oname})")
            if len(items) > 10:
                print(f"  ... and {len(items) - 10} more")

    # Save orphans list for review
    with open("orphan_entities.txt", "w") as f:
        for entity_type, items in sorted(orphans.items()):
            for oid, oname in items:
                f.write(f"{entity_type}/{oid}\t{oname}\n")
    print(f"\nWrote {total_orphans} orphans to orphan_entities.txt")

    # Save duplicates list
    with open("duplicate_entities.txt", "w") as f:
        for entity_type, dups in sorted(duplicates.items()):
            for dup in dups:
                f.write(f"{entity_type}\t{dup[0]}\t{dup[1]}\t{dup[2]}\n")
    print(f"Wrote {sum(len(v) for v in duplicates.values())} duplicates to duplicate_entities.txt")


if __name__ == "__main__":
    main()
