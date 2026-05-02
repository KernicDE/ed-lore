#!/usr/bin/env python3
"""
generate_audio_local.py — Generate all missing audio files locally.
Checks actual MP3 files on disk (not just manifest), so it works
regardless of whether files were generated on GitHub Actions.
Resumable: skips existing files, generates missing ones.
"""
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

    intro = f"{title} on {date}."
    clean_body = sanitize_for_tts(body)

    outro_parts = []
    if arc_id:
        outro_parts.append(f"Arc: {arc_id.replace('-', ' ').title()}.")
    if player_impact:
        outro_parts.append(f"Player impact: {sanitize_for_tts(player_impact)}")
    if modern_impact:
        outro_parts.append(f"Future impact: {sanitize_for_tts(modern_impact)}")
    outro = ("AI analysis. " + " ".join(outro_parts)) if outro_parts else ""

    full_text = "\n\n".join(filter(None, [intro, clean_body, outro]))

    if len(full_text) > 4500:
        max_body = max(100, 4500 - len(intro) - len(outro) - 50)
        clean_body = clean_body[:max_body]
        full_text = "\n\n".join(filter(None, [intro, clean_body, outro]))

    return full_text


def compute_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


MIN_AUDIO_BYTES = 2_000  # edge-tts can silently write near-empty files on soft failure


def validate_audio(path: Path) -> bool:
    """Return True if the file looks like a real MP3 (non-empty, has ID3/frame header)."""
    if not path.exists() or path.stat().st_size < MIN_AUDIO_BYTES:
        return False
    header = path.read_bytes()[:3]
    # ID3 tag or MPEG sync word (0xFF 0xFB / 0xFF 0xF3 / 0xFF 0xFA)
    return header[:3] == b"ID3" or (len(header) >= 2 and header[0] == 0xFF and header[1] & 0xE0 == 0xE0)


async def generate_one(
    uuid: str,
    text: str,
    output_path: Path,
    semaphore: asyncio.Semaphore,
    max_retries: int = 3,
) -> tuple[str, bool]:
    async with semaphore:
        for attempt in range(max_retries):
            try:
                communicate = edge_tts.Communicate(text, voice=VOICE)
                await asyncio.wait_for(communicate.save(str(output_path)), timeout=45)
                if not validate_audio(output_path):
                    output_path.unlink(missing_ok=True)
                    raise ValueError("output file missing or too small — likely a silent failure")
                return uuid, True
            except asyncio.TimeoutError:
                output_path.unlink(missing_ok=True)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    return uuid, False
            except Exception as e:
                output_path.unlink(missing_ok=True)
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    print(f"\n  ERROR {uuid}: {e}", file=sys.stderr)
                    return uuid, False
        return uuid, False


PROBE_CANDIDATES = [2, 4, 6, 8, 12, 16]
PROBE_SAMPLE = 4  # articles per concurrency level


async def probe_concurrency(queue: list) -> tuple[int, set[str]]:
    """
    Generate a small sample at increasing concurrency levels.
    Returns (best_concurrency, set_of_uuids_already_generated).
    Stops when throughput plateaus (< 10% gain) or failures appear.
    """
    print("Probing optimal concurrency (generates real files — no wasted work):")
    best_c = PROBE_CANDIDATES[0]
    best_rate = 0.0
    generated_uuids: set[str] = set()
    offset = 0

    for c in PROBE_CANDIDATES:
        sample = queue[offset: offset + PROBE_SAMPLE]
        if len(sample) < PROBE_SAMPLE:
            break

        sem = asyncio.Semaphore(c)
        start = time.time()
        tasks = [asyncio.create_task(generate_one(uuid, text, path, sem)) for uuid, text, path, _ in sample]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start

        ok_uuids = {uuid for (uuid, _, _, _), (_, success) in zip(sample, results) if success}
        failures = PROBE_SAMPLE - len(ok_uuids)
        generated_uuids |= ok_uuids
        offset += PROBE_SAMPLE

        rate = len(ok_uuids) / elapsed if elapsed > 0 else 0
        gain = (rate - best_rate) / best_rate if best_rate > 0 else 1.0
        note = f"{failures} failed — stopping" if failures else (f"+{gain*100:.0f}%" if best_rate > 0 else "baseline")
        print(f"  c={c:2d}: {rate:.2f} files/s  ({note})")

        if failures:
            break

        if rate > best_rate:
            best_rate = rate
            best_c = c

        if best_rate > 0 and gain < 0.10:
            # Plateau: less than 10% improvement — not worth going higher
            break

    print(f"  → Using concurrency={best_c}  ({best_rate:.2f} files/s)\n")
    return best_c, generated_uuids


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate all missing TTS audio locally")
    parser.add_argument("--concurrency", type=str, default="auto",
                        help="Parallel TTS requests, or 'auto' to probe (default: auto)")
    parser.add_argument("--batch-size", type=int, default=50, help="Save manifest every N completions (default: 50)")
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

    queue = []
    for uuid, fm, body in articles:
        output_path = AUDIO_DIR / f"{uuid}.mp3"
        if output_path.exists():
            continue
        tts_text = build_tts_text(fm, body)
        text_hash = compute_hash(tts_text)
        queue.append((uuid, tts_text, output_path, text_hash))

    total_articles = len(articles)
    missing = len(queue)
    existing = total_articles - missing

    print(f"Articles total:   {total_articles}")
    print(f"Already on disk:  {existing}")
    print(f"Missing audio:    {missing}")
    print()

    if not queue:
        print("Nothing to do — all audio files exist.")
        return

    # Resolve concurrency — probe if set to "auto"
    probe_generated: set[str] = set()
    if args.concurrency == "auto":
        if len(queue) < PROBE_SAMPLE * 2:
            concurrency = 4
            print(f"Queue too small to probe — using concurrency={concurrency}\n")
        else:
            concurrency, probe_generated = await probe_concurrency(queue)
    else:
        try:
            concurrency = int(args.concurrency)
        except ValueError:
            print(f"Invalid --concurrency value '{args.concurrency}' (use a number or 'auto')", file=sys.stderr)
            sys.exit(1)

    # Remove probe-generated files from the remaining queue
    hash_map = {uuid: text_hash for uuid, _, _, text_hash in queue}
    if probe_generated:
        for uuid in probe_generated:
            manifest[uuid] = hash_map[uuid]
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        queue = [(uuid, text, path, h) for uuid, text, path, h in queue if uuid not in probe_generated]

    remaining = len(queue)
    already_done = missing - remaining
    print(f"Manifest save:    every {args.batch_size} completions")
    if already_done:
        print(f"Probe generated:  {already_done} files")
    print(f"Remaining:        {remaining}")
    print(f"Concurrency:      {concurrency}")
    print(f"Estimated time:   ~{remaining * 3 // 60 // concurrency}–{remaining * 5 // 60 // concurrency} minutes")
    print()

    confirm = input("Start generation? [Y/n] ")
    if confirm.lower() not in ("", "y", "yes"):
        print("Aborted.")
        return

    semaphore = asyncio.Semaphore(concurrency)

    tasks = [
        asyncio.create_task(generate_one(uuid, text, path, semaphore))
        for uuid, text, path, _ in queue
    ]

    generated = failed = done = 0
    manifest_dirty = 0
    start_time = time.time()

    print()
    for fut in asyncio.as_completed(tasks):
        result_uuid, success = await fut
        done += 1

        if success:
            manifest[result_uuid] = hash_map[result_uuid]
            generated += 1
            manifest_dirty += 1
        else:
            failed += 1
            print(f"\n  FAILED {result_uuid} (after 3 attempts)", file=sys.stderr)

        if manifest_dirty >= args.batch_size:
            MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
            manifest_dirty = 0

        elapsed = time.time() - start_time
        rate = done / elapsed if elapsed > 0 else 0
        eta = (remaining - done) / rate if rate > 0 else 0
        pct = done / remaining * 100 if remaining else 100
        print(
            f"\r  [{done}/{remaining}] {pct:.0f}%  {generated} OK  {failed} failed"
            f"  {rate:.1f}/s  ~{eta/60:.0f}min left   ",
            end="",
            flush=True,
        )

    if manifest_dirty:
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    elapsed = time.time() - start_time
    print(f"\n\nDone in {elapsed/60:.1f} minutes: {generated} generated, {failed} failed")
    print(f"Total audio files on disk: {len(list(AUDIO_DIR.glob('*.mp3')))}")


if __name__ == "__main__":
    asyncio.run(main())
