#!/usr/bin/env python3
"""Add Inara/EDSM links to entity markdown files.

Only location entities get Inara links (starsystem search).
Faction and person Inara links are unreliable — minorfaction search returns
empty results for non-game factions, and cmdr-search only finds registered
player CMDRs (not NPCs). These have been removed.
"""

import yaml
from pathlib import Path
from urllib.parse import quote

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


def enrich_locations():
    """Add Inara starsystem search URLs to location entities."""
    subdir = ENTITIES_DIR / "location"
    if not subdir.exists():
        return 0

    updated = 0
    for md_file in subdir.glob("*.md"):
        fm, body = parse_frontmatter(md_file)
        if not fm:
            continue

        name = fm.get("name", md_file.stem.replace("-", " ").title())
        encoded = quote(name)
        url = f"https://inara.cz/elite/starsystem/?search={encoded}"

        changed = False
        if "inara_url" not in fm:
            fm["inara_url"] = url
            changed = True

        if changed:
            new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_fm}---\n{body}"
            md_file.write_text(new_content, encoding="utf-8")
            updated += 1

    return updated


def main():
    l_updated = enrich_locations()
    print(f"Updated {l_updated} locations with Inara links")
    print("Skipped factions and persons — Inara search is unreliable for these types")


if __name__ == "__main__":
    main()
