#!/usr/bin/env python3
"""Fetch all articles from GalNet API and compare against local archive by date+title."""

import asyncio
import yaml
import httpx
import re
from pathlib import Path
from datetime import datetime
from tqdm.asyncio import tqdm

JSON_API_URL = "https://cms.zaonce.net/en-GB/jsonapi/node/galnet_article?sort=-published_at&page[limit]=50"
ARCHIVE_DIR = Path("Archive")
GALNET_DIR = Path("GalNet")


def slugify(text):
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    return re.sub(r'[-\s]+', '_', text).strip('_')


def parse_archive_article(path: Path) -> dict:
    """Extract date and title from archive article frontmatter."""
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {"date": None, "title": None, "path": str(path)}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {"date": None, "title": None, "path": str(path)}
    try:
        fm = yaml.safe_load(parts[1])
        date_val = fm.get("date")
        if hasattr(date_val, 'strftime'):
            date_val = date_val.strftime("%Y-%m-%d")
        return {
            "uuid": fm.get("uuid"),
            "date": date_val,
            "title": fm.get("title"),
            "slug": fm.get("slug"),
            "path": str(path),
        }
    except Exception:
        return {"date": None, "title": None, "path": str(path)}


async def fetch_all_api_articles() -> list:
    """Fetch all articles from the GalNet API."""
    articles = []
    url = JSON_API_URL
    limits = httpx.Limits(max_keepalive_connections=10, max_connections=30)
    async with httpx.AsyncClient(timeout=30.0, limits=limits, follow_redirects=True) as client:
        while url:
            try:
                r = await client.get(url)
                if r.status_code != 200:
                    print(f"API error: {r.status_code} on {url}")
                    break
                data = r.json()
                batch = data.get("data", [])
                if not batch:
                    break
                for art in batch:
                    attr = art["attributes"]
                    date_obj = datetime.fromisoformat(attr["published_at"].replace("Z", "+00:00"))
                    articles.append({
                        "api_uuid": art["id"],
                        "title": attr["title"],
                        "date": date_obj.strftime("%Y-%m-%d"),
                        "ed_date": f"{date_obj.year + 1286}-{date_obj.strftime('%m-%d')}",
                        "body": attr["body"]["value"] if attr.get("body") else "",
                    })
                next_link = data.get("links", {}).get("next")
                url = next_link.get("href") if isinstance(next_link, dict) else next_link
            except Exception as e:
                print(f"Error fetching page: {e}")
                break
    return articles


def scan_archive() -> dict:
    """Scan all archive files and return {(date, slug): article_info}."""
    archive = {}
    for md_file in ARCHIVE_DIR.rglob("*.md"):
        info = parse_archive_article(md_file)
        if info["date"] and info["title"]:
            key = (info["date"], slugify(info["title"]))
            archive[key] = info
    return archive


def main():
    print("Scanning local archive...")
    archive = scan_archive()
    print(f"Local archive: {len(archive)} articles")

    print("\nFetching from GalNet API...")
    api_articles = asyncio.run(fetch_all_api_articles())
    print(f"API returned: {len(api_articles)} articles")

    # Convert API real dates to ED dates for comparison
    def to_ed_date(real_date_str):
        real_year = int(real_date_str.split("-")[0])
        ed_year = real_year + 1286
        return f"{ed_year}-{real_date_str[5:]}"
    
    api_keys = {(to_ed_date(a["date"]), slugify(a["title"])) for a in api_articles}
    archive_keys = set(archive.keys())

    missing_from_archive = api_keys - archive_keys
    missing_from_api = archive_keys - api_keys

    print(f"\n--- COMPARISON ---")
    print(f"In API but missing from archive: {len(missing_from_archive)}")
    print(f"In archive but missing from API: {len(missing_from_api)}")

    # Check date range coverage
    api_dates = sorted({a["date"] for a in api_articles})
    print(f"\nAPI date range: {api_dates[0]} to {api_dates[-1]}")
    arch_dates = sorted({str(k[0]) for k in archive_keys})
    print(f"Archive date range: {arch_dates[0]} to {arch_dates[-1]}")

    def api_key_to_article(date, slug):
        # date is ED date, find matching API article
        real_year = int(date.split("-")[0]) - 1286
        real_date = f"{real_year}-{date[5:]}"
        return next(a for a in api_articles if a["date"] == real_date and slugify(a["title"]) == slug)
    
    if missing_from_archive:
        print(f"\n--- MISSING FROM ARCHIVE (first 30) ---")
        for date, slug in sorted(missing_from_archive)[:30]:
            art = api_key_to_article(date, slug)
            print(f"  {art['ed_date']} | {art['title'][:70]} | {slug}")
        if len(missing_from_archive) > 30:
            print(f"  ... and {len(missing_from_archive) - 30} more")

    if missing_from_api:
        print(f"\n--- MISSING FROM API (first 30) ---")
        for key in sorted(missing_from_api)[:30]:
            info = archive[key]
            print(f"  {info['date']} | {info['title'][:70] if info.get('title') else 'NO TITLE'}")
        if len(missing_from_api) > 30:
            print(f"  ... and {len(missing_from_api) - 30} more")

    # Save missing articles for later processing
    if missing_from_archive:
        with open("missing_from_archive.txt", "w") as f:
            for date, slug in sorted(missing_from_archive):
                art = api_key_to_article(date, slug)
                f.write(f"{art['ed_date']}|{art['title']}|{slug}\n")
        print(f"\nWrote {len(missing_from_archive)} missing article IDs to missing_from_archive.txt")

    return len(missing_from_archive), len(missing_from_api)


if __name__ == "__main__":
    main()
