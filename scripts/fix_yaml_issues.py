#!/usr/bin/env python3
"""Fix YAML syntax issues in agent-edited files."""

import re
from pathlib import Path
import yaml


def fix_modern_impact_line(line: str) -> str:
    """Fix modern_impact lines that contain unescaped double quotes."""
    prefix = "modern_impact:"
    if not line.strip().startswith(prefix):
        return line

    value = line[len(prefix):].strip()

    # If the value starts and ends with " and parses as a clean string, leave it
    if value.startswith('"') and value.endswith('"') and value.count('"') == 2:
        return line

    # If the value contains any " characters, wrap the whole thing in double quotes
    # and escape internal double quotes
    if '"' in value:
        # Escape internal double quotes
        escaped = value.replace('"', '\\"')
        return f'{prefix} "{escaped}"'

    return line


def fix_inline_list_line(line: str) -> list:
    """Fix inline list syntax like 'locations: - Marlinist'."""
    m = re.match(r"^(\s*)(\w+):\s+-\s+(.+)$", line)
    if not m:
        return [line]
    indent = m.group(1)
    key = m.group(2)
    rest = m.group(3).strip()
    result = [f"{indent}{key}:"]
    for item in [x.strip() for x in rest.split(",")]:
        if item:
            result.append(f"{indent}  - {item}")
    return result


def fix_alias_line(line: str) -> str:
    """Fix lines where the value starts with * (YAML alias indicator)."""
    m = re.match(r"^(\s*\w+:\s*)(\*.*)$", line)
    if m:
        return f'{m.group(1)}"{m.group(2)}"'
    return line


def fix_file(path: Path) -> bool:
    """Fix known YAML syntax issues. Returns True if modified."""
    content = path.read_text()
    if not content.startswith("---"):
        return False

    parts = content.split("---", 2)
    if len(parts) < 3:
        return False

    frontmatter = parts[1]
    body = parts[2]
    modified = False

    lines = frontmatter.split("\n")
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Fix inline list syntax
        if re.match(r"^\s*(locations|groups|topics|persons|entities|related_uuids):\s+-\s+", line):
            fixed = fix_inline_list_line(line)
            new_lines.extend(fixed)
            if fixed != [line]:
                modified = True
            i += 1
            continue

        # Fix modern_impact with unescaped quotes
        if line.strip().startswith("modern_impact:"):
            fixed = fix_modern_impact_line(line)
            if fixed != line:
                modified = True
            new_lines.append(fixed)
            i += 1
            continue

        # Fix alias lines (values starting with *)
        if re.match(r"^\s*(summary|player_impact):\s*\*", line):
            fixed = fix_alias_line(line)
            if fixed != line:
                modified = True
            new_lines.append(fixed)
            i += 1
            continue

        new_lines.append(line)
        i += 1

    if not modified:
        return False

    new_frontmatter = "\n".join(new_lines)

    # Validate
    try:
        yaml.safe_load(new_frontmatter)
    except yaml.YAMLError as e:
        print(f"  STILL BROKEN: {path}")
        print(f"    {e}")
        return False

    new_content = f"---{new_frontmatter}---{body}"
    path.write_text(new_content)
    return True


def main():
    root = Path("Archive")
    fixed = 0
    still_broken = []

    for year_dir in sorted(root.iterdir()):
        if not year_dir.is_dir():
            continue
        for month_dir in sorted(year_dir.iterdir()):
            if not month_dir.is_dir():
                continue
            for md_file in sorted(month_dir.glob("*.md")):
                try:
                    content = md_file.read_text()
                    if not content.startswith("---"):
                        continue
                    parts = content.split("---", 2)
                    if len(parts) < 3:
                        continue
                    yaml.safe_load(parts[1])
                except yaml.YAMLError:
                    if fix_file(md_file):
                        fixed += 1
                    else:
                        still_broken.append(str(md_file))

    print(f"Fixed {fixed} files.")
    if still_broken:
        print(f"Still broken: {len(still_broken)}")
        for f in still_broken:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
