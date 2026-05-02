#!/usr/bin/env python3
"""Remove unreliable Inara links from faction and person entities."""
import yaml
from pathlib import Path

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

def remove_inara(subdir_name):
    subdir = ENTITIES_DIR / subdir_name
    if not subdir.exists():
        return 0
    removed = 0
    for md_file in subdir.glob("*.md"):
        fm, body = parse_frontmatter(md_file)
        if not fm:
            continue
        if "inara_url" in fm:
            del fm["inara_url"]
            new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_fm}---\n{body}"
            md_file.write_text(new_content, encoding="utf-8")
            removed += 1
    return removed

if __name__ == "__main__":
    f = remove_inara("faction")
    p = remove_inara("person")
    print(f"Removed inara_url from {f} faction files")
    print(f"Removed inara_url from {p} person files")
