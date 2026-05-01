#!/usr/bin/env python3
"""Remove all [[ ]] wikilink brackets from article markdown files."""

import glob
import sys


def remove_wikilinks(path_pattern: str) -> int:
    count = 0
    files = glob.glob(path_pattern, recursive=True)
    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            text = f.read()

        if "[[" not in text and "]]" not in text:
            continue

        new_text = text.replace("[[", "").replace("]]", "")

        if new_text != text:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_text)
            count += 1

    return count


if __name__ == "__main__":
    archive_count = remove_wikilinks("Archive/**/*.md")
    galnet_count = remove_wikilinks("GalNet/**/*.md")
    print(f"Processed {archive_count} Archive files and {galnet_count} GalNet files")
