# AGENTS.md — ed-lore / The GalNet Chronicle

> This file describes the project structure, conventions, and operational details for AI coding agents working on this repository.

---

## 0. Security & Secrets (CRITICAL)

**API keys, tokens, passwords, and any secrets must NEVER be committed to this repository or shown in code/output.**
- This is a **public GitHub repo** — all commits, issues, and workflow logs are visible
- No hardcoded credentials in Python scripts, Astro components, or workflow YAML files
- No `.env` files committed (`.gitignore` blocks `.env*`, `*.key`, `secrets/`)
- Secrets are passed via **GitHub Actions Secrets** (`CLOUDFLARE_R2_TOKEN`) or environment variables at runtime only
- Never echo secrets in CI logs or local output
- If a key is accidentally committed: rotate it immediately, scrub from git history

---

## 1. Project Overview

This project is **"The GalNet Chronicle"** — an archive and knowledge system for *Elite: Dangerous* GalNet articles.

**Current state:**
- **2,551** Markdown articles in `Archive/YYYY/MM/DD_slug.md` (in-game year/month/day)
- **3,484** entity profiles in `Entities/` (persons, factions, arcs, technologies, locations)
- **30** story arcs in `Entities/Arcs/`
- Static website built with **Astro 6.2 + React 19**, deployed to **GitHub Pages**
- Data pipeline: `scripts/build_graph.py` → `lore_graph.json` + split async JSON → website
- Audio pipeline: **GitHub Actions** generates TTS → uploads to **Cloudflare R2** → site loads from R2
- Deploy artifact: ~50 MB (HTML/CSS/JS only — audio is served from R2)

**Output:** ~3,477 static pages deployed to `https://kernicde.github.io/ed-lore/`

---

## 2. Technology Stack

| Layer | Technology |
|-------|------------|
| Fetcher | Python 3, `asyncio` |
| HTTP client | `httpx` (async) |
| Frontmatter | `pyyaml` |
| Data format | Markdown + YAML frontmatter |
| Build pipeline | `scripts/build_graph.py` → `lore_graph.json` + client JSONs |
| SSG | Astro 6.2 + React 19 |
| Package manager | `pnpm` |
| Deployment | GitHub Actions → GitHub Pages |
| Audio hosting | Cloudflare R2 (public bucket) |
| TTS | edge-tts (`en-GB-SoniaNeural`) |

Python dependencies: `pyyaml`, `httpx`, `tqdm`, `edge-tts`, `requests`

---

## 3. Project Structure

```
ed-lore/
├── AGENTS.md                  # This file
├── prompt.md                  # High-level product vision
├── scripts/
│   ├── build_graph.py         # Builds lore_graph.json + split client JSONs + version.json
│   ├── fetch.py               # Async article fetcher from Frontier API
│   ├── enrich.py              # Bulk enrichment (initial import only)
│   ├── generate_audio.py      # TTS audio generation (edge-tts)
│   ├── sync_audio_to_r2.py    # Upload MP3s to Cloudflare R2 with MD5/etag dedup
│   ├── validate_enrichment.py # Validates article frontmatter
│   ├── audit_api_vs_archive.py # Compares API with local archive
│   └── audit_arcs_and_uuids.py # Checks arc consistency
├── Archive/                   # Canonical article archive (YYYY/MM/DD_slug.md)
│   ├── 3301/02/08_....md
│   ├── 3307/08/02_....md
│   └── ... 3301–3312
├── Entities/                  # Entity profiles
│   ├── Arcs/
│   ├── faction/
│   ├── person/
│   ├── technology/
│   └── location/
└── website/                   # Astro 6.2 static site
    ├── src/
    │   ├── components/        # React components (AppShell, Timeline, AudioPlayer, etc.)
    │   └── pages/             # Astro pages
    ├── public/
    │   └── data/              # Generated JSONs (galnet-meta.json, galnet-bodies.json, search-index.json, version.json)
    ├── astro.config.mjs
    └── package.json
```

**Article path convention:** `Archive/<YYYY>/<MM>/<DD>_<slug>.md`
- `YYYY` = in-game year (e.g. `3307`)
- `MM` = month (zero-padded)
- `DD` = day (zero-padded)
- `slug` = lowercased, underscores, no special chars

---

## 4. Article Data Format

Every article has YAML frontmatter followed by a blank line and the article body.

### Core fields (always present)

| Field | Description |
|-------|-------------|
| `uuid` | Deterministic UUIDv5 from `date + lowercase title` |
| `title` | Original headline |
| `slug` | URL-safe slug |
| `date` | In-game date `YYYY-MM-DD` (quoted string) |
| `source_url` | Link to original GalNet article |

### Enrichment fields (added manually)

| Field | Description |
|-------|-------------|
| `summary` | 1–3 sentence summary of the article's content |
| `player_impact` | What pilots could do / did in this event |
| `modern_impact` | Why this still matters today |
| `topics` | Tags like `terrorism`, `diplomacy`, `corporate expansion` |
| `entities` | List of `{name, type, role}` objects |
| `locations` | List of star systems or significant places |
| `arc_id` | Single story-arc identifier (or omitted) |

### Banned topics (remove unless explicitly legitimate)

`ship`, `sport`, `trade`, `construction`, `medicine`, `safety`, `treasure hunt`

Legitimate exceptions exist (e.g. `medicine` for Titan quarantine articles).

### Body characteristics

- Plain text / minimal Markdown
- No images, no inline links, no headings, no blockquotes
- API-sourced bodies have HTML stripped

---

## 5. The Fetch Script (`scripts/fetch.py`)

**WARNING:** `fetch.py` is a **destructive-sync** script. It re-downloads and overwrites articles every run.

1. **API Phase** — Paginates Frontier's JSON API (`cms.zaonce.net`)
2. **Write Phase** — Writes to `Archive/YYYY/MM/DD_slug.md`

**DO NOT RUN** while enriching or editing articles, as it will overwrite your work.

---

## 6. Build Pipeline

### Step 1: Build the graph

```bash
python scripts/build_graph.py
```

Reads all articles in `Archive/` and entity files in `Entities/`, then writes:
- `lore_graph.json` — full graph (used by entity/arc static pages)
- `website/public/data/galnet-meta.json` — articles without `body_full` + entities + arcs (~6 MB, loaded async)
- `website/public/data/galnet-bodies.json` — `{uuid: body_full}` map (~3 MB, loaded lazily on first article expand)
- `website/public/data/search-index.json` — search-optimized articles (~1.5 MB)
- `website/public/data/version.json` — build timestamp + counts (used for cache busting)

### Step 2: Local Build Test (optional)

```bash
cd website
pnpm install
pnpm build
```

Output goes to `website/dist/`.

### Step 3: Deploy

**CRITICAL:** Deployment is handled by GitHub Actions.

**Correct deployment flow:**
1. Make your changes
2. Build locally: `python scripts/build_graph.py && cd website && pnpm build`
3. Commit everything
4. Push to `main`: `git push origin main`
5. The GitHub Actions workflow will rebuild and deploy to GitHub Pages automatically

Monitor deployment status at: https://github.com/KernicDE/ed-lore/actions

---

## 7. Audio Pipeline (Fully Automated)

**DO NOT generate audio locally.** All audio is handled by GitHub Actions.

### How it works

1. `audio-generation` workflow runs hourly (or manual trigger)
2. Restores MP3 cache + manifest cache from GitHub Actions Cache
3. Generates missing/changed audio via `scripts/generate_audio.py` (edge-tts)
4. Uploads MP3s to **Cloudflare R2** via `scripts/sync_audio_to_r2.py`
   - Uses MD5/etag comparison to skip already-uploaded files
5. Removes MP3s from build, builds Astro site, deploys
6. Saves MP3 cache for next run

### R2 Configuration

- **Bucket:** `ed-lore-audio`
- **Public URL:** `https://pub-4404b20907c141e1b68f3dc578038230.r2.dev/audio/{uuid}.mp3`
- **Cost:** $0 (within 10 GB free tier)

### Manual full rebuild

If audio is completely missing or corrupted:
- GitHub → Actions → Audio Generation → Run workflow → ✅ **full_rebuild**

---

## 8. Validation

```bash
python scripts/validate_enrichment.py
```

Checks:
- Required fields present (`summary`, `player_impact`)
- No duplicate persons/groups
- No banned topics
- No bad locations (sentence fragments)
- YAML parseable
- Arc consistency

---

## 9. Article Enrichment Workflow

New articles require **manual enrichment**. See `.kimi/prompts/fetch-enrich-deploy.md` for the full process.

### Rules
- **Read every file fully** before editing. No Python scripts, no batch processing, no guessing, no hallucination.
- **Skip already-enriched files** (those with `summary` and `player_impact` fields).
- Add fields: `summary`, `player_impact`, `modern_impact`, `entities`, `locations`, `topics`, `arc_id` where appropriate.
- **Clean garbage auto-extraction:**
  - Remove sentence-fragment locations like `"With the"`, `"Our endeavour in"`.
  - Never put `"Thargoid"` as a location.
  - Deduplicate groups.
- Fix `modern_impact` when it is clearly wrong.
- Use `ReadFile` to inspect each file, then `StrReplaceFile` with exact old text.
- Validate YAML after edits with `python scripts/validate_enrichment.py`.

---

## 10. Entity Files

Entity profiles live in `Entities/` and are auto-generated stubs plus hand-curated enrichment.

**Auto-generated stubs** have this format:
```yaml
---
id: person-name
name: Person Name
type: person
first_seen_date: '3307-08-16'
last_seen_date: '3307-08-26'
mention_count: 3
---

<!-- AUTO-GENERATED -->
```

When new persons or groups are introduced in articles, the build script may create stubs. These can be enriched later with biographical details.

---

## 11. Git & GitHub

- Repository: `https://github.com/KernicDE/ed-lore.git`
- Branch: `main`
- GitHub Actions auto-deploys the website on every push to `main`
- **Do not use** `git subtree push` to `gh-pages` — it is legacy and does not trigger deployments
- The CI pipeline rebuilds the site from scratch
- Always verify deployment succeeded at https://github.com/KernicDE/ed-lore/actions

---

## 12. Quick Reference

| Task | Command |
|------|---------|
| Install Python deps | `pip install pyyaml httpx tqdm edge-tts requests` |
| Fetch / refresh archive | `python scripts/fetch.py` *(destructive)* |
| Validate enrichment | `python scripts/validate_enrichment.py` |
| Build graph + client JSONs | `python scripts/build_graph.py` |
| Build website | `cd website && pnpm build` |
| Count articles | `find Archive -type f \| wc -l` |
| Push to GitHub (triggers deploy) | `git push origin main` |
| Check deployment status | https://github.com/KernicDE/ed-lore/actions |
| Trigger audio full rebuild | GitHub Actions → Audio Generation → Run workflow → ✅ full_rebuild |
| New article workflow | See `.kimi/prompts/fetch-enrich-deploy.md` |

---

## 13. Related Files

| File | Purpose |
|------|---------|
| `.kimi/prompts/fetch-enrich-deploy.md` | Step-by-step guide for importing & enriching new articles |
| `prompt.md` | High-level project vision |
| `AGENTS.md` | This file — technical conventions and operational details |

---

*Last updated: 2026-05-02*
