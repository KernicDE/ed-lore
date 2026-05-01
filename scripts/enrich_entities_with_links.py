#!/usr/bin/env python3
"""Add Inara/EDSM links to faction and person entities."""

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


def enrich_type(subdir_name, url_template):
    """Add links to all entities of a given type."""
    subdir = ENTITIES_DIR / subdir_name
    if not subdir.exists():
        return 0

    updated = 0
    for md_file in subdir.glob("*.md"):
        fm, body = parse_frontmatter(md_file)
        if not fm:
            continue

        name = fm.get("name", md_file.stem.replace("-", " ").title())
        encoded = quote(name)

        changed = False
        url = url_template.format(encoded=encoded, name=name)
        key = "inara_url" if "inara" in url_template else "edsm_url"

        if key not in fm:
            fm[key] = url
            changed = True

        if changed:
            new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_fm}---\n{body}"
            md_file.write_text(new_content, encoding="utf-8")
            updated += 1

    return updated


def main():
    f_updated = enrich_type("faction", "https://inara.cz/elite/minorfaction/?search={encoded}")
    p_updated = enrich_type("person", "https://inara.cz/elite/cmdr-search/?search={encoded}")
    t_updated = enrich_type("technology", "https://inara.cz/elite/commodity/?search={encoded}")

    print(f"Updated {f_updated} factions with Inara links")
    print(f"Updated {p_updated} persons with Inara links")
    print(f"Updated {t_updated} technologies with Inara links")


if __name__ == "__main__":
    main()
