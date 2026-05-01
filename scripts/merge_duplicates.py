#!/usr/bin/env python3
"""Merge obvious near-name duplicate entities by standardizing on canonical form."""

import yaml
from pathlib import Path
import re

ARCHIVE_DIR = Path("Archive")
ENTITIES_DIR = Path("Entities")

# Mapping: bad form -> canonical form
MERGES = {
    # factions - "The" prefix normalization
    "The Kalana Independents": "Kalana Independents",
    "The Hands of the Architects": "Hands of the Architects",
    "The Imperial Herald": "Imperial Herald",
    "The Alliance Tribune": "Alliance Tribune",
    "The Future of Segovan": "Future of Segovan",
    # factions - other
    "Radio Sidewinder News": "Radio Sidewinder",
    # persons
    "Volantyne": "Kay Volantyne",
    "Tyllerius Adle": "Tyllerius Adle III",
}


def slugify(text):
    if text is None:
        return ""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text).strip('_')
    return text


def process_articles():
    """Update article frontmatter to use canonical forms."""
    changed = 0
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
        
        modified = False
        for field in ["persons", "groups", "locations", "technologies"]:
            items = fm.get(field) or []
            new_items = []
            for item in items:
                if item in MERGES:
                    new_items.append(MERGES[item])
                    modified = True
                else:
                    new_items.append(item)
            if modified:
                fm[field] = new_items
        
        if modified:
            new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_fm}---\n{parts[2]}"
            md_file.write_text(new_content, encoding="utf-8")
            changed += 1
    
    return changed


def delete_obsolete_entities():
    """Delete entity files for obsolete forms."""
    deleted = 0
    for canonical, bad in [(v, k) for k, v in MERGES.items()]:
        # Determine entity type from canonical form
        # We need to find which type the bad entity is in
        for subdir in ENTITIES_DIR.iterdir():
            if not subdir.is_dir():
                continue
            bad_file = subdir / f"{slugify(bad)}.md"
            if bad_file.exists():
                bad_file.unlink()
                deleted += 1
                print(f"Deleted {subdir.name}/{bad_file.stem}")
                break
    return deleted


def rename_entity_files():
    """Rename entity files to canonical form if needed."""
    renamed = 0
    for canonical_name in set(MERGES.values()):
        canonical_slug = slugify(canonical_name)
        for subdir in ENTITIES_DIR.iterdir():
            if not subdir.is_dir():
                continue
            old_file = subdir / f"{canonical_slug}.md"
            if old_file.exists():
                # Already correct
                break
            # Check if there's an entity with a different slug but same name
            for f in subdir.glob("*.md"):
                content = f.read_text()
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    try:
                        fm = yaml.safe_load(parts[1])
                        if fm.get("name") == canonical_name:
                            # Rename file
                            new_file = subdir / f"{canonical_slug}.md"
                            f.rename(new_file)
                            renamed += 1
                            print(f"Renamed {f} -> {new_file}")
                            break
                    except Exception:
                        pass
    return renamed


def main():
    article_changes = process_articles()
    deleted = delete_obsolete_entities()
    renamed = rename_entity_files()
    
    print(f"\nModified {article_changes} articles")
    print(f"Deleted {deleted} obsolete entity files")
    print(f"Renamed {renamed} entity files")


if __name__ == "__main__":
    main()
