#!/usr/bin/env python3
"""
sync_audio_to_r2.py — Upload GalNet audio MP3s to Cloudflare R2.
Uses Cloudflare REST API. Skips files already present in R2 (by size check).
"""
import argparse
import hashlib
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
    resp = requests.put(url, headers={"Authorization": f"Bearer {token}"}, json={})
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
    )
    list_resp.raise_for_status()
    buckets = list_resp.json().get("result", {}).get("buckets", [])
    if any(b["name"] == BUCKET_NAME for b in buckets):
        print(f"  Bucket '{BUCKET_NAME}' already exists")
        return False
    resp.raise_for_status()
    return True


def list_r2_objects(token: str, account_id: str) -> dict[str, int]:
    """Return mapping of object key -> size for all objects in bucket."""
    objects: dict[str, int] = {}
    cursor = None
    while True:
        url = f"{API_BASE}/accounts/{account_id}/r2/buckets/{BUCKET_NAME}/objects"
        params = {"limit": 1000}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            params=params,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success"):
            raise RuntimeError(f"Failed to list objects: {data}")
        result = data.get("result", [])
        # result can be a list (empty bucket) or a dict with objects
        if isinstance(result, list):
            for obj in result:
                objects[obj["key"]] = obj["size"]
            break  # no pagination for list response
        for obj in result.get("objects", []):
            objects[obj["key"]] = obj["size"]
        if not result.get("truncated", False):
            break
        cursor = result.get("cursor")
    return objects


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
    r2_objects = list_r2_objects(token, account_id)
    print(f"  R2 objects:  {len(r2_objects)}")

    to_upload = []
    for fpath in local_files:
        key = f"audio/{fpath.name}"
        local_size = fpath.stat().st_size
        r2_info = r2_objects.get(key)
        if r2_info is None:
            to_upload.append((key, fpath))
            continue
        r2_size, r2_etag = r2_info
        if r2_size != local_size:
            to_upload.append((key, fpath))
            continue
        # Size matches — check MD5 vs etag to catch edge-tts regeneration drift
        local_md5 = md5_file(fpath)
        if local_md5 != r2_etag:
            print(f"    {key}: size matches but MD5 differs (local={local_md5}, r2={r2_etag})")
            to_upload.append((key, fpath))
            continue

    print(f"Files to upload: {len(to_upload)}")

    if args.check:
        if len(to_upload) == 0:
            print("✅ All audio files are present in R2.")
            sys.exit(0)
        else:
            print(f"⚠️  {len(to_upload)} files missing or different in R2.")
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

    uploaded = failed = skipped = 0
    for i, (key, fpath) in enumerate(to_upload, 1):
        print(f"  [{i}/{len(to_upload)}] Uploading {key} ...", end="", flush=True)
        if upload_file(token, account_id, key, fpath):
            print(" OK")
            uploaded += 1
        else:
            print(" FAIL")
            failed += 1

    print(f"\nDone: {uploaded} uploaded, {failed} failed, {skipped} skipped")
    print(f"Total in R2: {len(r2_objects) + uploaded} objects")
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
