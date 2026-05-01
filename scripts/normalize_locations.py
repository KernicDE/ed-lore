#!/usr/bin/env python3
"""Normalize location name variants across articles and entity files."""

import yaml
from pathlib import Path
import re

ARCHIVE_DIR = Path("Archive")
ENTITIES_DIR = Path("Entities/location")

# Mapping: canonical form -> list of variants to replace
NORMALIZATIONS = {
    "Col 70 Sector": ["Col 70 sector", "COL 70 sector"],
    "George Lucas Station": ["George Lucas station"],
    "Iren's Dock": ["Irens Dock"],
    "Levi-Montalcini Dock": ["Levi Montalcini Dock"],
    "Merope 5 C": ["Merope 5c"],
    "Pleiades Sector IH-V c2-16": ["Pleiades Sector IH-V C2-16"],
    "Pleiades Sector IH-V c2-5": ["Pleiades Sector IH-V C2-5"],
    "PRE Logistics Support Gamma": ["Pre Logistics Support Gamma"],
    "Scutum-Centaurus Arm": ["Scutum-Centaurus arm"],
    "Smith Port": ["Smithport"],
    "Synuefai EB-R c7-5": ["Synuefai EB-R C7-5"],
    "T'iensei": ["T\u2019iensei", "T'iensei"],  # smart quote vs straight quote
    "T Tauri": ["T-Tauri"],
    "Wregoe TC-X b29-0": ["Wregoe TC-X B29-0"],
}

# Build reverse lookup: variant -> canonical
VARIANT_TO_CANONICAL = {}
for canonical, variants in NORMALIZATIONS.items():
    for variant in variants:
        VARIANT_TO_CANONICAL[variant] = canonical


def normalize_in_text(text):
    """Replace all location variants in text with canonical forms."""
    for variant, canonical in VARIANT_TO_CANONICAL.items():
        text = text.replace(variant, canonical)
    return text


def process_article(md_file):
    """Normalize locations in an article's frontmatter and body."""
    content = md_file.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return False
    parts = content.split("---", 2)
    if len(parts) < 3:
        return False
    
    try:
        fm = yaml.safe_load(parts[1])
    except Exception:
        return False
    
    changed = False
    
    # Normalize locations list
    locations = fm.get("locations") or []
    new_locations = []
    for loc in locations:
        if loc in VARIANT_TO_CANONICAL:
            new_locations.append(VARIANT_TO_CANONICAL[loc])
            changed = True
        else:
            new_locations.append(loc)
    
    if changed:
        fm["locations"] = new_locations
        # Rebuild frontmatter
        new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
        new_content = f"---\n{new_fm}---\n{parts[2]}"
        md_file.write_text(new_content, encoding="utf-8")
    
    # Also normalize body text
    body = parts[2]
    new_body = normalize_in_text(body)
    if new_body != body:
        if not changed:
            # Need to rewrite with original frontmatter
            new_content = f"---\n{parts[1]}---\n{new_body}"
            md_file.write_text(new_content, encoding="utf-8")
        else:
            # Already rewrote, now fix body
            content = md_file.read_text(encoding="utf-8")
            parts2 = content.split("---", 2)
            new_content = f"---\n{parts2[1]}---\n{new_body}"
            md_file.write_text(new_content, encoding="utf-8")
        changed = True
    
    return changed


def process_entity(md_file):
    """Normalize entity name if needed."""
    content = md_file.read_text(encoding="utf-8")
    parts = content.split("---", 2)
    if len(parts) < 3:
        return False
    
    try:
        fm = yaml.safe_load(parts[1])
    except Exception:
        return False
    
    name = fm.get("name", "")
    if name in VARIANT_TO_CANONICAL:
        fm["name"] = VARIANT_TO_CANONICAL[name]
        new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
        new_content = f"---\n{new_fm}---\n{parts[2]}"
        md_file.write_text(new_content, encoding="utf-8")
        return True
    
    # Also normalize body
    body = parts[2]
    new_body = normalize_in_text(body)
    if new_body != body:
        new_content = f"---\n{parts[1]}---\n{new_body}"
        md_file.write_text(new_content, encoding="utf-8")
        return True
    
    return False


def main():
    article_changes = 0
    entity_changes = 0
    
    for md_file in ARCHIVE_DIR.rglob("*.md"):
        if process_article(md_file):
            article_changes += 1
    
    for md_file in ENTITIES_DIR.glob("*.md"):
        if process_entity(md_file):
            entity_changes += 1
    
    print(f"Modified {article_changes} articles")
    print(f"Modified {entity_changes} entity files")


if __name__ == "__main__":
    main()
