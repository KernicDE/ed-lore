#!/usr/bin/env python3
"""Validate enriched article frontmatter for quality issues."""

import sys
from pathlib import Path
import yaml


def normalize_name(name: str) -> str:
    """Normalize a person name for deduplication."""
    n = name.lower().strip()
    # Remove common titles
    for title in ["professor ", "dr ", "admiral ", "captain ", "commander ",
                  "senator ", "president ", "shadow president ", "vice president ",
                  "prime minister ", "deputy prime minister ", "executive agent ",
                  "ms ", "mr ", "mrs ", "miss ", "sir ", "lady ", "lord ",
                  "emperor ", "empress ", "princess ", "prince ", "archduke ",
                  "countess ", "count ", "king ", "queen ", "first apostle ",
                  "grand attorney ", "secretary of state ", "secretary of security "]:
        if n.startswith(title):
            n = n[len(title):]
    return n.strip()


def find_duplicate_persons(persons: list) -> list:
    """Find duplicate persons by normalized name."""
    seen = {}
    dups = []
    for p in persons:
        norm = normalize_name(p)
        if norm in seen:
            dups.append((p, seen[norm]))
        else:
            seen[norm] = p
    return dups


def find_duplicate_groups(groups: list) -> list:
    """Find duplicate groups (case-insensitive, normalized)."""
    seen = {}
    dups = []
    for g in groups:
        norm = g.lower().strip().replace(" corp", " corporation")
        if norm in seen:
            dups.append((g, seen[norm]))
        else:
            seen[norm] = g
    return dups


def validate_file(path: Path) -> list:
    """Return list of issues found in a file."""
    issues = []
    try:
        content = path.read_text()
        # Split frontmatter from body
        if not content.startswith("---"):
            return [(str(path), "No frontmatter")]
        parts = content.split("---", 2)
        if len(parts) < 3:
            return [(str(path), "Malformed frontmatter")]
        fm = yaml.safe_load(parts[1])
        if not fm:
            return [(str(path), "Empty frontmatter")]

        # Check for enrichment fields
        if "summary" not in fm:
            issues.append((str(path), "Missing 'summary' field"))
        if "player_impact" not in fm:
            issues.append((str(path), "Missing 'player_impact' field"))
        if "modern_impact" not in fm:
            issues.append((str(path), "Missing 'modern_impact' field"))

        # Check persons deduplication
        persons = fm.get("persons", []) or []
        dups = find_duplicate_persons(persons)
        for dup, orig in dups:
            issues.append((str(path), f"Duplicate person: '{dup}' (same as '{orig}')"))

        # Check groups deduplication
        groups = fm.get("groups", []) or []
        dups = find_duplicate_groups(groups)
        for dup, orig in dups:
            issues.append((str(path), f"Duplicate group: '{dup}' (same as '{orig}')"))

        # Check for partial names in persons (single word that looks like a fragment)
        for p in persons:
            if len(p.split()) == 1 and len(p) < 5 and p not in ["Seo", "Ram", "Li", "Wu", "Du"]:
                issues.append((str(path), f"Possible partial person name: '{p}'"))

        # Check modern_impact truncation
        mi = fm.get("modern_impact", "")
        if mi and not mi.endswith('"') and not mi.endswith("'") and not mi.endswith(".") and not mi.endswith(")") and not mi.endswith("?") and not mi.endswith("!"):
            issues.append((str(path), f"modern_impact may be truncated (ends with: '{mi[-20:]}')"))

        # Check entities were cleaned
        entities = fm.get("entities", []) or []
        for e in entities:
            e_lower = e.lower()
            if "provided" in e_lower or "confirmed" in e_lower or "argued" in e_lower or "gave" in e_lower or "delivered" in e_lower:
                issues.append((str(path), f"Malformed entity (contains verb): '{e}'"))

        # Check related_uuids for arc articles (warn only for large arcs)
        arc_id = fm.get("arc_id")
        related = fm.get("related_uuids", []) or []
        if arc_id and arc_id != "null" and not related:
            issues.append((str(path), f"[WARN] Has arc_id '{arc_id}' but empty related_uuids"))

        # Check topics are reasonable
        topics = fm.get("topics", []) or []
        if len(topics) == 0:
            issues.append((str(path), "No topics"))
        bad_topics = [t for t in topics if t in ('ship','sport','trade','construction','medicine','safety','treasure hunt')]
        if bad_topics:
            issues.append((str(path), f"Has banned topics: {bad_topics}"))

        # Check locations for garbage
        locations = fm.get("locations", []) or []
        for loc in locations:
            if loc.lower() in ["aegis", "azimuth", "thargoid", "titan", "act", "nmla"]:
                issues.append((str(path), f"Bad location: '{loc}'"))
            if "shortening" in loc.lower() or "the number of" in loc.lower() or "as i jumped" in loc.lower() or "federation preventing" in loc.lower():
                issues.append((str(path), f"Garbage location: '{loc}'"))

    except yaml.YAMLError as e:
        issues.append((str(path), f"YAML error: {e}"))
    except Exception as e:
        issues.append((str(path), f"Error: {e}"))

    return issues


def main():
    root = Path("Archive")
    all_issues = []
    checked = 0

    for year_dir in sorted(root.iterdir()):
        if not year_dir.is_dir():
            continue
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for md_file in sorted(month_dir.glob("*.md")):
                checked += 1
                issues = validate_file(md_file)
                all_issues.extend(issues)

    print(f"Checked {checked} articles. Found {len(all_issues)} issues.")
    print()

    # Group by file
    by_file = {}
    for path, issue in all_issues:
        by_file.setdefault(path, []).append(issue)

    for path, issues in sorted(by_file.items()):
        print(f"\n{path}:")
        for issue in issues:
            print(f"  - {issue}")

    return 1 if all_issues else 0


if __name__ == "__main__":
    sys.exit(main())
