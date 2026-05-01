#!/usr/bin/env python3
"""Enrich location entities with data from EDSM API."""

import yaml
from pathlib import Path
import httpx
import time
from urllib.parse import urlencode

ENTITIES_DIR = Path("Entities/location")
BATCH_SIZE = 20
DELAY = 1.5  # seconds between batches

EDSM_SYSTEMS_URL = "https://www.edsm.net/api-v1/systems"


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


def fetch_systems_batch(names):
    """Fetch system data from EDSM for a batch of names."""
    params = [("showInformation", "1"), ("showCoordinates", "1")]
    for name in names:
        params.append(("systemName[]", name))

    url = f"{EDSM_SYSTEMS_URL}?{urlencode(params)}"
    try:
        resp = httpx.get(url, timeout=30)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  Error fetching batch: {e}")
        return []


def main():
    # Collect all location entities
    locations = []
    for md_file in ENTITIES_DIR.glob("*.md"):
        fm, body = parse_frontmatter(md_file)
        if not fm:
            continue
        name = fm.get("name", md_file.stem.replace("-", " ").title())
        locations.append({
            "file": md_file,
            "name": name,
            "fm": fm,
            "body": body,
        })

    print(f"Found {len(locations)} location entities")

    # Process in batches
    enriched = 0
    not_found = 0
    for i in range(0, len(locations), BATCH_SIZE):
        batch = locations[i:i + BATCH_SIZE]
        names = [loc["name"] for loc in batch]
        print(f"Batch {i // BATCH_SIZE + 1}/{(len(locations) + BATCH_SIZE - 1) // BATCH_SIZE}: {len(batch)} systems")

        data = fetch_systems_batch(names)

        # Map results by name
        results = {r["name"].lower(): r for r in data if "name" in r}

        for loc in batch:
            name_lower = loc["name"].lower()
            result = results.get(name_lower)

            if not result:
                not_found += 1
                continue

            fm = loc["fm"]
            info = result.get("information") or {}
            coords = result.get("coords")

            # Add EDSM data
            if coords:
                fm["coords"] = coords
            if info.get("allegiance"):
                fm["allegiance"] = info["allegiance"]
            if info.get("government"):
                fm["government"] = info["government"]
            if info.get("faction"):
                fm["controlling_faction"] = info["faction"]
            if info.get("population"):
                fm["population"] = info["population"]
            if info.get("security"):
                fm["security"] = info["security"]
            if info.get("economy"):
                fm["economy"] = info["economy"]
            if info.get("secondEconomy"):
                fm["second_economy"] = info["secondEconomy"]

            # Add Inara/EDSM links
            fm["edsm_url"] = f"https://www.edsm.net/en/system?search={loc['name'].replace(' ', '%20')}"
            fm["inara_url"] = f"https://inara.cz/elite/starsystem/?search={loc['name'].replace(' ', '%20')}"

            # Write back
            new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_fm}---\n{loc['body']}"
            loc["file"].write_text(new_content, encoding="utf-8")
            enriched += 1

        if i + BATCH_SIZE < len(locations):
            time.sleep(DELAY)

    print(f"\nEnriched {enriched} locations")
    print(f"Not found in EDSM: {not_found}")


if __name__ == "__main__":
    main()
