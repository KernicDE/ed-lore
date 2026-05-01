#!/usr/bin/env python3
"""
Normalize formatting across all Archive articles.

Transformations applied:
  1. Enforce canonical YAML frontmatter key order
  2. Strip duplicate title from body text
  3. Collapse 3+ consecutive blank lines to 2
  4. Normalize single-asterisk italic (*text*) to bold (**text**)
  5. Report (but don't fix) mojibake encoding anomalies

Mid-sentence random capitalization is intentionally NOT auto-fixed
(too risky — cannot distinguish proper nouns from OCR artifacts).
"""

import re
from pathlib import Path

import yaml

# Canonical YAML key order. Unknown keys are appended at the end.
CANONICAL_KEY_ORDER = [
    "uuid", "title", "slug", "date", "source",
    "summary", "player_impact",
    "persons", "groups", "locations", "topics", "entities", "technologies",
    "arc_id", "arc_chapter",
    "modern_impact", "legacy_weight", "significance",
    "related_uuids",
]

# Mojibake patterns: UTF-8 bytes decoded as Latin-1
MOJIBAKE_PATTERNS = [
    "â",  # â€™ → '
    "â",  # â€œ → "
    "â",  # â€  → "
    "â",  # â€" → –
    "â",  # â€" → —
    "Ã¶",        # Ã¶ → ö
    "Ã¼",        # Ã¼ → ü
    "Ã¤",        # Ã¤ → ä
]


def reorder_frontmatter(fm: dict) -> dict:
    """Return a new dict with keys in canonical order; unknown keys appended."""
    ordered = {}
    for key in CANONICAL_KEY_ORDER:
        if key in fm:
            ordered[key] = fm[key]
    for key in fm:
        if key not in ordered:
            ordered[key] = fm[key]
    return ordered


def normalize_title(t: str) -> str:
    """Lowercase, strip all punctuation and whitespace for comparison."""
    t = t.lower()
    t = re.sub(r"[^\w]", "", t)  # strip punctuation AND spaces (handles hyphens, apostrophes)
    return t


def strip_duplicate_title(body: str, title: str) -> tuple[str, bool]:
    """
    Remove the title line from the start of the body if it matches
    the frontmatter title (fuzzy: normalized comparison).
    Returns (new_body, changed).
    """
    norm_title = normalize_title(title)
    lines = body.split("\n")

    # Find first non-empty line
    first_nonempty_idx = None
    for i, line in enumerate(lines):
        if line.strip():
            first_nonempty_idx = i
            break

    if first_nonempty_idx is None:
        return body, False

    first_line = lines[first_nonempty_idx].strip()
    if normalize_title(first_line) == norm_title:
        # Remove that line and any immediately following blank lines
        remaining = lines[first_nonempty_idx + 1:]
        # Strip leading blank lines after the removed title
        while remaining and not remaining[0].strip():
            remaining.pop(0)
        return "\n".join(remaining), True

    return body, False


def collapse_blank_lines(body: str) -> tuple[str, bool]:
    """Reduce 3+ consecutive blank lines to 2."""
    new_body = re.sub(r"\n{3,}", "\n\n", body)
    return new_body, new_body != body


def normalize_italics(body: str) -> tuple[str, bool]:
    """Convert *text* (single asterisk) to **text** (bold). Skips **already bold**."""
    # Content must start with a non-whitespace char to avoid matching `* *`
    pattern = re.compile(r"(?<!\*)\*(\S[^*\n]*)\*(?!\*)")
    new_body = pattern.sub(r"**\1**", body)
    return new_body, new_body != body


def has_mojibake(text: str) -> bool:
    return any(pat in text for pat in MOJIBAKE_PATTERNS)


def dump_frontmatter(fm: dict) -> str:
    """Serialize frontmatter preserving list style and string quoting."""
    return yaml.dump(
        fm,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=10000,
    )


def process_file(path: Path, dry_run: bool = False) -> dict:
    """Process one file. Returns a dict describing changes made."""
    content = path.read_text(encoding="utf-8")

    if not content.startswith("---"):
        return {}

    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}

    raw_frontmatter = parts[1]
    body = parts[2]

    try:
        fm = yaml.safe_load(raw_frontmatter)
    except yaml.YAMLError as e:
        return {"error": str(e)}

    if not isinstance(fm, dict):
        return {}

    changes = {}

    # 0. Ensure body starts with a blank line after closing ---
    if not body.startswith("\n"):
        body = "\n\n" + body
        changes["body_separator_fixed"] = True

    # 1. Reorder YAML keys
    ordered_fm = reorder_frontmatter(fm)
    if list(ordered_fm.keys()) != list(fm.keys()):
        changes["yaml_reordered"] = True
        fm = ordered_fm

    # 2. Strip duplicate title from body
    title = fm.get("title", "")
    if title:
        new_body, changed = strip_duplicate_title(body, title)
        if changed:
            changes["title_stripped"] = True
            body = new_body

    # 3. Collapse blank lines
    new_body, changed = collapse_blank_lines(body)
    if changed:
        changes["blank_lines_collapsed"] = True
        body = new_body

    # 4. Normalize italics in body
    new_body, changed = normalize_italics(body)
    if changed:
        changes["italics_normalized"] = True
        body = new_body

    # 5. Report mojibake
    if has_mojibake(body) or has_mojibake(raw_frontmatter):
        changes["mojibake_detected"] = True

    if not changes:
        return {}

    if not dry_run and set(changes.keys()) - {"mojibake_detected"}:
        new_frontmatter = dump_frontmatter(fm)
        new_content = f"---\n{new_frontmatter}---{body}"
        path.write_text(new_content, encoding="utf-8")

    return changes


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Format all Archive articles.")
    parser.add_argument("--dry-run", action="store_true", help="Report without writing")
    parser.add_argument("--sample", type=int, default=0, help="Process only N files")
    parser.add_argument("path", nargs="?", default="Archive", help="Root path")
    args = parser.parse_args()

    root = Path(args.path)
    files = sorted(root.rglob("*.md"))
    if args.sample:
        files = files[: args.sample]

    stats = {
        "yaml_reordered": 0,
        "title_stripped": 0,
        "blank_lines_collapsed": 0,
        "italics_normalized": 0,
        "mojibake_detected": 0,
        "errors": 0,
        "total": 0,
    }
    mojibake_files = []

    for path in files:
        result = process_file(path, dry_run=args.dry_run)
        if not result:
            continue
        if result.get("error"):
            stats["errors"] += 1
            print(f"  ERROR {path}: {result['error']}")
            continue  # don't count errors as modifications
        stats["total"] += 1
        for key in stats:
            if key in result:
                stats[key] += 1
        if result.get("mojibake_detected"):
            mojibake_files.append(str(path))
        if args.dry_run or args.sample:
            tag = "[DRY]" if args.dry_run else ""
            applied = [k for k in result if k not in ("error", "body_separator_fixed")]
            print(f"  {tag} {path.name}: {', '.join(applied)}")

    print(f"\nFiles modified:          {stats['total']}")
    print(f"  YAML reordered:        {stats['yaml_reordered']}")
    print(f"  Duplicate title strip: {stats['title_stripped']}")
    print(f"  Blank lines collapsed: {stats['blank_lines_collapsed']}")
    print(f"  Italics normalized:    {stats['italics_normalized']}")
    print(f"  Mojibake detected:     {stats['mojibake_detected']} (not auto-fixed)")
    if stats["errors"]:
        print(f"  Errors:                {stats['errors']}")
    if mojibake_files:
        print("\nFiles with possible mojibake:")
        for f in mojibake_files[:20]:
            print(f"  {f}")
        if len(mojibake_files) > 20:
            print(f"  ... and {len(mojibake_files) - 20} more")


if __name__ == "__main__":
    main()
