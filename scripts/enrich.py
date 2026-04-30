#!/usr/bin/env python3
"""
enrich.py — GalNet article enrichment pipeline.

Reads raw articles from GalNet/, produces:
  - Archive/YYYY/MM/DD_slug.md   (enhanced frontmatter + wiki links)
  - Entities/<type>/<id>.md      (entity profiles)
  - Arcs/<id>.md                 (story arc narratives)

This script is designed to be run incrementally: it skips articles whose
uuid + file hash have already been processed (tracked in .sync_state.json).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).parent.parent
GALNET_DIR = BASE_DIR / "GalNet"
ARCHIVE_DIR = BASE_DIR / "Archive"
ENTITIES_DIR = BASE_DIR / "Entities"
ARCS_DIR = BASE_DIR / "Entities" / "Arcs"
STATE_FILE = BASE_DIR / ".sync_state.json"

# Directories to ensure exist
DIRS = [ARCHIVE_DIR, ENTITIES_DIR, ARCS_DIR]

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Article:
    uuid: str
    title: str
    slug: str
    date: str          # YYYY-MM-DD (Elite date)
    source: str
    body: str
    entities: list[str] = field(default_factory=list)
    groups: list[str] = field(default_factory=list)
    locations: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    arc_id: str | None = None
    arc_chapter: str | None = None
    modern_impact: str | None = None
    legacy_weight: int = 1

    def to_frontmatter(self) -> dict[str, Any]:
        fm = {
            "uuid": self.uuid,
            "title": self.title,
            "slug": self.slug,
            "date": self.date,
            "source": self.source,
        }
        if self.entities:
            fm["entities"] = self.entities
        if self.groups:
            fm["groups"] = self.groups
        if self.locations:
            fm["locations"] = self.locations
        if self.topics:
            fm["topics"] = self.topics
        if self.arc_id:
            fm["arc_id"] = self.arc_id
        if self.arc_chapter:
            fm["arc_chapter"] = self.arc_chapter
        if self.modern_impact:
            fm["modern_impact"] = self.modern_impact
        if self.legacy_weight != 1:
            fm["legacy_weight"] = self.legacy_weight
        return fm


@dataclass
class Entity:
    id: str
    name: str
    type: str  # person, faction, system, technology, concept, ship, location
    aliases: list[str] = field(default_factory=list)
    affiliation: str | None = None
    status: str = "active"  # active | deceased | unknown | dissolved
    first_seen: str | None = None
    last_seen: str | None = None
    article_count: int = 0
    related_entities: list[str] = field(default_factory=list)
    arcs: list[str] = field(default_factory=list)
    biography: str = ""
    modern_status: str = ""
    appearances: list[tuple[str, str]] = field(default_factory=list)  # (date, title)

    def to_frontmatter(self) -> dict[str, Any]:
        fm: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
        }
        if self.aliases:
            fm["aliases"] = self.aliases
        if self.affiliation:
            fm["affiliation"] = self.affiliation
        if self.status != "active":
            fm["status"] = self.status
        if self.first_seen:
            fm["first_seen"] = self.first_seen
        if self.last_seen:
            fm["last_seen"] = self.last_seen
        if self.article_count:
            fm["article_count"] = self.article_count
        if self.related_entities:
            fm["related_entities"] = self.related_entities
        if self.arcs:
            fm["arcs"] = self.arcs
        return fm


@dataclass
class Arc:
    id: str
    name: str
    type: str = "arc"
    start_date: str | None = None
    end_date: str | None = None
    article_count: int = 0
    key_entities: list[str] = field(default_factory=list)
    summary: str = ""
    phases: list[tuple[str, str]] = field(default_factory=list)  # (label, description)
    modern_relevance: str = ""

    def to_frontmatter(self) -> dict[str, Any]:
        fm: dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "type": self.type,
        }
        if self.start_date:
            fm["start_date"] = self.start_date
        if self.end_date:
            fm["end_date"] = self.end_date
        if self.article_count:
            fm["article_count"] = self.article_count
        if self.key_entities:
            fm["key_entities"] = self.key_entities
        return fm


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def file_hash(path: Path) -> str:
    """Return SHA-256 hex digest of file contents."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_sync_state() -> dict[str, str]:
    """Load map of uuid -> file_hash for already-processed articles."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_sync_state(state: dict[str, str]) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True))


def parse_galnet_article(path: Path) -> dict[str, Any]:
    """Parse a GalNet markdown file into raw frontmatter + body."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {"error": "missing frontmatter"}

    # Split on first '---\n' after the opening ---
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {"error": "malformed frontmatter"}

    fm_text = parts[1].strip()
    body = parts[2].strip()

    try:
        frontmatter = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as e:
        return {"error": f"yaml parse error: {e}"}

    return {
        "uuid": frontmatter.get("uuid"),
        "title": frontmatter.get("title"),
        "slug": frontmatter.get("slug"),
        "date": frontmatter.get("ed_date"),
        "source": frontmatter.get("source"),
        "body": body,
    }


def slugify_entity(name: str) -> str:
    """Convert entity name to URL-safe ID."""
    s = name.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return s


def write_article(article: Article) -> Path:
    """Write an enriched article to Archive/YYYY/MM/DD_slug.md."""
    date_parts = article.date.split("-")
    if len(date_parts) != 3:
        raise ValueError(f"invalid date: {article.date}")
    year, month, day = date_parts
    out_dir = ARCHIVE_DIR / year / month
    out_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{day}_{article.slug}.md"
    out_path = out_dir / filename

    fm = article.to_frontmatter()
    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)
    content = f"---\n{fm_yaml}---\n\n{article.body}\n"
    out_path.write_text(content, encoding="utf-8")
    return out_path


def write_entity(entity: Entity) -> Path:
    """Write or update an entity profile."""
    type_dir = ENTITIES_DIR / entity.type
    type_dir.mkdir(parents=True, exist_ok=True)
    out_path = type_dir / f"{entity.id}.md"

    fm = entity.to_frontmatter()
    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)

    # Build markdown body
    lines: list[str] = [f"# {entity.name}", ""]
    if entity.biography:
        lines.extend(["## Biography", entity.biography, ""])
    if entity.modern_status:
        lines.extend(["## Modern Status (3312)", entity.modern_status, ""])
    if entity.appearances:
        lines.extend(["## Appearances", ""])
        for date, title in sorted(entity.appearances):
            slug = slugify_entity(title)
            lines.append(f"- [[{date}-{slug}|{title}]]")
        lines.append("")

    body = "\n".join(lines)
    content = f"---\n{fm_yaml}---\n\n{body}\n"
    out_path.write_text(content, encoding="utf-8")
    return out_path


def write_arc(arc: Arc) -> Path:
    """Write or update an arc narrative."""
    ARCS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = ARCS_DIR / f"{arc.id}.md"

    fm = arc.to_frontmatter()
    fm_yaml = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False)

    lines: list[str] = [f"# {arc.name}", ""]
    if arc.summary:
        lines.extend(["## Summary", arc.summary, ""])
    if arc.phases:
        lines.extend(["## Phases", ""])
        for label, desc in arc.phases:
            lines.append(f"### {label}")
            lines.append(desc)
            lines.append("")
    if arc.modern_relevance:
        lines.extend(["## Modern Relevance", arc.modern_relevance, ""])

    body = "\n".join(lines)
    content = f"---\n{fm_yaml}---\n\n{body}\n"
    out_path.write_text(content, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="Enrich GalNet articles")
    parser.add_argument("--year", type=str, help="Process only a specific Elite year (e.g., 3301)")
    parser.add_argument("--incremental", action="store_true", help="Skip already-processed articles")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without writing")
    args = parser.parse_args()

    for d in DIRS:
        d.mkdir(parents=True, exist_ok=True)

    state = load_sync_state() if args.incremental else {}

    # Discover source files
    if args.year:
        real_year = int(args.year) - 1286
        glob_pattern = str(GALNET_DIR / f"{real_year}-{args.year}" / "*.md")
        source_paths = list(GALNET_DIR.glob(f"{real_year}-{args.year}/*.md"))
    else:
        source_paths = sorted(GALNET_DIR.rglob("*.md"))

    print(f"Discovered {len(source_paths)} source article(s)")

    to_process: list[Path] = []
    for path in source_paths:
        raw = parse_galnet_article(path)
        if "error" in raw:
            print(f"  SKIP {path.name}: {raw['error']}")
            continue
        uuid = raw["uuid"]
        if args.incremental and uuid in state and state[uuid] == file_hash(path):
            continue
        to_process.append(path)

    print(f"Processing {len(to_process)} article(s)")
    if args.dry_run:
        for p in to_process:
            print(f"  would process: {p}")
        return 0

    # TODO: wire in AI-driven enrichment logic here
    # For now, this script is a scaffold. The actual enrichment is done
    # by the AI reading articles and calling write_article / write_entity / write_arc.
    print("Scaffold ready. Enrichment logic to be integrated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
