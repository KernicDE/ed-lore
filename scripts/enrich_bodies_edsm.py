#!/usr/bin/env python3
"""
Enrich body entities from the EDSM API.
Queries https://www.edsm.net/api-system-v1/bodies?systemName=SYSTEMNAME
for systems that contain known bodies.
"""

import json
import time
import yaml
from pathlib import Path
import httpx

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENTITIES_DIR = PROJECT_ROOT / "Entities" / "body"

EDSM_API = "https://www.edsm.net/api-system-v1/bodies"

# Mapping of body names to their parent system names (from known lore / obvious naming)
BODY_SYSTEM_MAP = {
    "Achenar 3": "Achenar",
    "Achenar 6d": "Achenar",
    "Altais 2B": "Altais",
    "Brestla A1": "Brestla",
    "Chukchan 5 b": "Chukchan",
    "Colonia 3 C A": "Colonia",
    "Cubeo III": "Cubeo",
    "Delphi 5 a": "Delphi",
    "Earth": "Sol",
    "Etain 4 c": "Etain",
    "HIP 17225 A 1": "HIP 17225",
    "HIP 17862 6 C A": "HIP 17862",
    "HIP 22460 10b": "HIP 22460",
    "Jupiter": "Sol",
    "Lave II": "Lave",
    "LHS 3447 B 1 a": "LHS 3447",
    "LP 339-7 4 A": "LP 339-7",
    "Lugh 6": "Lugh",
    "Maia A 3 a": "Maia",
    "Maia b1ba": "Maia",
    "Mars": "Sol",
    "Merope 5 C": "Merope",
    "Nanomam 1": "Nanomam",
    "Novas A 6": "Novas",
    "Skaudai CH-B d14-34": "Skaudai CH-B d14-34",
    "Talos 2": "Talos",
    "Topaz": "Merope",
    "Vennik 1": "Vennik",
    "Wredguia QA-N b34-4": "Wredguia QA-N b34-4",
    "Wredguia SX-L d7-91": "Wredguia SX-L d7-91",
    "Wredguia WD-K D8-66": "Wredguia WD-K D8-66",
    "Wredguia XD-K d8-78": "Wredguia XD-K d8-78",
    # Already have system from manual work:
    "Biggs Colony": "Altair",
    "Chione": "Prism",
    "Lily May": "Themiscrya",
}


def load_frontmatter(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    if content.startswith("---"):
        _, fm, _ = content.split("---", 2)
        return yaml.safe_load(fm) or {}
    return {}


def save_frontmatter(path: Path, data: dict, body: str):
    fm = yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False)
    path.write_text(f"---\n{fm}---\n{body}", encoding="utf-8")


def enrich_bodies():
    bodies = list(ENTITIES_DIR.glob("*.md"))
    print(f"Found {len(bodies)} body files")

    # Group bodies by system
    system_to_bodies: dict[str, list[tuple[Path, str]]] = {}
    for path in bodies:
        data = load_frontmatter(path)
        name = data.get("name", path.stem.replace("-", " ").title())
        system = data.get("system") or BODY_SYSTEM_MAP.get(name)
        if not system:
            print(f"  SKIP (no system known): {name}")
            continue
        system_to_bodies.setdefault(system, []).append((path, name))

    print(f"Grouped into {len(system_to_bodies)} systems")

    updated = 0
    skipped = 0
    not_found = 0

    for system_name, body_list in system_to_bodies.items():
        try:
            resp = httpx.get(EDSM_API, params={"systemName": system_name}, timeout=30.0)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as exc:
            print(f"  EDSM ERROR for system '{system_name}': {exc}")
            continue

        bodies_data = payload.get("bodies", []) if isinstance(payload, dict) else []
        if not bodies_data:
            print(f"  No bodies returned for system '{system_name}'")
            continue

        # Build lookup by name (case-insensitive)
        edsm_lookup = {}
        for b in bodies_data:
            edsm_lookup[b.get("name", "").lower()] = b

        for path, body_name in body_list:
            data = load_frontmatter(path)
            content = path.read_text(encoding="utf-8")
            body_text = content.split("---", 2)[2] if content.count("---") >= 2 else ""

            edsm_body = edsm_lookup.get(body_name.lower())
            if not edsm_body:
                # Try with the system name prefixed
                edsm_body = edsm_lookup.get(f"{system_name} {body_name}".lower())
            if not edsm_body:
                # Try stripping system prefix from EDSM names
                for edsm_name, edsm_info in edsm_lookup.items():
                    if body_name.lower() in edsm_name:
                        edsm_body = edsm_info
                        break

            if not edsm_body:
                print(f"    NOT FOUND: {body_name} in {system_name}")
                not_found += 1
                continue

            changed = False

            # Update system if missing
            if not data.get("system"):
                data["system"] = system_name
                changed = True

            # Update body_type if missing
            if not data.get("body_type") and edsm_body.get("subType"):
                data["body_type"] = edsm_body["subType"]
                changed = True

            # Update coords from parent system if missing
            if not data.get("coords"):
                system_coords = payload.get("coords")
                if system_coords:
                    data["coords"] = system_coords
                    changed = True

            # Update distance_to_arrival if present
            if edsm_body.get("distanceToArrival") is not None and not data.get("distance_to_arrival"):
                data["distance_to_arrival"] = edsm_body["distanceToArrival"]
                changed = True

            # Update gravity if present
            if edsm_body.get("gravity") is not None and not data.get("gravity"):
                data["gravity"] = round(edsm_body["gravity"], 4)
                changed = True

            # Update surfaceTemperature if present
            if edsm_body.get("surfaceTemperature") is not None and not data.get("surface_temperature"):
                data["surface_temperature"] = round(edsm_body["surfaceTemperature"], 2)
                changed = True

            # Update terraforming state
            if edsm_body.get("terraformingState") and not data.get("terraforming_state"):
                data["terraforming_state"] = edsm_body["terraformingState"]
                changed = True

            # Update atmosphere type
            if edsm_body.get("atmosphereType") and not data.get("atmosphere_type"):
                data["atmosphere_type"] = edsm_body["atmosphereType"]
                changed = True

            # Update volcanism type
            if edsm_body.get("volcanismType") and not data.get("volcanism_type"):
                data["volcanism_type"] = edsm_body["volcanismType"]
                changed = True

            # Update orbital data
            if edsm_body.get("orbitalPeriod") is not None and not data.get("orbital_period"):
                data["orbital_period"] = round(edsm_body["orbitalPeriod"], 4)
                changed = True

            if edsm_body.get("semiMajorAxis") is not None and not data.get("semi_major_axis"):
                data["semi_major_axis"] = round(edsm_body["semiMajorAxis"], 4)
                changed = True

            if edsm_body.get("rotationalPeriod") is not None and not data.get("rotational_period"):
                data["rotational_period"] = round(edsm_body["rotationalPeriod"], 4)
                changed = True

            if edsm_body.get("radius") is not None and not data.get("radius"):
                data["radius"] = round(edsm_body["radius"], 2)
                changed = True

            if edsm_body.get("earthMasses") is not None and not data.get("earth_masses"):
                data["earth_masses"] = round(edsm_body["earthMasses"], 4)
                changed = True

            # Rings
            if edsm_body.get("rings") and not data.get("rings"):
                data["rings"] = [
                    {
                        "name": r.get("name"),
                        "type": r.get("type"),
                        "mass": r.get("mass"),
                        "innerRadius": r.get("innerRadius"),
                        "outerRadius": r.get("outerRadius"),
                    }
                    for r in edsm_body["rings"]
                ]
                changed = True

            # Materials (for mining)
            if edsm_body.get("materials") and not data.get("materials"):
                data["materials"] = edsm_body["materials"]
                changed = True

            if changed:
                save_frontmatter(path, data, body_text)
                print(f"    UPDATED: {body_name}")
                updated += 1
            else:
                skipped += 1

        time.sleep(1.0)  # Rate limit

    print(f"\nDone. Updated: {updated}, Skipped (no changes): {skipped}, Not found: {not_found}")


if __name__ == "__main__":
    enrich_bodies()
