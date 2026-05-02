#!/usr/bin/env python3
"""
build_graph.py — Compile Archive/, Entities/, and Arcs/ into lore_graph.json.
Build-time script that flattens the enriched Markdown corpus into a single JSON.
Auto-generates entity/arc profile stubs from the corpus.
"""
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from collections import defaultdict, Counter

import yaml

BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "Archive"
ENTITIES_DIR = BASE_DIR / "Entities"
ARCS_DIR = ENTITIES_DIR / "Arcs"
OUTPUT_FILE = BASE_DIR / "lore_graph.json"
WEBSITE_DATA_DIR = BASE_DIR / "website" / "public" / "data"

MERGE_ALIASES: dict[str, str] = {
    "Sirius Corp": "Sirius Corporation",
    "Sirius Gov": "Sirius Corporation",
    "Pilots' Federation": "Pilots Federation",
    "ACT": "Affiliated Counter-Terrorism unit",
    "NMLA": "Neo-Marlinist Liberation Army",
    "Aegis Core": "Aegis",
    "Aegis Research": "Aegis",
    "Palin": "Ishmael Palin",
    "Arissa": "Arissa Lavigny-Duval",
    "Hudson": "Zachary Hudson",
    "Winters": "Felicia Winters",
    "Mahon": "Edmund Mahon",
    "Blaine": "Anders Blaine",
    "Patreus": "Denton Patreus",
    "Torval": "Zemina Torval",
    "Aisling": "Aisling Duval",
    "Halsey": "Jasmina Halsey",
    "Archer": "Jerome Archer",
    "Kaine": "Nakato Kaine",
    "Grom": "Yuri Grom",
    "Delaine": "Archon Delaine",
    "Antal": "Pranav Antal",
    "Loren": "Kahina Tijani Loren",
    "Kahina": "Kahina Tijani Loren",
    "Salomé": "Kahina Tijani Loren",
    "Salome": "Kahina Tijani Loren",
    "Rackham": "Zachary Rackham",
    "Seo": "Seo Jin-ae",
    "Jin-ae": "Seo Jin-ae",
    "Tesreau": "Alba Tesreau",
    "Farseer": "Felicity Farseer",
    "Faulcon": "Faulcon DeLacy",
    "DeLacy": "Faulcon DeLacy",
    "Lakon": "Lakon Spaceways",
    "Saud Kruger": "Saud Kruger",
    "Dr. Walden": "Hans Walden",
}

LOCATION_BLOCKLIST = {
    "Thargoid", "Aegis", "Guardian", "Alliance", "Empire", "Federation",
    "Federal", "Imperial", "Galactic", "Sirius", "Azimuth", "Salvation",
    "NMLA", "ACT", "INRA", "Marlinist", "Colonia", "Pleiades",
    "Col 285 Sector", "Wregoe Sector", "Swoilz Sector",
    "California Sector", "Witch Head Sector", "Coalsack Sector",
    "Pleiades Sector", "Hyades Sector", "Sirius Sector", "Achenar Sector",
    "Musca", "Ophiuchus", "Cepheus", "Pegasi Sector", "NGC",
}

ENTITY_BLOCKLIST = {
    "The", "A", "An", "This", "That", "It", "He", "She", "They",
    "Imperial", "Federal", "Alliance", "Empire", "Federation", "Galactic",
    "Today", "Yesterday", "Last", "Next", "First", "Second",
    "Sirius", "Gutamaya", "Core", "Dynamics", "Brewer", "Pacap", "Olympus",
    "Money Matters", "Jameson Memorial", "Radio Sidewinder", "Interstellar Press",
    "Alliance News Network", "Federal Times", "Imperial Herald",
    "Thargoid", "Guardian", "Aegis", "NMLA", "Marlinist", "Azimuth",
    "Salvation", "ACT", "INRA", "Emperor", "President", "Prime Minister",
    "Shadow President", "Senator", "Admiral", "General", "Commander", "CEO",
}


def parse_frontmatter(path: Path) -> dict[str, Any] | None:
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


def extract_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return text.strip()


def normalize_entity(name: str) -> str | None:
    name = name.strip()
    if not name or len(name) < 3:
        return None
    if name in ENTITY_BLOCKLIST:
        return None
    return MERGE_ALIASES.get(name, name)


def normalize_location(name: str) -> str | None:
    name = name.strip()
    if not name or len(name) < 3:
        return None
    if name in LOCATION_BLOCKLIST:
        return None
    return name


def make_entity_id(name: str) -> str:
    # Normalize Unicode: decompose accents, strip combining marks, then remove non-word chars
    n = unicodedata.normalize("NFD", name)
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return re.sub(r"[^\w-]", "", n.lower().replace(" ", "-"))


def build() -> dict[str, Any]:
    graph: dict[str, Any] = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "article_count": 0,
            "entity_count": 0,
            "arc_count": 0,
        },
        "articles": [],
        "entities": {},
        "arcs": {},
        "timeline_index": {},
        "entity_cooccurrence": {},
    }

    entity_mentions: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"mentions": 0, "articles": [], "first_seen": None, "last_seen": None}
    )
    arc_mentions: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"mentions": 0, "articles": [], "first_seen": None, "last_seen": None}
    )
    location_mentions: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"mentions": 0, "articles": [], "first_seen": None, "last_seen": None}
    )
    group_mentions: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"mentions": 0, "articles": [], "first_seen": None, "last_seen": None}
    )
    person_mentions: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"mentions": 0, "articles": [], "first_seen": None, "last_seen": None}
    )
    technology_mentions: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"mentions": 0, "articles": [], "first_seen": None, "last_seen": None}
    )

    article_paths = list(ARCHIVE_DIR.rglob("*.md"))
    print(f"Processing {len(article_paths)} articles...")

    for i, article_path in enumerate(sorted(article_paths)):
        if (i + 1) % 500 == 0:
            print(f"  ... {i + 1}")

        fm = parse_frontmatter(article_path)
        if not fm:
            continue
        body = extract_body(article_path)
        date_raw = fm.get("date", "")
        date = str(date_raw) if date_raw else ""
        uuid = fm.get("uuid", "")
        arc_id = fm.get("arc_id")

        # Normalise entities
        clean_entities = []
        seen = set()
        for e in fm.get("entities", []):
            c = normalize_entity(e)
            if c and c not in seen:
                clean_entities.append(c)
                seen.add(c)
                d = entity_mentions[c]
                d["mentions"] += 1
                d["articles"].append(uuid)
                if not d["first_seen"] or date < d["first_seen"]:
                    d["first_seen"] = date
                if not d["last_seen"] or date > d["last_seen"]:
                    d["last_seen"] = date

        # Normalise groups
        clean_groups = []
        for g in fm.get("groups") or []:
            c = normalize_entity(g) or g
            if c and c not in seen:
                clean_groups.append(c)
                seen.add(c)
                d = group_mentions[c]
                d["mentions"] += 1
                d["articles"].append(uuid)
                if not d["first_seen"] or date < d["first_seen"]:
                    d["first_seen"] = date
                if not d["last_seen"] or date > d["last_seen"]:
                    d["last_seen"] = date

        # Normalise locations
        clean_locations = []
        seen_locs = set()
        for loc in fm.get("locations") or []:
            c = normalize_location(loc)
            if c and c not in seen_locs:
                clean_locations.append(c)
                seen_locs.add(c)
                d = location_mentions[c]
                d["mentions"] += 1
                d["articles"].append(uuid)
                if not d["first_seen"] or date < d["first_seen"]:
                    d["first_seen"] = date
                if not d["last_seen"] or date > d["last_seen"]:
                    d["last_seen"] = date

        # Normalise persons
        for p in fm.get("persons") or []:
            c = normalize_entity(p) or p
            if c:
                d = person_mentions[c]
                d["mentions"] += 1
                d["articles"].append(uuid)
                if not d["first_seen"] or date < d["first_seen"]:
                    d["first_seen"] = date
                if not d["last_seen"] or date > d["last_seen"]:
                    d["last_seen"] = date

        # Normalise technologies
        for t in fm.get("technologies") or []:
            c = normalize_entity(t) or t
            if c:
                d = technology_mentions[c]
                d["mentions"] += 1
                d["articles"].append(uuid)
                if not d["first_seen"] or date < d["first_seen"]:
                    d["first_seen"] = date
                if not d["last_seen"] or date > d["last_seen"]:
                    d["last_seen"] = date

        if arc_id:
            d = arc_mentions[arc_id]
            d["mentions"] += 1
            d["articles"].append(uuid)
            if not d["first_seen"] or date < d["first_seen"]:
                d["first_seen"] = date
            if not d["last_seen"] or date > d["last_seen"]:
                d["last_seen"] = date

        record = {
            "uuid": uuid,
            "title": fm.get("title", ""),
            "slug": fm.get("slug", ""),
            "date": date,
            "source": fm.get("source", ""),
            "entities": clean_entities,
            "groups": clean_groups,
            "locations": clean_locations,
            "topics": fm.get("topics") or [],
            "arc_id": arc_id,
            "arc_chapter": fm.get("arc_chapter"),
            "summary": fm.get("summary", ""),
            "player_impact": fm.get("player_impact", ""),
            "modern_impact": fm.get("modern_impact", ""),
            "persons": fm.get("persons") or [],
            "technologies": fm.get("technologies") or [],
            "legacy_weight": fm.get("legacy_weight", 2),
            "significance": fm.get("significance", "low"),
            "related_uuids": fm.get("related_uuids") or [],
            "body_full": body,
            "body_preview": body[:500] + "..." if len(body) > 500 else body,
            "word_count": len(body.split()),
            "archive_path": str(article_path.relative_to(BASE_DIR)),
        }
        graph["articles"].append(record)

        if date:
            y, m, _ = date.split("-")
            graph["timeline_index"].setdefault(y, {}).setdefault(m, []).append(uuid)

    graph["articles"].sort(key=lambda a: a.get("date", "") or "")
    print(f"Indexed {len(graph['articles'])} articles.")

    # Build entity records
    print("Building entity records...")
    for name, data in entity_mentions.items():
        eid = make_entity_id(name)
        graph["entities"][eid] = {
            "id": eid, "name": name, "type": "person",
            "first_seen_date": data["first_seen"], "last_seen_date": data["last_seen"],
            "mention_count": data["mentions"], "article_uuids": data["articles"],
            "bio": "", "affiliations": [], "related_entities": [], "related_arcs": [],
        }
    for name, data in group_mentions.items():
        eid = make_entity_id(name)
        if eid not in graph["entities"]:
            graph["entities"][eid] = {
                "id": eid, "name": name, "type": "faction",
                "first_seen_date": data["first_seen"], "last_seen_date": data["last_seen"],
                "mention_count": data["mentions"], "article_uuids": data["articles"],
                "bio": "", "affiliations": [], "related_entities": [], "related_arcs": [],
            }
    for name, data in location_mentions.items():
        eid = make_entity_id(name)
        if eid not in graph["entities"]:
            graph["entities"][eid] = {
                "id": eid, "name": name, "type": "location",
                "first_seen_date": data["first_seen"], "last_seen_date": data["last_seen"],
                "mention_count": data["mentions"], "article_uuids": data["articles"],
                "bio": "", "affiliations": [], "related_entities": [], "related_arcs": [],
            }

    for name, data in person_mentions.items():
        eid = make_entity_id(name)
        if eid not in graph["entities"]:
            graph["entities"][eid] = {
                "id": eid, "name": name, "type": "person",
                "first_seen_date": data["first_seen"], "last_seen_date": data["last_seen"],
                "mention_count": data["mentions"], "article_uuids": data["articles"],
                "bio": "", "affiliations": [], "related_entities": [], "related_arcs": [],
            }

    for name, data in technology_mentions.items():
        eid = make_entity_id(name)
        if eid not in graph["entities"]:
            graph["entities"][eid] = {
                "id": eid, "name": name, "type": "technology",
                "first_seen_date": data["first_seen"], "last_seen_date": data["last_seen"],
                "mention_count": data["mentions"], "article_uuids": data["articles"],
                "bio": "", "affiliations": [], "related_entities": [], "related_arcs": [],
            }

    # Merge enriched data from entity files
    print("Merging enriched entity data...")
    for subdir in ENTITIES_DIR.iterdir():
        if not subdir.is_dir() or subdir.name == "Arcs":
            continue
        for md_file in subdir.glob("*.md"):
            eid = md_file.stem
            if eid not in graph["entities"]:
                continue
            content = md_file.read_text(encoding="utf-8")
            parts = content.split("---", 2)
            if len(parts) < 3:
                continue
            try:
                fm = yaml.safe_load(parts[1])
            except Exception:
                continue
            rec = graph["entities"][eid]
            # Merge enriched fields
            for key in ["coords", "allegiance", "government", "controlling_faction",
                        "population", "security", "economy", "second_economy",
                        "edsm_url", "inara_url", "parent_arc", "summary", "description",
                        "status", "outcome", "phases", "key_entities", "bio"]:
                if key in fm and fm[key] is not None:
                    rec[key] = fm[key]

    # Build arc records
    print("Building arc records...")
    for arc_id, data in arc_mentions.items():
        graph["arcs"][arc_id] = {
            "id": arc_id,
            "name": arc_id.replace("-", " ").title(),
            "first_seen_date": data["first_seen"],
            "last_seen_date": data["last_seen"],
            "mention_count": data["mentions"],
            "article_uuids": data["articles"],
            "description": "",
            "key_entities": [],
            "significance": "medium",
        }

    # Merge enriched arc data from Arcs/ markdown frontmatter
    print("Merging enriched arc data...")
    for arc_id, rec in graph["arcs"].items():
        path = ARCS_DIR / f"{arc_id}.md"
        if path.exists():
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---"):
                continue
            parts = text.split("---", 2)
            if len(parts) < 3:
                continue
            try:
                fm = yaml.safe_load(parts[1])
            except Exception:
                continue
            if not isinstance(fm, dict):
                continue
            for key in ["description", "summary", "status", "outcome", "phases", "significance", "key_entities"]:
                if key in fm and fm[key] is not None:
                    rec[key] = fm[key]

    # Co-occurrence
    print("Building co-occurrence matrix...")
    cooccurrence: dict[str, dict[str, int]] = {}
    for art in graph["articles"]:
        ids = [make_entity_id(e) for e in art.get("entities", []) + art.get("groups", []) + art.get("locations", [])]
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                if a == b:
                    continue
                cooccurrence.setdefault(a, {}).setdefault(b, 0)
                cooccurrence[a][b] += 1
                cooccurrence.setdefault(b, {}).setdefault(a, 0)
                cooccurrence[b][a] += 1
    graph["entity_cooccurrence"] = cooccurrence

    # Add related entities
    for eid, rec in graph["entities"].items():
        if eid in cooccurrence:
            top = sorted(cooccurrence[eid].items(), key=lambda x: -x[1])[:10]
            rec["related_entities"] = [{"id": rid, "mentions": c} for rid, c in top]

    # Add key entities to arcs
    for arc_id, rec in graph["arcs"].items():
        counts = Counter()
        for art in graph["articles"]:
            if art.get("arc_id") == arc_id:
                for e in art.get("entities", []) + art.get("groups", []):
                    counts[make_entity_id(e)] += 1
        top = sorted(counts.items(), key=lambda x: -x[1])[:8]
        rec["key_entities"] = [{"id": eid, "mentions": c} for eid, c in top]

    graph["meta"]["article_count"] = len(graph["articles"])
    graph["meta"]["entity_count"] = len(graph["entities"])
    graph["meta"]["arc_count"] = len(graph["arcs"])
    return graph


def write_profiles(graph: dict[str, Any]) -> None:
    ENTITIES_DIR.mkdir(parents=True, exist_ok=True)
    ARCS_DIR.mkdir(parents=True, exist_ok=True)

    for eid, rec in graph["entities"].items():
        subdir = ENTITIES_DIR / rec.get("type", "person")
        subdir.mkdir(parents=True, exist_ok=True)
        path = subdir / f"{eid}.md"
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if len(existing) > 300:
                continue
        fm = {
            "id": eid, "name": rec["name"], "type": rec.get("type", "person"),
            "first_seen_date": rec.get("first_seen_date"),
            "last_seen_date": rec.get("last_seen_date"),
            "mention_count": rec.get("mention_count", 0),
            "related_entities": [r["id"] for r in rec.get("related_entities", [])[:5]],
        }
        fm = {k: v for k, v in fm.items() if v is not None and v != []}
        yml = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
        content = f"---\n{yml}---\n\n<!-- AUTO-GENERATED -->\n\n# {rec['name']}\n\n"
        content += f"First mentioned: **{rec.get('first_seen_date', 'Unknown')}**  \n"
        content += f"Last mentioned: **{rec.get('last_seen_date', 'Unknown')}**  \n"
        content += f"Total mentions: **{rec.get('mention_count', 0)}**\n\n"
        content += "## Related\n\n"
        for rel in rec.get("related_entities", [])[:5]:
            rel_name = graph["entities"].get(rel["id"], {}).get("name", rel["id"])
            content += f"- [[{rel_name}]] ({rel['mentions']} co-mentions)\n"
        content += "\n## Biography\n\n*[To be enriched]*\n"
        path.write_text(content, encoding="utf-8")

    for arc_id, rec in graph["arcs"].items():
        path = ARCS_DIR / f"{arc_id}.md"
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            if len(existing) > 300:
                continue
        fm = {
            "id": arc_id, "name": rec["name"],
            "first_seen_date": rec.get("first_seen_date"),
            "last_seen_date": rec.get("last_seen_date"),
            "mention_count": rec.get("mention_count", 0),
            "significance": rec.get("significance", "medium"),
            "key_entities": [e["id"] for e in rec.get("key_entities", [])[:5]],
        }
        fm = {k: v for k, v in fm.items() if v is not None and v != []}
        yml = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
        content = f"---\n{yml}---\n\n<!-- AUTO-GENERATED -->\n\n# {rec['name']}\n\n"
        content += f"First seen: **{rec.get('first_seen_date', 'Unknown')}**  \n"
        content += f"Last seen: **{rec.get('last_seen_date', 'Unknown')}**  \n"
        content += f"Articles: **{rec.get('mention_count', 0)}**\n\n"
        content += "## Key Figures\n\n"
        for ent in rec.get("key_entities", [])[:5]:
            ent_name = graph["entities"].get(ent["id"], {}).get("name", ent["id"])
            content += f"- [[{ent_name}]] ({ent['mentions']} mentions)\n"
        content += "\n## Description\n\n*[To be enriched]*\n"
        path.write_text(content, encoding="utf-8")


AUDIO_MANIFEST_FILE = BASE_DIR / "scripts" / "audio_manifest.json"

def main() -> int:
    print("Building lore_graph.json...")
    graph = build()

    # Mark articles that have generated audio
    audio_uuids: set[str] = set()
    if AUDIO_MANIFEST_FILE.exists():
        audio_manifest = json.loads(AUDIO_MANIFEST_FILE.read_text(encoding="utf-8"))
        audio_uuids = set(audio_manifest.keys())
        print(f"Audio manifest found: {len(audio_uuids)} files")
    for art in graph["articles"]:
        art["has_audio"] = art["uuid"] in audio_uuids

    OUTPUT_FILE.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Articles: {graph['meta']['article_count']}, Entities: {graph['meta']['entity_count']}, Arcs: {graph['meta']['arc_count']}")

    print("Writing split JSON for async loading...")
    WEBSITE_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Fields NOT needed by client-side React app:
    # slug, significance, legacy_weight, related_uuids, archive_path, source, word_count, arc_chapter
    CLIENT_ARTICLE_STRIP = {
        "slug", "significance", "legacy_weight", "related_uuids",
        "archive_path", "source", "word_count", "arc_chapter", "body_full",
        "body_preview",  # moved to search-index.json
    }

    # Build lite articles for client (timeline + context panel)
    client_articles = []
    search_articles = []
    for a in graph["articles"]:
        client_articles.append({k: v for k, v in a.items() if k not in CLIENT_ARTICLE_STRIP})
        search_articles.append({
            "uuid": a["uuid"],
            "title": a["title"],
            "date": a["date"],
            "body_preview": a.get("body_preview", ""),
        })

    # Strip server-only fields from entities for client JSON
    # article_uuids is only needed by server-rendered entity/arc pages
    client_entities = {}
    for eid, rec in graph["entities"].items():
        client_rec = {k: v for k, v in rec.items() if k != "article_uuids"}
        client_entities[eid] = client_rec

    meta = {
        **graph,
        "articles": client_articles,
        "entities": client_entities,
    }
    bodies = {a["uuid"]: a.get("body_full", "") for a in graph["articles"]}

    (WEBSITE_DATA_DIR / "galnet-meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    (WEBSITE_DATA_DIR / "galnet-bodies.json").write_text(json.dumps(bodies, ensure_ascii=False), encoding="utf-8")
    (WEBSITE_DATA_DIR / "search-index.json").write_text(json.dumps(search_articles, ensure_ascii=False), encoding="utf-8")

    # Write tiny version file for cache busting + dynamic header counts
    version = {
        "build": graph["meta"]["generated_at"],
        "article_count": graph["meta"]["article_count"],
        "entity_count": graph["meta"]["entity_count"],
        "arc_count": graph["meta"]["arc_count"],
    }
    (WEBSITE_DATA_DIR / "version.json").write_text(json.dumps(version, ensure_ascii=False), encoding="utf-8")

    meta_size = (WEBSITE_DATA_DIR / 'galnet-meta.json').stat().st_size
    bodies_size = (WEBSITE_DATA_DIR / 'galnet-bodies.json').stat().st_size
    search_size = (WEBSITE_DATA_DIR / 'search-index.json').stat().st_size
    print(f"  galnet-meta.json: {meta_size//1024}KB")
    print(f"  galnet-bodies.json: {bodies_size//1024}KB")
    print(f"  search-index.json: {search_size//1024}KB")


    print("Writing profiles...")
    write_profiles(graph)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
