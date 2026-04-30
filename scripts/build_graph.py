#!/usr/bin/env python3
"""
build_graph.py — Compile Archive/, Entities/, and Arcs/ into lore_graph.json.

This is a build-time script that flattens the enriched Markdown corpus into a
single JSON file consumed by the website.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "Archive"
ENTITIES_DIR = BASE_DIR / "Entities"
ARCS_DIR = BASE_DIR / "Entities" / "Arcs"
OUTPUT_FILE = BASE_DIR / "lore_graph.json"


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


def build() -> dict[str, Any]:
    graph: dict[str, Any] = {
        "meta": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "article_count": 0,
            "entity_count": 0,
            "arc_count": 0,
        },
        "articles": [],
        "entities": [],
        "arcs": [],
        "timeline_index": {},
    }

    # Index articles
    for article_path in sorted(ARCHIVE_DIR.rglob("*.md")):
        fm = parse_frontmatter(article_path)
        if not fm:
            continue
        body = extract_body(article_path)
        record = {
            **fm,
            "body_full": body,
            "body_preview": body[:500] + "..." if len(body) > 500 else body,
            "word_count": len(body.split()),
            "archive_path": str(article_path.relative_to(BASE_DIR)),
        }
        graph["articles"].append(record)

        # Build timeline index
        date = fm.get("date")
        if date:
            y, m, _ = date.split("-")
            graph["timeline_index"].setdefault(y, {}).setdefault(m, []).append(fm.get("uuid"))

    # Index entities
    for entity_path in sorted(ENTITIES_DIR.rglob("*.md")):
        if entity_path.parent.name == "Arcs":
            continue
        fm = parse_frontmatter(entity_path)
        if not fm:
            continue
        record = {**fm, "profile_path": str(entity_path.relative_to(BASE_DIR))}
        graph["entities"].append(record)

    # Index arcs
    for arc_path in sorted(ARCS_DIR.glob("*.md")):
        fm = parse_frontmatter(arc_path)
        if not fm:
            continue
        record = {**fm, "profile_path": str(arc_path.relative_to(BASE_DIR))}
        graph["arcs"].append(record)

    # Co-occurrence matrix (entity pairs across articles)
    cooccurrence: dict[str, dict[str, int]] = {}
    for art in graph["articles"]:
        ents = art.get("entities", [])
        for i, a in enumerate(ents):
            aid = re.sub(r"[^\w-]", "", a.lower().replace(" ", "-"))
            for b in ents[i + 1 :]:
                bid = re.sub(r"[^\w-]", "", b.lower().replace(" ", "-"))
                cooccurrence.setdefault(aid, {}).setdefault(bid, 0)
                cooccurrence[aid][bid] += 1
                cooccurrence.setdefault(bid, {}).setdefault(aid, 0)
                cooccurrence[bid][aid] += 1
    graph["entity_cooccurrence"] = cooccurrence

    # Meta counts
    graph["meta"]["article_count"] = len(graph["articles"])
    graph["meta"]["entity_count"] = len(graph["entities"])
    graph["meta"]["arc_count"] = len(graph["arcs"])

    return graph


def main() -> int:
    print("Building lore_graph.json...")
    graph = build()
    OUTPUT_FILE.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")
    print(
        f"Done: {graph['meta']['article_count']} articles, "
        f"{graph['meta']['entity_count']} entities, "
        f"{graph['meta']['arc_count']} arcs"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
