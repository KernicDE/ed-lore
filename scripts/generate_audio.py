#!/usr/bin/env python3
"""
generate_audio.py — Incremental TTS audio generation for GalNet articles.
Uses edge-tts. Supports English (en-GB-SoniaNeural) and German
(de-DE-KatjaNeural, articles with body_de only). Parallel processing.
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
COMMUNITY_DIR = BASE_DIR / "Community"
CHRONICLES_DIR = COMMUNITY_DIR / "chronicles"
AUDIO_DIR = BASE_DIR / "website" / "public" / "audio"
AUDIO_DIR_DE = BASE_DIR / "website" / "public" / "audio-de"
MANIFEST_PATH = BASE_DIR / "scripts" / "audio_manifest.json"
MANIFEST_DE_PATH = BASE_DIR / "scripts" / "audio_manifest_de.json"
CONCURRENCY = 8

# Per-language configuration. DE audio is generated from the `body_de`
# frontmatter field and stored in a parallel manifest/directory so the
# English pipeline stays byte-for-byte unchanged.
LANG_CONFIG = {
    "en": {
        "lang": "en",
        "voice": "en-GB-SoniaNeural",
        "manifest": MANIFEST_PATH,
        "audio_dir": AUDIO_DIR,
        "date_joiner": "on",
        "analysis_label": "AI analysis.",
        "player_impact_label": "Player impact:",
        "modern_impact_label": "Future impact:",
    },
    "de": {
        "lang": "de",
        "voice": "de-DE-KatjaNeural",
        "manifest": MANIFEST_DE_PATH,
        "audio_dir": AUDIO_DIR_DE,
        "date_joiner": "vom",
        "analysis_label": "KI-Analyse.",
        "player_impact_label": "Auswirkung für Piloten:",
        "modern_impact_label": "Zukünftige Bedeutung:",
    },
}

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR_DE.mkdir(parents=True, exist_ok=True)


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


def build_tts_text(fm: dict, body: str, cfg: dict) -> str:
    title = fm.get("title", "Untitled")
    date = fm.get("date", "")
    arc_id = fm.get("arc_id")
    # DE runs prefer the translated *_de impact fields, falling back to EN
    impact_suffix = "_de" if cfg["lang"] == "de" else ""
    player_impact = fm.get(f"player_impact{impact_suffix}") or fm.get("player_impact", "")
    modern_impact = fm.get(f"modern_impact{impact_suffix}") or fm.get("modern_impact", "")

    clean_body = sanitize_for_tts(body)
    parts = [f"{title} {cfg['date_joiner']} {date}.", clean_body]

    outro_parts = []
    if arc_id:
        outro_parts.append(f"Arc: {arc_id.replace('-', ' ').title()}.")
    if player_impact:
        outro_parts.append(f"{cfg['player_impact_label']} {sanitize_for_tts(player_impact)}")
    if modern_impact:
        outro_parts.append(f"{cfg['modern_impact_label']} {sanitize_for_tts(modern_impact)}")

    if outro_parts:
        parts.append(cfg["analysis_label"] + " " + " ".join(outro_parts))

    tts_text = "\n\n".join(parts)

    if len(tts_text) > 4500:
        intro = f"{title} {cfg['date_joiner']} {date}."
        outro = cfg["analysis_label"] + " " + " ".join(outro_parts) if outro_parts else ""
        max_body = max(100, 4500 - len(intro) - len(outro) - 50)
        tts_text = f"{intro}\n\n{sanitize_for_tts(body)[:max_body]}\n\n{outro}".strip()

    return tts_text


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


async def generate_one(uuid: str, text: str, output_path: Path, semaphore: asyncio.Semaphore, voice: str) -> tuple[str, bool]:
    async with semaphore:
        try:
            communicate = edge_tts.Communicate(text, voice=voice)
            await communicate.save(str(output_path))
            return uuid, True
        except Exception as e:
            print(f"  ERROR {uuid}: {e}", file=sys.stderr)
            # Remove partial/empty output so a failed run can't leave a
            # corrupt MP3 behind for the sync step to upload.
            if output_path.exists():
                try:
                    output_path.unlink()
                except OSError:
                    pass
            return uuid, False


async def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio for GalNet articles")
    parser.add_argument("--lang", choices=["en", "de"], default="en",
                        help="Language to generate (de = articles with body_de only)")
    parser.add_argument("--batch-size", type=int, default=0, help="Max articles to generate (0 = all)")
    parser.add_argument("--sort", choices=["recent", "oldest"], default="oldest", help="Process order")
    parser.add_argument("--concurrency", type=int, default=CONCURRENCY, help="Parallel requests")
    parser.add_argument("--max-runtime", type=int, default=0, help="Max runtime in seconds (0 = no limit)")
    args = parser.parse_args()

    cfg = LANG_CONFIG[args.lang]
    voice = cfg["voice"]
    manifest_path = cfg["manifest"]
    audio_dir = cfg["audio_dir"]

    manifest = {}
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    articles = []
    for md_file in ARCHIVE_DIR.rglob("*.md"):
        fm = parse_frontmatter(md_file)
        if not fm or not fm.get("uuid"):
            continue
        if args.lang == "de":
            body_de = (fm.get("body_de") or "").strip()
            if not body_de:
                continue
            articles.append((fm.get("uuid"), fm, body_de))
        else:
            articles.append((fm.get("uuid"), fm, extract_body(md_file)))

    if CHRONICLES_DIR.exists():
        for md_file in CHRONICLES_DIR.rglob("*.md"):
            fm = parse_frontmatter(md_file)
            if not fm or not fm.get("uuid"):
                continue
            if args.lang == "de":
                body_de = (fm.get("body_de") or "").strip()
                if not body_de:
                    continue
                articles.append((fm.get("uuid"), fm, body_de))
            else:
                articles.append((fm.get("uuid"), fm, extract_body(md_file)))

    print(f"[{args.lang}] Found {len(articles)} articles. Manifest has {len(manifest)} entries.")

    # Sort by date
    reverse = args.sort == "recent"
    articles.sort(key=lambda x: str(x[1].get("date", "")), reverse=reverse)

    # Build work queue
    queue = []
    missing_files = 0
    for uuid, fm, body in articles:
        tts_text = build_tts_text(fm, body, cfg)
        text_hash = compute_hash(tts_text)
        output_path = audio_dir / f"{uuid}.mp3"
        if manifest.get(uuid) == text_hash and output_path.exists():
            continue
        if manifest.get(uuid) == text_hash and not output_path.exists():
            missing_files += 1

        queue.append((uuid, tts_text, output_path, text_hash))

        if args.batch_size > 0 and len(queue) >= args.batch_size:
            break

    # Clean up stale manifest entries and MP3s for deleted articles
    valid_uuids = {uuid for uuid, _, _ in articles}
    stale = [u for u in list(manifest.keys()) if u not in valid_uuids]
    removed_mp3s = 0
    for u in stale:
        del manifest[u]
        stale_mp3 = audio_dir / f"{u}.mp3"
        if stale_mp3.exists():
            stale_mp3.unlink()
            removed_mp3s += 1
    if stale:
        print(f"Removed {len(stale)} stale manifest entries for deleted articles")
        if removed_mp3s:
            print(f"  Also removed {removed_mp3s} stale MP3 files")
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

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
        tasks = [generate_one(uuid, text, path, semaphore, voice) for uuid, text, path, _ in batch]
        results = await asyncio.gather(*tasks)

        for (uuid, _, _, text_hash), (result_uuid, success) in zip(batch, results):
            if success:
                manifest[result_uuid] = text_hash
                generated += 1
            else:
                failed += 1

        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
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
    print(f"Audio files: {len(manifest)} in manifest, {len(list(audio_dir.glob('*.mp3')))} on disk")


if __name__ == "__main__":
    asyncio.run(main())
