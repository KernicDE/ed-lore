#!/usr/bin/env python3
"""
enrich_systems_edsm.py — Batch-enrich system entities from EDSM API.
Fills missing coords, allegiance, government, population, security, economy,
second_economy, controlling_faction, reserve, and adds EDSM URLs.
Rate limit: 1 request per second.
Batch size: 100 systems per request.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests
import yaml

BASE_DIR = Path(__file__).parent.parent
SYSTEMS_DIR = BASE_DIR / "Entities" / "system"
EDSM_API = "https://www.edsm.net/api-v1/systems"
RATE_LIMIT = 1.0  # seconds between requests


def parse_frontmatter(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    try:
        fm = yaml.safe_load(parts[1].strip()) or {}
    except yaml.YAMLError:
        fm = {}
    body = parts[2].strip()
    return fm, body


def write_frontmatter(path: Path, fm: dict[str, Any], body: str) -> None:
    # Clean None values and empty lists
    clean_fm = {k: v for k, v in fm.items() if v is not None and v != []}
    yml = yaml.dump(clean_fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    content = f"---\n{yml}---\n\n{body}\n"
    path.write_text(content, encoding="utf-8")


def fetch_systems_batch(names: list[str]) -> list[dict[str, Any]]:
    params: dict[str, Any] = {
        "showCoordinates": 1,
        "showInformation": 1,
        "showPrimaryStar": 1,
    }
    for name in names:
        params.setdefault("systemName[]", []).append(name)
    resp = requests.get(EDSM_API, params=params, timeout=60)
    resp.raise_for_status()
    return resp.json()


def update_system(fm: dict[str, Any], data: dict[str, Any]) -> bool:
    changed = False

    # Coords
    coords = data.get("coords")
    if coords and "x" in coords and "y" in coords and "z" in coords:
        if "coords" not in fm or not fm.get("coords"):
            fm["coords"] = {
                "x": coords["x"],
                "y": coords["y"],
                "z": coords["z"],
            }
            changed = True

    # Information block
    info = data.get("information")
    if info:
        mapping = {
            "allegiance": "allegiance",
            "government": "government",
            "population": "population",
            "security": "security",
            "economy": "economy",
            "secondEconomy": "second_economy",
            "faction": "controlling_faction",
            "reserve": "reserve",
        }
        for src_key, dst_key in mapping.items():
            val = info.get(src_key)
            if val is not None and val != "":
                if dst_key not in fm or fm.get(dst_key) is None or fm.get(dst_key) == "":
                    fm[dst_key] = val
                    changed = True

    # EDSM URL
    edsm_id = data.get("id")
    if edsm_id:
        if "edsm_url" not in fm or not fm.get("edsm_url"):
            safe_name = data.get("name", "").replace(" ", "%20")
            fm["edsm_url"] = f"https://www.edsm.net/en/system/id/{edsm_id}/name/{safe_name}"
            changed = True

    return changed


def main() -> None:
    md_files = sorted(SYSTEMS_DIR.glob("*.md"))
    print(f"Found {len(md_files)} system files.")

    # Parse all files
    records: list[tuple[Path, dict[str, Any], str]] = []
    names: list[str] = []
    for path in md_files:
        fm, body = parse_frontmatter(path)
        name = fm.get("name", "")
        if not name:
            continue
        records.append((path, fm, body))
        names.append(name)

    # Batch fetch from EDSM
    batch_size = 100
    all_data: dict[str, dict[str, Any]] = {}
    for i in range(0, len(names), batch_size):
        batch = names[i : i + batch_size]
        print(f"Fetching batch {i // batch_size + 1}/{(len(names) + batch_size - 1) // batch_size}: {len(batch)} systems...")
        try:
            results = fetch_systems_batch(batch)
            for item in results:
                if item and "name" in item:
                    all_data[item["name"]] = item
        except requests.RequestException as e:
            print(f"  ERROR: {e}")
        if i + batch_size < len(names):
            time.sleep(RATE_LIMIT)

    # Update files
    updated = 0
    for path, fm, body in records:
        name = fm.get("name", "")
        data = all_data.get(name)
        if not data:
            continue
        if update_system(fm, data):
            write_frontmatter(path, fm, body)
            updated += 1

    print(f"Done. Updated {updated} system files.")


if __name__ == "__main__":
    main()
