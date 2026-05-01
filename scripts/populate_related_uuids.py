#!/usr/bin/env python3
"""Populate related_uuids for articles that don't have them."""
from pathlib import Path
from datetime import datetime
import yaml

BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "Archive"


def parse_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1].strip()) or {}
    except yaml.YAMLError:
        return None


def write_frontmatter(path: Path, fm: dict, body: str):
    yaml_text = yaml.dump(fm, default_flow_style=False, sort_keys=False, allow_unicode=True)
    content = f"---\n{yaml_text}---\n{body}"
    path.write_text(content, encoding="utf-8")


# Load all articles
articles = []
for md_file in sorted(ARCHIVE_DIR.rglob("*.md")):
    fm = parse_frontmatter(md_file)
    if not fm:
        continue
    articles.append({
        "path": md_file,
        "fm": fm,
        "uuid": fm.get("uuid", ""),
        "date": str(fm.get("date", "")),
        "arc_id": fm.get("arc_id"),
        "entities": set(fm.get("entities") or []),
        "groups": set(fm.get("groups") or []),
        "locations": set(fm.get("locations") or []),
        "persons": set(fm.get("persons") or []),
        "technologies": set(fm.get("technologies") or []),
        "existing_related": set(fm.get("related_uuids") or []),
    })

uuid_to_article = {a["uuid"]: a for a in articles if a["uuid"]}
print(f"Loaded {len(articles)} articles")

# Group by arc
by_arc = {}
for a in articles:
    if a["arc_id"]:
        by_arc.setdefault(a["arc_id"], []).append(a)

# Sort arc articles by date
for arc_id in by_arc:
    by_arc[arc_id].sort(key=lambda x: x["date"])

updated_count = 0
new_links = 0

# Process arc articles without related_uuids
for arc_id, arc_articles in by_arc.items():
    for i, a in enumerate(arc_articles):
        if a["existing_related"]:
            continue  # Already has related_uuids
        
        # Link to up to 4 nearest neighbors in the same arc (2 before, 2 after)
        neighbors = []
        for offset in [-2, -1, 1, 2]:
            j = i + offset
            if 0 <= j < len(arc_articles):
                neighbors.append(arc_articles[j]["uuid"])
        
        if not neighbors:
            continue
        
        a["fm"]["related_uuids"] = neighbors
        updated_count += 1
        new_links += len(neighbors)
        
        # Ensure bidirectional
        for nuuid in neighbors:
            if nuuid in uuid_to_article:
                na = uuid_to_article[nuuid]
                if a["uuid"] not in na["existing_related"]:
                    na["existing_related"].add(a["uuid"])
                    if "related_uuids" not in na["fm"]:
                        na["fm"]["related_uuids"] = []
                    if a["uuid"] not in na["fm"]["related_uuids"]:
                        na["fm"]["related_uuids"].append(a["uuid"])

# Process standalone articles (no arc_id, no related_uuids)
standalone = [a for a in articles if not a["arc_id"] and not a["existing_related"]]
print(f"Standalone articles to link: {len(standalone)}")

for a in standalone:
    a_all = a["entities"] | a["groups"] | a["locations"] | a["persons"] | a["technologies"]
    if not a_all:
        continue
    
    scores = []
    for b in articles:
        if b["uuid"] == a["uuid"]:
            continue
        b_all = b["entities"] | b["groups"] | b["locations"] | b["persons"] | b["technologies"]
        shared = len(a_all & b_all)
        if shared == 0:
            continue
        date_bonus = 0
        try:
            da = datetime.strptime(a["date"], "%Y-%m-%d")
            db = datetime.strptime(b["date"], "%Y-%m-%d")
            delta = abs((da - db).days)
            if delta <= 30:
                date_bonus = 2
            elif delta <= 90:
                date_bonus = 1
        except Exception:
            pass
        scores.append((b["uuid"], shared + date_bonus))
    
    scores.sort(key=lambda x: -x[1])
    top = [uuid for uuid, _ in scores[:5]]
    
    if not top:
        continue
    
    a["fm"]["related_uuids"] = top
    updated_count += 1
    new_links += len(top)
    
    # Ensure bidirectional
    for nuuid in top:
        if nuuid in uuid_to_article:
            na = uuid_to_article[nuuid]
            if a["uuid"] not in na["existing_related"]:
                na["existing_related"].add(a["uuid"])
                if "related_uuids" not in na["fm"]:
                    na["fm"]["related_uuids"] = []
                if a["uuid"] not in na["fm"]["related_uuids"]:
                    na["fm"]["related_uuids"].append(a["uuid"])

print(f"Updated {updated_count} articles with {new_links} new related links")

# Write back all modified articles
written = 0
for a in articles:
    fm = a["fm"]
    path = a["path"]
    text = path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        continue
    body = parts[2]
    # Only write if related_uuids was modified (check if it exists in fm and wasn't originally there)
    if "related_uuids" in fm:
        write_frontmatter(path, fm, body)
        written += 1

print(f"Wrote {written} files")
