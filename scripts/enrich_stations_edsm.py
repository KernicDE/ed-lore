#!/usr/bin/env python3
"""
enrich_stations_edsm.py — Batch-enrich station entities from EDSM API.
Fills missing station_type, distance_to_arrival, allegiance, government,
economy, second_economy, have_market, have_shipyard, have_outfitting.
Rate limit: 1 request per second.
Caches results per system to avoid duplicate API calls.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import httpx
import yaml

BASE_DIR = Path(__file__).parent.parent
STATIONS_DIR = BASE_DIR / "Entities" / "station"
EDSM_API = "https://www.edsm.net/api-system-v1/stations"
RATE_LIMIT = 0.3
REQUEST_TIMEOUT = 15.0


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
    clean_fm = {k: v for k, v in fm.items() if v is not None and v != []}
    yml = yaml.dump(clean_fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
    content = f"---\n{yml}---\n\n{body}\n"
    path.write_text(content, encoding="utf-8")


def fetch_stations(system_name: str) -> list[dict[str, Any]]:
    with httpx.Client(timeout=REQUEST_TIMEOUT) as client:
        resp = client.get(EDSM_API, params={"systemName": system_name})
        resp.raise_for_status()
        data = resp.json()
    return data.get("stations", [])


def match_station(name: str, stations: list[dict[str, Any]]) -> dict[str, Any] | None:
    name_norm = name.strip().lower()
    for st in stations:
        if st.get("name", "").strip().lower() == name_norm:
            return st
    return None


def update_station(fm: dict[str, Any], data: dict[str, Any]) -> bool:
    changed = False

    mapping = {
        "station_type": ("type", str),
        "distance_to_arrival": ("distanceToArrival", (int, float)),
        "allegiance": ("allegiance", str),
        "government": ("government", str),
        "economy": ("economy", str),
        "second_economy": ("secondEconomy", str),
        "have_market": ("haveMarket", bool),
        "have_shipyard": ("haveShipyard", bool),
        "have_outfitting": ("haveOutfitting", bool),
    }

    for dst_key, (src_key, expected_type) in mapping.items():
        val = data.get(src_key)
        if val is not None and val != "":
            if isinstance(val, expected_type):
                if dst_key not in fm or fm.get(dst_key) is None or fm.get(dst_key) == "":
                    fm[dst_key] = val
                    changed = True

    return changed


def main() -> None:
    md_files = sorted(STATIONS_DIR.glob("*.md"))
    print(f"Found {len(md_files)} station files.", flush=True)

    # Parse all files
    records: list[tuple[Path, dict[str, Any], str]] = []
    for path in md_files:
        fm, body = parse_frontmatter(path)
        name = fm.get("name", "")
        system = fm.get("system", "")
        if not name or not system:
            continue
        records.append((path, fm, body))

    # Group by system
    system_to_records: dict[str, list[tuple[Path, dict[str, Any], str]]] = {}
    for path, fm, body in records:
        system = fm.get("system", "").strip()
        system_to_records.setdefault(system, []).append((path, fm, body))

    unique_systems = list(system_to_records.keys())
    print(f"Unique systems: {len(unique_systems)}", flush=True)

    # Fetch and update
    cache: dict[str, list[dict[str, Any]]] = {}
    updated = 0
    errors = 0
    for i, system in enumerate(unique_systems):
        if system in cache:
            stations = cache[system]
        else:
            try:
                stations = fetch_stations(system)
                cache[system] = stations
            except Exception as e:
                print(f"  ERROR fetching {system}: {e}", flush=True)
                stations = []
                errors += 1
            if i < len(unique_systems) - 1:
                time.sleep(RATE_LIMIT)

        for path, fm, body in system_to_records[system]:
            name = fm.get("name", "")
            data = match_station(name, stations)
            if not data:
                continue
            if update_station(fm, data):
                write_frontmatter(path, fm, body)
                updated += 1

        if (i + 1) % 10 == 0 or i == len(unique_systems) - 1:
            print(f"  Progress: {i + 1}/{len(unique_systems)} systems, {updated} updated, {errors} errors", flush=True)

    print(f"Done. Updated {updated} station files.", flush=True)


if __name__ == "__main__":
    main()
