#!/usr/bin/env python3
"""Add parent_arc field to arc files based on the taxonomy."""

import yaml
from pathlib import Path

ARCS_DIR = Path("Entities/Arcs")

# Mapping: arc_id -> parent_arc_id
# Parent arcs are Story Arcs that group related minor arcs
PARENT_MAP = {
    # Federal Politics & Presidential Crises
    "halsey-presidency": "federal-politics",
    "federal-politics": None,  # Top-level Story Arc

    # Imperial Succession & Power Struggles
    "nova-imperium": "imperial-succession",
    "imperial-succession": None,  # Top-level Story Arc
    "prism-senator": "imperial-succession",
    "salome-conspiracy": "imperial-succession",

    # Kumo Crew/Pirate Conflicts
    "kumo-crew-rise": None,  # Top-level Story Arc

    # Exploration & Colonization
    "jaques-station": "distant-worlds-3",
    "trailblazer-colonisation": "distant-worlds-3",
    "distant-worlds-3": None,  # Top-level Story Arc

    # Thargoid & Xenological Arcs (under Second Thargoid War)
    "barnacle-meta-alloy": "thargoid-contact",
    "pleiades-expansion": "thargoid-contact",
    "salvation-azimuth": "thargoid-titan-war",
    "thargoid-titan-war": "thargoid-contact",
    "thargoid-contact": None,  # Top-level Story Arc

    # Guardian Archaeology
    "guardian-ancients": None,  # Top-level Story Arc

    # Independent & Minor Faction Conflicts
    "lugh-independence": "alliance-expansion",
    "onionhead-conflict": "alliance-expansion",
    "falisci-conflict": "alliance-expansion",
    "cayutorme-conflict": "alliance-expansion",
    "cerberus-plague": "alliance-expansion",
    "alliance-expansion": None,  # Top-level Story Arc

    # Anomalous/Mystery Arcs
    "formidine-rift": "unknown-artefacts",
    "antares-mystery": "unknown-artefacts",
    "raxxla-mystery": "unknown-artefacts",
    "unknown-artefacts": None,  # Top-level Story Arc

    # Other
    "hip87621-conflict": "alliance-expansion",
    "marlinist-refugee": "nmla-terrorism",
    "inra-exposed": "nmla-terrorism",
    "nmla-terrorism": None,  # Top-level Story Arc
}


def main():
    updated = 0
    for arc_file in ARCS_DIR.glob("*.md"):
        arc_id = arc_file.stem
        parent = PARENT_MAP.get(arc_id)

        content = arc_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        if len(parts) < 3:
            continue
        try:
            fm = yaml.safe_load(parts[1])
        except Exception:
            continue

        changed = False
        if parent is not None:
            fm["parent_arc"] = parent
            changed = True
        elif "parent_arc" in fm:
            del fm["parent_arc"]
            changed = True

        if changed:
            new_fm = yaml.dump(fm, default_flow_style=False, allow_unicode=True, sort_keys=False)
            new_content = f"---\n{new_fm}---\n{parts[2]}"
            arc_file.write_text(new_content, encoding="utf-8")
            updated += 1

    print(f"Updated {updated} arc files with parent_arc hierarchy")


if __name__ == "__main__":
    main()
