#!/usr/bin/env python3
"""
generate_audio.py — Incremental TTS audio generation for GalNet articles.
Uses edge-tts with en-GB-SoniaNeural voice. Parallel processing for speed.
"""
import argparse
import asyncio
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import yaml
import edge_tts

BASE_DIR = Path(__file__).parent.parent
ARCHIVE_DIR = BASE_DIR / "Archive"
AUDIO_DIR = BASE_DIR / "website" / "public" / "audio"
MANIFEST_PATH = BASE_DIR / "scripts" / "audio_manifest.json"
VOICE = "en-GB-SoniaNeural"
CONCURRENCY = 8

AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def parse_frontmatter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    try:
        return yaml.safe_load(parts[1].strip()) or {}
    except yaml.YAMLError:
        return None


def extract_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    return parts[2] if len(parts) >= 3 else ""


def sanitize_for_tts(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    text = re.sub(r'\*([^*]+)\*', r'\1', text)
    text = re.sub(r'__([^_]+)__', r'\1', text)
    text = re.sub(r'_([^_]+)_', r'\1', text)
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^---+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^>\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^[\*\-\+]\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\d+\.\s+', '', text, flags=re.MULTILINE)
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'https?://\S+', '', text)
    text = re.sub(r'!\[([^\]]*)\]\([^)]+\)', '', text)
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\*\*Pilots Federation ALERT\*\*', 'Pilots Federation Alert.', text, flags=re.IGNORECASE)
    text = re.sub(r'\bALERT\b', 'Alert', text)
    text = text.replace(' & ', ' and ')
    text = text.replace('—', '-').replace('–', '-')
    text = text.replace('|', '').replace('~', '').replace('^', '')
    return text.strip()


def build_tts_text(fm: dict, body: str) -> str:
    title = fm.get("title", "Untitled")
    date = fm.get("date", "")
    arc_id = fm.get("arc_id")
    player_impact = fm.get("player_impact", "")
    modern_impact = fm.get("modern_impact", "")
    
    clean_body = sanitize_for_tts(body)
    parts = [f"{title} on {date}.", clean_body]
    
    outro_parts = []
    if arc_id:
        outro_parts.append(f"Arc: {arc_id.replace('-', ' ').title()}.")
    if player_impact:
        outro_parts.append(f"Player impact: {sanitize_for_tts(player_impact)}")
    if modern_impact:
        outro_parts.append(f"Future impact: {sanitize_for_tts(modern_impact)}")
    
    if outro_parts:
        parts.append("AI analysis. " + " ".join(outro_parts))
    
    return "\n\n".join(parts)


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


async def generate_one(uuid: str, text: str, output_path: Path, semaphore: asyncio.Semaphore) -> tuple[str, bool]:
    async with semaphore:
        try:
            communicate = edge_tts.Communicate(text, voice=VOICE)
            await communicate.save(str(output_path))
            return uuid, True
        except Exception as e:
            print(f"  ERROR {uuid}: {e}", file=sys.stderr)
            return uuid, False


async def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio for GalNet articles")
    parser.add_argument("--batch-size", type=int, default=0, help="Max articles to generate (0 = all)")
    parser.add_argument("--sort", choices=["recent", "oldest"], default="oldest", help="Process order")
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY, help="Parallel requests")
    parser.add_argument("--max-runtime", type=int, default=0, help="Max runtime in seconds (0 = no limit)")
    args = parser.parse_args()
    
    manifest = {}
    if MANIFEST_PATH.exists():
        manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    
    articles = []
    for md_file in ARCHIVE_DIR.rglob("*.md"):
        fm = parse_frontmatter(md_file)
        if not fm or not fm.get("uuid"):
            continue
        articles.append((fm.get("uuid"), fm, extract_body(md_file)))
    
    print(f"Found {len(articles)} articles. Manifest has {len(manifest)} entries.")
    
    # Sort by date
    reverse = args.sort == "recent"
    articles.sort(key=lambda x: str(x[1].get("date", "")), reverse=reverse)
    
    # Build work queue
    queue = []
    missing_files = 0
    for uuid, fm, body in articles:
        tts_text = build_tts_text(fm, body)
        text_hash = compute_hash(tts_text)
        output_path = AUDIO_DIR / f"{uuid}.mp3"
        if manifest.get(uuid) == text_hash and output_path.exists():
            continue
        if manifest.get(uuid) == text_hash and not output_path.exists():
            missing_files += 1
        
        if len(tts_text) > 4500:
            intro = f"{fm.get('title', 'Untitled')} on {fm.get('date', '')}."
            outro_parts = []
            arc_id = fm.get("arc_id")
            player_impact = fm.get("player_impact", "")
            modern_impact = fm.get("modern_impact", "")
            if arc_id:
                outro_parts.append(f"Arc: {arc_id.replace('-', ' ').title()}.")
            if player_impact:
                outro_parts.append(f"Player impact: {sanitize_for_tts(player_impact)}")
            if modern_impact:
                outro_parts.append(f"Future impact: {sanitize_for_tts(modern_impact)}")
            outro = "AI analysis. " + " ".join(outro_parts) if outro_parts else ""
            max_body = max(100, 4500 - len(intro) - len(outro) - 50)
            clean_body = sanitize_for_tts(body)[:max_body]
            tts_text = f"{intro}\n\n{clean_body}\n\n{outro}".strip()
        
        queue.append((uuid, tts_text, output_path, text_hash))
        
        if args.batch_size > 0 and len(queue) >= args.batch_size:
            break
    
    # Clean up stale manifest entries and MP3s for deleted articles
    valid_uuids = {uuid for uuid, _, _ in articles}
    stale = [u for u in list(manifest.keys()) if u not in valid_uuids]
    removed_mp3s = 0
    for u in stale:
        del manifest[u]
        stale_mp3 = AUDIO_DIR / f"{u}.mp3"
        if stale_mp3.exists():
            stale_mp3.unlink()
            removed_mp3s += 1
    if stale:
        print(f"Removed {len(stale)} stale manifest entries for deleted articles")
        if removed_mp3s:
            print(f"  Also removed {removed_mp3s} stale MP3 files")
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(f"Need to generate: {len(queue)} articles (skipped {len(articles) - len(queue)})")
    if missing_files:
        print(f"  ({missing_files} had manifest entries but missing MP3 files)")
    if not queue:
        print("Nothing to do — all audio up to date.")
        return
    
    start_time = time.monotonic()
    semaphore = asyncio.Semaphore(args.concurrency)
    generated = failed = 0
    
    batch_size = 50
    for i in range(0, len(queue), batch_size):
        batch = queue[i:i+batch_size]
        tasks = [generate_one(uuid, text, path, semaphore) for uuid, text, path, _ in batch]
        results = await asyncio.gather(*tasks)
        
        for (uuid, _, _, text_hash), (result_uuid, success) in zip(batch, results):
            if success:
                manifest[result_uuid] = text_hash
                generated += 1
            else:
                failed += 1
        
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        total_done = len([u for u, h in manifest.items() if any(u == q[0] for q in queue)])
        print(f"  Batch {i//batch_size + 1}/{(len(queue) + batch_size - 1)//batch_size}: "
              f"{generated} generated, {failed} failed")
        
        if args.max_runtime > 0:
            elapsed = time.monotonic() - start_time
            if elapsed >= args.max_runtime:
                remaining = len(queue) - (generated + failed)
                print(f"\n⏱️  Runtime limit reached ({int(elapsed)}s). "
                      f"{remaining} articles remaining for next run.")
                break
    
    print(f"\nDone: {generated} generated, {failed} failed")
    print(f"Audio files: {len(manifest)} in manifest, {len(list(AUDIO_DIR.glob('*.mp3')))} on disk")


if __name__ == "__main__":
    asyncio.run(main())
