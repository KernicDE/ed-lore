#!/usr/bin/env python3
"""
sync_audio_to_r2.py — Upload GalNet audio MP3s to Cloudflare R2.
Uses Cloudflare REST API. Skips files already present in R2 (by UUID key).
Since audio files are named by article UUID and generate_audio.py handles
regeneration when content changes, we only need to check existence in R2.
"""
import argparse
import json
import os
import sys
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent.parent
AUDIO_DIR = BASE_DIR / "website" / "public" / "audio"
BUCKET_NAME = "ed-lore-audio"
API_BASE = "https://api.cloudflare.com/client/v4"


def get_account_id(token: str) -> str:
    resp = requests.get(
        f"{API_BASE}/accounts",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"Failed to list accounts: {data}")
    accounts = data["result"]
    if not accounts:
        raise RuntimeError("No Cloudflare accounts found for this token.")
    return accounts[0]["id"]


def ensure_bucket(token: str, account_id: str) -> bool:
    """Create bucket if it doesn't exist. Returns True if created."""
    url = f"{API_BASE}/accounts/{account_id}/r2/buckets/{BUCKET_NAME}"
    resp = requests.put(url, headers={"Authorization": f"Bearer {token}"}, json={}, timeout=30)
    if resp.status_code == 200:
        print(f"  Created bucket '{BUCKET_NAME}'")
        return True
    if resp.status_code == 400 and "already exists" in resp.text.lower():
        print(f"  Bucket '{BUCKET_NAME}' already exists")
        return False
    # Some other error — check if bucket exists via list
    list_resp = requests.get(
        f"{API_BASE}/accounts/{account_id}/r2/buckets",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    list_resp.raise_for_status()
    buckets = list_resp.json().get("result", {}).get("buckets", [])
    if any(b["name"] == BUCKET_NAME for b in buckets):
        print(f"  Bucket '{BUCKET_NAME}' already exists")
        return False
    resp.raise_for_status()
    return True


def list_r2_keys(token: str, account_id: str) -> set[str]:
    """Return set of all object keys in bucket."""
    keys: set[str] = set()
    cursor = None
    page = 0
    while True:
        page += 1
        url = f"{API_BASE}/accounts/{account_id}/r2/buckets/{BUCKET_NAME}/objects"
        params = {"per_page": 1000}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Failed to list objects: {data}")

        result = data.get("result", [])
        result_info = data.get("result_info", {})

        # Cloudflare returns either a list of objects or a dict with {objects, truncated, cursor}
        if isinstance(result, list):
            objects = result
        else:
            objects = result.get("objects", [])

        for obj in objects:
            keys.add(obj["key"])

        print(f"  Listed page {page}: {len(objects)} objects (total: {len(keys)})")

        # Determine next cursor — check both response formats
        next_cursor = None
        if result_info.get("cursor"):
            next_cursor = result_info["cursor"]
        elif isinstance(result, dict) and result.get("cursor"):
            next_cursor = result["cursor"]

        # Check if there are more pages
        has_more = False
        if result_info.get("cursor"):
            has_more = True
        elif isinstance(result, dict) and result.get("truncated", False):
            has_more = True
        elif len(objects) == 1000:
            has_more = True  # fallback: full page likely means more

        if not has_more or not next_cursor:
            break
        cursor = next_cursor

    return keys


def upload_file(token: str, account_id: str, key: str, file_path: Path) -> bool:
    url = f"{API_BASE}/accounts/{account_id}/r2/buckets/{BUCKET_NAME}/objects/{key}"
    with open(file_path, "rb") as f:
        resp = requests.put(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "audio/mpeg",
            },
            data=f,
            timeout=300,
        )
    if resp.status_code == 200:
        return True
    print(f"    Upload failed: {resp.status_code} {resp.text[:200]}", file=sys.stderr)
    return False


def main():
    parser = argparse.ArgumentParser(description="Sync GalNet audio to Cloudflare R2")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually upload")
    parser.add_argument("--check", action="store_true", help="Only check coverage, don't upload")
    args = parser.parse_args()

    token = os.environ.get("CLOUDFLARE_R2_TOKEN")
    if not token:
        print("ERROR: CLOUDFLARE_R2_TOKEN environment variable not set", file=sys.stderr)
        sys.exit(1)

    print("=== Sync Audio to Cloudflare R2 ===")
    print(f"Fetching Cloudflare account...")
    account_id = get_account_id(token)
    print(f"  Account ID: {account_id}")

    print(f"Ensuring bucket '{BUCKET_NAME}'...")
    ensure_bucket(token, account_id)

    print("Listing local MP3 files...")
    local_files = sorted(AUDIO_DIR.glob("*.mp3"))
    if not local_files:
        print("ERROR: No MP3 files found in website/public/audio/", file=sys.stderr)
        sys.exit(1)
    print(f"  Local files: {len(local_files)}")

    print("Listing R2 objects...")
    r2_keys = list_r2_keys(token, account_id)
    print(f"  R2 objects:  {len(r2_keys)}")
    if r2_keys:
        sample = sorted(r2_keys)[:5]
        print(f"  Sample keys: {sample}")
    else:
        print("  WARNING: R2 bucket appears empty!")

    to_upload = []
    for fpath in local_files:
        key = f"audio/{fpath.name}"
        if key not in r2_keys:
            to_upload.append((key, fpath))

    print(f"Files to upload: {len(to_upload)}")

    if args.check:
        if len(to_upload) == 0:
            print("✅ All audio files are present in R2.")
            sys.exit(0)
        else:
            print(f"⚠️  {len(to_upload)} files missing in R2.")
            sys.exit(1)

    if args.dry_run:
        print("Dry run — would upload:")
        for key, fpath in to_upload[:10]:
            print(f"  {key} ({fpath.stat().st_size} bytes)")
        if len(to_upload) > 10:
            print(f"  ... and {len(to_upload) - 10} more")
        return

    if not to_upload:
        print("✅ Nothing to upload — all files already in R2.")
        return

    uploaded = failed = 0
    for i, (key, fpath) in enumerate(to_upload, 1):
        print(f"  [{i}/{len(to_upload)}] Uploading {key} ...", end="", flush=True)
        if upload_file(token, account_id, key, fpath):
            print(" OK")
            uploaded += 1
        else:
            print(" FAIL")
            failed += 1

    print(f"\nDone: {uploaded} uploaded, {failed} failed")
    print(f"Total in R2: {len(r2_keys) + uploaded} objects")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
